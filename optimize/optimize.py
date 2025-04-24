from flask import Flask, jsonify
import requests
import logging
from flask_cors import CORS
from prometheus_client import Gauge, start_http_server

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Prometheus metrics
measures = {
    "fcpv": Gauge("fcpv", "Energy used from the community PV", ["source"]),
    "tcr": Gauge("tcr", "Energy shared to residential customers", ["source"]),
    "fcr": Gauge("fcr", "Energy used from residential customers", ["source"]),
    "tcc": Gauge("tcc", "Energy shared to commercial customers", ["source"]),
    "fcc": Gauge("fcc", "Energy used from commercial customers", ["source"]),
    "tcb": Gauge("tcb", "Energy shared to the community battery", ["source"]),
    "fcb": Gauge("fcb", "Energy used from the community battery", ["source"]),
    "tg": Gauge("tg", "Energy shared to the grid", ["source"]),
    "fg": Gauge("fg", "Energy used from the grid", ["source"]),
}

# Start Prometheus metrics server
start_http_server(9099)

# Customer sources
customers = [
    ("rcwopv1", "http://customer1:5001/measure"),
    ("rcwpv1", "http://customer2:5002/measure"),
    ("ccwopv", "http://customer3:5003/measure"),
    ("ccwpv", "http://customer4:5004/measure"),
    ("rcwopv2", "http://customer5:5005/measure"),
    ("rcwpv2", "http://customer6:5006/measure"),
    ("cbat", "http://cbat:8080/measure"),
    ("cpv", "http://cpv:9000/measure"),
]

def fetch_customer_data():
    new_data = {}
    for source, url in customers:
        try:
            response = requests.get(url)
            response.raise_for_status()
            new_data[source] = response.json()
            logging.debug(f"Fetched data for {source}: {new_data[source]}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data for {source}: {e}")
            new_data[source] = {"error": str(e)}
    return new_data

@app.route('/optimize', methods=['GET'])
def optimize_measure():
    # Clear Prometheus metrics
    for metric in measures.values():
        metric._metrics.clear()

    customer_data = fetch_customer_data()

    if not customer_data:
        return jsonify({"error": "No data available"}), 500

    total_active_power = 0.0
    total_reactive_power = 0.0
    transaction_decisions = {}

    sellers = {
        "community": [],
        "commercial": [],
        "residential": [],
    }

    # First pass: compute power and identify sellers
    for source, data in customer_data.items():
        if "error" in data:
            continue

        active_power = data['active_power']
        reactive_power = data['reactive_power']
        decision = data['transaction_decision']

        total_active_power += active_power
        total_reactive_power += reactive_power
        transaction_decisions[source] = decision

        # Update Prometheus metrics
        if "Selling" in decision or active_power < 0:
            if source.startswith("rc"):
                measures["tcr"].labels(source=source).set(abs(active_power))
            elif source.startswith("cc"):
                measures["tcc"].labels(source=source).set(abs(active_power))
            elif source == "cpv":
                measures["tcb"].labels(source=source).set(abs(active_power))
            elif source == "cbat":
                measures["tg"].labels(source=source).set(abs(active_power))
        else:
            if source.startswith("rc"):
                measures["fcr"].labels(source=source).set(abs(active_power))
            elif source.startswith("cc"):
                measures["fcc"].labels(source=source).set(abs(active_power))
            elif source == "cbat":
                measures["fcb"].labels(source=source).set(abs(active_power))
            elif source == "cpv":
                measures["fcpv"].labels(source=source).set(abs(active_power))
            elif "Grid" in decision:
                measures["fg"].labels(source=source).set(abs(active_power))

        # Identify sellers
        if "Selling" in decision and active_power < 0:
            if source.startswith("cc"):
                sellers["commercial"].append(source)
            elif source.startswith("rc"):
                sellers["residential"].append(source)
            elif source == "cpv":
                sellers["community"].append(source)

    # --- Adjust Community Battery Logic ---
    if "cpv" in transaction_decisions and \
       transaction_decisions["cpv"] == "Charging Community Battery" and \
       "cpv" in sellers["community"]:
        transaction_decisions["cbat"] = "Charging from CPV"
    elif sellers["residential"] or sellers["commercial"]:
        transaction_decisions["cbat"] = "Charging from Community"
    else:
        transaction_decisions["cbat"] = "Idle"

    # --- Validate Commercial Buyers & Handle Selling Excess PV ---
    for cc in ["ccwpv", "ccwopv"]:
        decision = transaction_decisions.get(cc, "")

        if decision.startswith("Buying"):
            if not sellers.get("commercial"):
                transaction_decisions[cc] = "Buying from Grid"

        elif decision == "Selling Excess PV to Community/Other Customers":
            buyers = []
            for rc in ["rcwopv1", "rcwopv2", "rcwpv1", "rcwpv2"]:
                if transaction_decisions.get(rc, "").startswith("Buying from Commercial Customers"):
                    buyers.append(rc)
            for other_cc in ["ccwopv"]:
                if other_cc != cc and transaction_decisions.get(other_cc, "").startswith("Buying from Commercial Customers"):
                    buyers.append(other_cc)

            if buyers:
                transaction_decisions[cc] = f"Selling to {', '.join(buyers)}"
            elif transaction_decisions.get("cbat") == "Idle":
                transaction_decisions[cc] = "Selling to Community Battery"
                transaction_decisions["cbat"] = f"Charging from {cc.upper()}"
            else:
                transaction_decisions[cc] = "Selling to Grid"

    # --- Validate Residential Buyers ---
    for rc in ["rcwopv1", "rcwopv2", "rcwpv1", "rcwpv2"]:
        if transaction_decisions.get(rc, "").startswith("Buying"):
            if not (sellers["residential"] or sellers["commercial"] or sellers["community"]):
                transaction_decisions[rc] = "Buying from Grid"

    # --- Prevent CBAT from charging if CPV is not selling ---
    if transaction_decisions.get("cbat") == "Charging from CPV" and "cpv" not in sellers["community"]:
        transaction_decisions["cbat"] = "Idle"

    output = {
        "total_active_power": round(total_active_power, 2),
        "total_reactive_power": round(total_reactive_power, 2),
        "transaction_decisions": transaction_decisions
    }

    logging.debug(f"Final Output: {output}")
    return jsonify(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, jsonify
import requests
from prometheus_client import Gauge, start_http_server
import logging

app = Flask(__name__)

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

# Start the Prometheus metrics server on a separate port
start_http_server(9100)  # Exposes metrics at http://<host>:9099/metrics

@app.route('/optimize', methods=['GET'])
def optimize_measure():
    try:
        # Fetch data from all customer nodes
        customers = [
            ("rcwopv1", "http://customer1:5001/measure"),  # Residential Customer without PV
            ("rcwpv1", "http://customer2:5002/measure"),  # Residential Customer with PV
            ("ccwopv", "http://customer3:5003/measure"),  # Commercial Customer without PV
            ("ccwpv", "http://customer4:5004/measure"),  # Commercial Customer with PV
            ("rcwopv2", "http://customer5:5005/measure"),  # Residential Customer 2 without PV
            ("rcwpv2", "http://customer6:5006/measure"),  # Residential Customer 2 with PV
        ]
        customer_data = {}

        for source, url in customers:
            try:
                response = requests.get(url)
                response.raise_for_status()
                customer_data[source] = response.json()
                logging.debug(f"Fetched data for {source} from {url}: {customer_data[source]}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching data for {source} from {url}: {e}")
                return jsonify({"error": f"Error fetching data for {source}: {str(e)}"}), 500

        # Initialize total power values
        total_active_power = 0.0
        total_reactive_power = 0.0
        transaction_decisions = {}

        # Iterate over each source and calculate metrics
        for source, data in customer_data.items():
            active_power = data['active_power']
            reactive_power = data['reactive_power']
            transaction_decision = data['transaction_decision']

            # Debug transaction decision mapping
            logging.debug(f"Processing source: {source}, Transaction: {transaction_decision}")

            # Update total power
            total_active_power += active_power
            total_reactive_power += reactive_power

            # Update transaction decisions
            transaction_decisions[source] = transaction_decision

            # Assign metrics based on transaction decisions
            if transaction_decision == "Buying from Residential/Commercial Customer":
                # Energy used by residential/commercial customers
                measures["fcr"].labels(source=source).set(abs(active_power))  # Energy used from residential
                measures["fcc"].labels(source=source).set(abs(active_power))  # Energy used from commercial

            elif transaction_decision == "Selling to Community Battery":
                # Energy shared to the community battery
                measures["tcb"].labels(source=source).set(abs(active_power))

            elif transaction_decision == "Buying from Retailer":
                # Energy used from grid
                measures["fg"].labels(source=source).set(abs(active_power))  # Energy used from grid

            elif transaction_decision == "Using Community Battery":
                # Energy used from community battery
                measures["fcb"].labels(source=source).set(abs(active_power))  # Energy used from community battery

            elif transaction_decision == "Buying from Community PV":
                # Energy used from community PV
                measures["fcpv"].labels(source=source).set(abs(active_power))  # Energy used from community PV

            else:
                # Assume no energy shared to the grid, residential, or commercial for unknown decisions
                measures["tg"].labels(source=source).set(0.0)  # Energy shared to grid (default 0.0 for now)
                measures["tcr"].labels(source=source).set(0.0)  # Energy shared to residential customers
                measures["tcc"].labels(source=source).set(0.0)  # Energy shared to commercial customers

        # Prepare output
        output = {
            "total_active_power": total_active_power,
            "total_reactive_power": total_reactive_power,
            "transaction_decisions": transaction_decisions
        }

        logging.debug(f"Output: {output}")

        return jsonify(output)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Exposing on port 5000

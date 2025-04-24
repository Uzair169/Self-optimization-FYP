from flask import Flask, jsonify
import requests
from prometheus_client import Gauge, start_http_server
import logging
from flask_cors import CORS

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

# Start the Prometheus metrics server on a separate port
start_http_server(9100)  # Exposes metrics at http://<host>:9100/metrics

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

        # Classify customers into sellers (prosumers) and buyers
        sellers = {k: v for k, v in customer_data.items() if v['active_power'] > 0}
        buyers = {k: v for k, v in customer_data.items() if v['active_power'] < 0}
        
        # Simulate market clearance mechanism
        transactions = {}
        for buyer, buyer_data in buyers.items():
            demand = abs(buyer_data['active_power'])
            for seller, seller_data in sellers.items():
                supply = seller_data['active_power']
                transaction_amount = min(demand, supply)
                if transaction_amount > 0:
                    transactions[f"{buyer}_buys_from_{seller}"] = transaction_amount
                    sellers[seller]['active_power'] -= transaction_amount
                    buyers[buyer]['active_power'] += transaction_amount
                    demand -= transaction_amount
                if demand <= 0:
                    break  # Buyer satisfied
        
        # Handle battery transactions
        battery_data = requests.get("http://cbat:8080/measure").json()
        battery_capacity = battery_data["current_kwh"]
        
        for buyer, buyer_data in buyers.items():
            demand = abs(buyer_data['active_power'])
            if battery_capacity > 0 and demand > 0:
                transaction_amount = min(demand, battery_capacity)
                transactions[f"{buyer}_buys_from_battery"] = transaction_amount
                battery_capacity -= transaction_amount
                buyers[buyer]['active_power'] += transaction_amount
        
        # Assign energy metrics
        for transaction, amount in transactions.items():
            source, target = transaction.split("_buys_from_")
            measures["fcr"].labels(source=source).set(amount)
        
        # Prepare output
        output = {
            "transactions": transactions,
            "remaining_demand": {k: v['active_power'] for k, v in buyers.items()},
            "remaining_supply": {k: v['active_power'] for k, v in sellers.items()},
        }
        logging.debug(f"Market Clearance Output: {output}")

        return jsonify(output)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Exposing on port 5000

from flask import Flask, jsonify
import random
import requests

app = Flask(__name__)

# Function to fetch the current price info from the Price Manager
def get_price_info():
    try:
        response = requests.get("http://price:2000/info")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price info: {e}")
        return None

@app.route('/measure', methods=['GET'])
def measure_pv():
    # Simulate active and reactive power output for the PV system
    active_power = round(random.uniform(0.0, 10.0), 2)  # Active power in kW (0 to 10 kW range)
    reactive_power = round(random.uniform(0.0, 2.0), 2)  # Reactive power in kVAR (0 to 2 kVAR range)

    # Get price info to determine the transaction decision
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Default transaction decision
    transaction_decision = "No Transaction"

    # Transaction decision logic based on price info
    if active_power > 0:
        if price_info['gridSelling'] > price_info['gridBuying']:
            transaction_decision = "Selling to Grid"  # Sell power to the grid if selling price is higher
        elif price_info['gridSelling'] < price_info['gridBuying']:
            transaction_decision = "Charging Community Battery"  # Charge community battery if it's cheaper to buy from the grid than sell to it

    # Prepare output
    output = {
        "active_power": active_power,
        "reactive_power": reactive_power,
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)

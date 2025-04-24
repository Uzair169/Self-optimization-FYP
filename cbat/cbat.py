from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Initialize battery state
battery_state = {
    "capacity_kwh": 15.0,  # Max capacity
    "current_kwh": 7.5,    # Starting at 50% capacity
    "max_power_kwh": 10.0, # Max charging/discharging power
    "active_power": 0.0,
    "reactive_power": 0.0
}

# Function to fetch the current price info from the Price Manager
def get_price_info():
    try:
        response = requests.get("http://price:2000/info")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price info: {e}")
        return None

@app.route('/config', methods=['POST'])
def configure_battery():
    global battery_state
    data = request.get_json()

    if "active_power" not in data or "reactive_power" not in data:
        return jsonify({"error": "Invalid input, requires active_power and reactive_power"}), 400

    active_power = data["active_power"]
    reactive_power = data["reactive_power"]

    if abs(active_power) > battery_state["max_power_kwh"]:
        return jsonify({"error": "Active power exceeds maximum limit"}), 400

    # Update battery state
    battery_state["active_power"] = active_power
    battery_state["reactive_power"] = reactive_power

    # Adjust current capacity (discharging or charging)
    battery_state["current_kwh"] = max(
        0.0,
        min(
            battery_state["capacity_kwh"],
            battery_state["current_kwh"] + (active_power * 0.1)  # Adjust by power over time
        )
    )

    # # Get price info to determine the transaction decision
    # price_info = get_price_info()
    # if not price_info:
    #     return jsonify({"error": "Unable to fetch price information"}), 500

    # # Transaction decision logic
    # transaction_decision = "No Transaction"  # Default

    # if price_info['gridBuying'] < price_info['gridSelling']:
    #     transaction_decision = "Discharging to Grid"  # Sell to grid if buying price is higher than selling
    # elif price_info['gridBuying'] > price_info['gridSelling']:
    #     transaction_decision = "Charging from Grid"  # Charge from grid if buying price is lower

    # # Prepare output
    # output = {
    #     "active_power": battery_state["active_power"],
    #     "reactive_power": battery_state["reactive_power"],
    #     "current_kwh": battery_state["current_kwh"],
    #     "transaction_decision": transaction_decision
    # }

    return jsonify({
        "status": "Battery configuration updated"
        # "battery_state": output
    })

@app.route('/measure', methods=['GET'])
def measure_battery():
    global battery_state
    # Get price info to determine the transaction decision
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Transaction decision logic
    transaction_decision = "No Transaction"  # Default

    if price_info['gridBuying'] < price_info['gridSelling']:
        transaction_decision = "Discharging to Grid"  # Sell to grid if buying price is higher than selling
    elif price_info['gridBuying'] > price_info['gridSelling']:
        transaction_decision = "Charging from Grid"  # Charge from grid if buying price is lower

    # Prepare output
    output = {
        "active_power": battery_state["active_power"],
        "reactive_power": battery_state["reactive_power"],
        "current_kwh": battery_state["current_kwh"],
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

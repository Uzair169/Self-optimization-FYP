from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize battery state
battery_state = {
    "capacity_kwh": 15.0,  # Max capacity
    "current_kwh": 7.5,    # Starting at 50% capacity
    "max_power_kwh": 10.0, # Max charging/discharging power
    "active_power": 0.0,
    "reactive_power": 0.0
}

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

    return jsonify({"status": "Battery configuration updated", "current_kwh": battery_state["current_kwh"]})

@app.route('/measure', methods=['GET'])
def measure_battery():
    global battery_state
    return jsonify({
        "active_power": battery_state["active_power"],
        "reactive_power": battery_state["reactive_power"],
        "current_kwh": battery_state["current_kwh"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

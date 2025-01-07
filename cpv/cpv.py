from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/measure', methods=['GET'])
def measure_pv():
    # Simulate active and reactive power output for the PV system
    active_power = round(random.uniform(0.0, 10.0), 2)  # Active power in kW (0 to 10 kW range)
    reactive_power = round(random.uniform(0.0, 2.0), 2)  # Reactive power in kVAR (0 to 2 kVAR range)

    output = {
        "active_power": active_power,
        "reactive_power": reactive_power
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)

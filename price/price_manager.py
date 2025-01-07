from flask import Flask, jsonify, request

app = Flask(__name__)

# Define prices for various transactions (in EUR cents per kWh)
prices = {
    "gridSelling": 0,          # Selling energy to the grid (3rd Party)
    "gridBuying": 0,           # Buying energy from the grid
    "p2pSelling": 10,          # Selling energy Peer-to-Peer (P2P)
    "p2pBuying": 15,           # Buying energy Peer-to-Peer (P2P)
    "cBatterySelling": 7,      # Selling energy to/from Community Battery
    "cBatteryBuying": 17,      # Buying energy to/from Community Battery
    "cPVBuying": 15            # Buying energy from Community PV
}

# Endpoint to get prices (same as before)
@app.route('/info', methods=['GET'])
def price_info():
    return jsonify(prices)

# Endpoint for buying energy from the retailer, Community PV, or Community Battery
@app.route('/buy', methods=['POST'])
def buy_energy():
    data = request.get_json()
    energy_needed = data.get('energy_needed', 0)
    source = data.get('source', 'grid')  # Can be 'grid', 'cPV', or 'cBattery'

    total_cost = 0

    if source == 'grid':
        total_cost = energy_needed * prices["gridBuying"]
    elif source == 'cPV':
        total_cost = energy_needed * prices["cPVBuying"]
    elif source == 'cBattery':
        total_cost = energy_needed * prices["cBatteryBuying"]
    else:
        return jsonify({"error": "Invalid energy source specified"}), 400

    response = {
        "status": "success",
        "message": f"Successfully purchased {energy_needed} kWh from {source} at a price of {prices[source]} EUR cents/kWh.",
        "total_cost": total_cost
    }
    return jsonify(response)

# Endpoint for selling energy to the retailer, Community PV, or Community Battery
@app.route('/sell', methods=['POST'])
def sell_energy():
    data = request.get_json()
    energy_to_sell = data.get('energy_to_sell', 0)
    destination = data.get('destination', 'grid')  # Can be 'grid', 'cPV', or 'cBattery'

    total_revenue = 0

    if destination == 'grid':
        total_revenue = energy_to_sell * prices["gridSelling"]
    elif destination == 'cPV':
        total_revenue = energy_to_sell * prices["cPVBuying"]  # Same price as cPVBuying for selling
    elif destination == 'cBattery':
        total_revenue = energy_to_sell * prices["cBatterySelling"]
    else:
        return jsonify({"error": "Invalid energy destination specified"}), 400

    response = {
        "status": "success",
        "message": f"Successfully sold {energy_to_sell} kWh to {destination} at a price of {prices[destination]} EUR cents/kWh.",
        "total_revenue": total_revenue
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000)

from flask import Flask, jsonify
import pandapower as pp
import requests
import random

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
def customer6_measure():
    # Fetch price info
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Create a new empty network for Customer 6
    net = pp.create_empty_network()

    # Add bus for Customer 6
    customer_bus6 = pp.create_bus(net, vn_kv=0.4, name="Customer Bus 6")

    # Add external grid
    pp.create_ext_grid(net, bus=customer_bus6, vm_pu=1.02, name="External Grid")

    # Randomize load (consumption)
    active_power = round(random.uniform(3.0, 5.0), 2)
    reactive_power = round(random.uniform(1.0, 2.0), 2)
    pp.create_load(net, bus=customer_bus6, p_mw=active_power, q_mvar=reactive_power, name="Customer Load 6")

    # Randomize PV generation
    pv_active_power = round(random.uniform(1.0, 4.0), 2)
    pp.create_sgen(net, bus=customer_bus6, p_mw=-pv_active_power, q_mvar=0.0, name="PV Generation", type='PV')

    # Run power flow
    pp.runpp(net)

    # Get results
    load6_results = net.res_load.loc[0, ['p_mw', 'q_mvar']]
    pv_results = net.res_sgen.loc[0, ['p_mw', 'q_mvar']]

    total_active_power = load6_results.p_mw + pv_results.p_mw
    total_reactive_power = load6_results.q_mvar + pv_results.q_mvar

    transaction_decision = "No Transaction"

    # Surplus condition (generation > consumption, total_active_power > 0 means net demand)
    if total_active_power < 0:  # Net export
        # Residential customers can sell to residential customers
        if price_info['p2pSelling'] > price_info['cBatterySelling']:
            transaction_decision = "Selling to Residential Customer"
        # Can sell to commercial customers too
        elif price_info['p2pSelling'] > price_info['gridSelling']:
            transaction_decision = "Selling to Commercial Customer"
        # Or sell to community battery
        elif price_info['cBatterySelling'] > price_info['gridSelling']:
            transaction_decision = "Selling to Community Battery"
        else:
            transaction_decision = "Selling to Retailer"

    # Deficit condition (consumption > generation)
    else:
        # Buy from residential/commercial customers
        if price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['cPVBuying']:
            transaction_decision = "Buying from Residential/Commercial Customer"
        # Buy from community PV
        elif price_info['cPVBuying'] < price_info['p2pBuying'] and price_info['cPVBuying'] < price_info['cBatteryBuying']:
            transaction_decision = "Buying from Community PV"
        # Buy from retailer
        elif price_info['gridBuying'] < price_info['cBatteryBuying']:
            transaction_decision = "Buying from Retailer"

    # Fallback
    if transaction_decision == "No Transaction":
        transaction_decision = "Using Community Battery"

    # Output
    output = {
        "active_power": total_active_power,
        "reactive_power": total_reactive_power,
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)

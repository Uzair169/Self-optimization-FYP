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

# Function to generate random active and reactive power
def get_random_power():
    active_power = round(random.uniform(3.5, 5.5), 2)  # Active power between 3.5 and 5.5 MW
    reactive_power = round(random.uniform(1.0, 2.5), 2)  # Reactive power between 1.0 and 2.5 MVAR
    return active_power, reactive_power

@app.route('/measure', methods=['GET'])
def customer2_measure():
    # Fetch price info
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Create a new empty network for Customer 2 (Residential with PV generation)
    net = pp.create_empty_network()

    # Add buses for Customer 2
    customer_bus2 = pp.create_bus(net, vn_kv=0.4, name="Customer Bus 2")

    # Add an external grid to supply power to the system
    pp.create_ext_grid(net, bus=customer_bus2, vm_pu=1.02, name="External Grid")

    # Add a load to Customer Bus 2 (representing a customer with consumption)
    # Generate random active and reactive power for Customer 2 load
    load_active_power, load_reactive_power = get_random_power()
    pp.create_load(net, bus=customer_bus2, p_mw=load_active_power, q_mvar=load_reactive_power, name="Customer Load 2")

    # Add a smaller PV generation to Customer Bus 2 (with negative power to indicate generation)
    # Generate random active and reactive power for PV generation
    pv_active_power, pv_reactive_power = get_random_power()
    pp.create_sgen(net, bus=customer_bus2, p_mw=-pv_active_power, q_mvar=-pv_reactive_power, name="PV Generation", type='PV')

    # Run power flow calculation
    pp.runpp(net)

    # Get active and reactive power results for Customer 2
    load2_results = net.res_load.loc[0, ['p_mw', 'q_mvar']]
    pv_results = net.res_sgen.loc[0, ['p_mw', 'q_mvar']]

    # Prepare output (total power consumed or produced by Customer 2)
    total_active_power = load2_results.p_mw + pv_results.p_mw
    total_reactive_power = load2_results.q_mvar + pv_results.q_mvar

    # Decision-making logic based on price information and constraints
    transaction_decision = "No Transaction"

    # If Customer 2 is generating more energy than it consumes
    if total_active_power > 0:  # Surplus Generation
        # 1. Sell excess energy to residential/commercial customers (Residential must be preferred)
        if price_info['p2pSelling'] > price_info['p2pBuying']:
            transaction_decision = "Selling to Residential Customer"  # Residential preferred
        elif price_info['p2pSelling'] > price_info['cBatteryBuying']:
            transaction_decision = "Selling to Commercial Customer"
        # 2. If selling to other customers isn't favorable, store in the Community Battery
        elif price_info['cBatterySelling'] < price_info['cBatteryBuying']:
            transaction_decision = "Selling to Community Battery"
        # 3. Otherwise, store energy in the Community Battery
        else:
            transaction_decision = "Using Community Battery"

    # If Customer 2 needs more energy than it generates
    else:  # Energy Deficit
        # 1. Residential customers can buy from residential or commercial customers (Residential preferred)
        if price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['cPVBuying']:
            transaction_decision = "Buying from Residential Customer"  # Residential preferred
        elif price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['cPVBuying']:
            transaction_decision = "Buying from Commercial Customer"
        # 2. Residential customers can sell to other residential customers
        elif price_info['p2pSelling'] > price_info['p2pBuying']:
            transaction_decision = "Selling to Residential Customer"
        # 3. Residential customers can buy from Community PV (not applicable for Commercial)
        elif price_info['cPVBuying'] < price_info['p2pBuying'] and price_info['cPVBuying'] < price_info['cBatteryBuying']:
            transaction_decision = "Buying from Community PV"
        # 4. All customers can buy and sell to/from retailer and battery storage system
        elif price_info['gridBuying'] > price_info['gridSelling']:
            transaction_decision = "Buying from Retailer"

    # Final decision based on preferred residential customer rule:
    if transaction_decision == "No Transaction":
        transaction_decision = "Using Community Battery"

    # Prepare output
    output = {
        "active_power": total_active_power,
        "reactive_power": total_reactive_power,
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

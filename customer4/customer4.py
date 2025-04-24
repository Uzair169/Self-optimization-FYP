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
    active_power = round(random.uniform(2.0, 6.0), 2)  # Active power between 2.0 and 6.0 MW
    reactive_power = round(random.uniform(1., 3.0), 2)  # Reactive power between 1.5 and 3.0 MVAR
    return active_power, reactive_power

@app.route('/measure', methods=['GET'])
def customer4_measure():
    # Fetch price info
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Create a new empty network for Customer 4
    net = pp.create_empty_network()

    # Add buses for Customer 4
    customer_bus4 = pp.create_bus(net, vn_kv=0.4, name="Customer Bus 4")

    # Add an external grid to supply power to the system
    pp.create_ext_grid(net, bus=customer_bus4, vm_pu=1.02, name="External Grid")

    # Generate random active and reactive power for Customer 4 load
    load_active_power, load_reactive_power = get_random_power()

    # Add a load to Customer Bus 4 (representing a commercial customer with consumption)
    pp.create_load(net, bus=customer_bus4, p_mw=load_active_power, q_mvar=load_reactive_power, name="Customer Load 4")

    # Add a PV system for Customer 4 (commercial customer with PV generation)
    pv_active_power = round(random.uniform(1.0, 3.0), 2)  # PV active power between 1.0 and 3 MW
    pp.create_sgen(net, bus=customer_bus4, p_mw=-pv_active_power, name="Customer PV Generation")  # Negative power for PV

    # Run power flow calculation
    pp.runpp(net)

    # Get active and reactive power results for Customer 4
    load4_results = net.res_load.loc[0, ['p_mw', 'q_mvar']]
    pv4_results = net.res_sgen.loc[0, ['p_mw']]  # Only need active power for PV (negative)

    # Decision-making logic based on price information and constraints
    transaction_decision = "No Transaction"

    # 1. Commercial customers can buy energy only from other commercial customers.
    if price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['gridBuying']:
        transaction_decision = "Buying from Commercial Customer"

    # 2. Commercial customers can sell to residential and commercial customers.
    elif price_info['p2pSelling'] > price_info['p2pBuying']:
        transaction_decision = "Selling to Residential/Commercial Customer"

    # 3. Commercial customers can sell their excess PV generation to the community or others.
    if pv4_results.p_mw < 0 and abs(pv4_results.p_mw) > load4_results.p_mw:
        transaction_decision = "Selling Excess PV to Community/Other Customers"

    # 4. Commercial customers cannot buy energy from the community PV system.
    if transaction_decision == "No Transaction" and price_info['gridBuying'] < price_info['cBatteryBuying']:
        transaction_decision = "Buying from Retailer"

    # 5. All customers can buy/sell energy from/to the battery storage system.
    if transaction_decision == "No Transaction":
        transaction_decision = "Using Community Battery"

    # Prepare output
    output = {
        "active_power": load4_results.p_mw,
        "reactive_power": load4_results.q_mvar,
        "pv_active_power": pv4_results.p_mw,  # This is negative, representing power fed back to the grid
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)

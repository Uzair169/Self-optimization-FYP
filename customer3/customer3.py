from flask import Flask, jsonify
import pandapower as pp
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
def customer3_measure():
    # Fetch price info
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Create a new empty network for Customer 3
    net = pp.create_empty_network()

    # Add buses for Customer 3
    customer_bus3 = pp.create_bus(net, vn_kv=0.4, name="Customer Bus 3")

    # Add an external grid to supply power to the system
    pp.create_ext_grid(net, bus=customer_bus3, vm_pu=1.02, name="External Grid")

    # Add a load to Customer Bus 3 (representing a commercial customer with consumption)
    pp.create_load(net, bus=customer_bus3, p_mw=5.0, q_mvar=2.0, name="Customer Load 3")

    # Run power flow calculation
    pp.runpp(net)

    # Get active and reactive power results for Customer 3
    load3_results = net.res_load.loc[0, ['p_mw', 'q_mvar']]

    # Decision-making logic based on price information and constraints
    transaction_decision = "No Transaction"

    # 1. Commercial customers can buy energy only from other commercial customers.
    if price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['gridBuying']:
        transaction_decision = "Buying from Commercial Customer"

    # 2. Commercial customers can sell to residential and commercial customers.
    elif price_info['p2pSelling'] > price_info['p2pBuying']:
        transaction_decision = "Selling to Residential/Commercial Customer"

    # 3. Commercial customers cannot buy energy from the community PV system.
    if transaction_decision == "No Transaction" and price_info['gridBuying'] < price_info['cBatteryBuying']:
        transaction_decision = "Buying from Retailer"

    # 4. All customers can buy/sell energy from/to the battery storage system.
    if transaction_decision == "No Transaction":
        transaction_decision = "Using Community Battery"

    # Prepare output
    output = {
        "active_power": load3_results.p_mw,
        "reactive_power": load3_results.q_mvar,
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

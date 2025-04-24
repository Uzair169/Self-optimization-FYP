from flask import Flask, jsonify
import pandapower as pp
import requests
import random  # <-- for dynamic power generation

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
def customer1_measure():
    # Fetch price info
    price_info = get_price_info()
    if not price_info:
        return jsonify({"error": "Unable to fetch price information"}), 500

    # Create a new empty network for Customer 1
    net = pp.create_empty_network()

    # Add buses for Customer 1
    customer_bus1 = pp.create_bus(net, vn_kv=0.4, name="Customer Bus 1")

    # Add an external grid to supply power to the system
    pp.create_ext_grid(net, bus=customer_bus1, vm_pu=1.02, name="External Grid")

    # 🔄 Generate dynamic active and reactive power values
    dynamic_p_mw = round(random.uniform(1.0, 5.0), 2)    # e.g., between 1.0 and 5.0 MW
    dynamic_q_mvar = round(random.uniform(0.2, 2.0), 2)  # e.g., between 0.2 and 2.0 MVAr

    # Add a load with the dynamic values
    pp.create_load(net, bus=customer_bus1, p_mw=dynamic_p_mw, q_mvar=dynamic_q_mvar, name="Customer Load 1")

    # Run power flow calculation
    pp.runpp(net)

    # Get active and reactive power results
    load1_results = net.res_load.loc[0, ['p_mw', 'q_mvar']]

    # Decision-making logic based on the provided constraints
    transaction_decision = "No Transaction"

    # **Constraint 1**: Residential customers can buy from residential/commercial customers
    # **Constraint 3**: Residential customers can buy from the community PV system
    if price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['cPVBuying']:
        transaction_decision = "Buying from Residential/Commercial Customer"
    elif price_info['p2pSelling'] > price_info['p2pBuying']:
        transaction_decision = "Selling to Residential Customer"  # Residential can only sell to other residential customers
    elif price_info['cPVBuying'] < price_info['p2pBuying'] and price_info['cPVBuying'] < price_info['cBatteryBuying']:
        transaction_decision = "Buying from Community PV"
    # **Constraint 7**: Residential customers must be preferred
    elif price_info['gridBuying'] > price_info['gridSelling']:
        transaction_decision = "Buying from Retailer"

    # **Constraint 8**: All customers can buy/sell from/to the battery storage
    if transaction_decision == "No Transaction":
        transaction_decision = "Using Community Battery"

    output = {
        "active_power": round(load1_results.p_mw, 2),
        "reactive_power": round(load1_results.q_mvar, 2),
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

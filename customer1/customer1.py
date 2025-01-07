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

    # Add a load to Customer Bus 1 (representing a customer without generation)
    pp.create_load(net, bus=customer_bus1, p_mw=3.0, q_mvar=1.0, name="Customer Load 1")

    # Run power flow calculation
    pp.runpp(net)

    # Get active and reactive power results for Customer 1
    load1_results = net.res_load.loc[0, ['p_mw', 'q_mvar']]

    # Decision-making logic based on price information and constraints
    transaction_decision = "No Transaction"

    # Apply the constraints:

    # 1. Residential customers can buy from residential or commercial customers.
    if price_info['p2pBuying'] < price_info['cBatteryBuying'] and price_info['p2pBuying'] <= price_info['cPVBuying']:
        transaction_decision = "Buying from Residential/Commercial Customer"
    
    # 2. Residential customers can sell to other residential customers
    elif price_info['p2pSelling'] > price_info['p2pBuying']:
        transaction_decision = "Selling to Residential Customer"

    # 3. Residential customers can buy from Community PV
    elif price_info['cPVBuying'] < price_info['p2pBuying'] and price_info['cPVBuying'] < price_info['cBatteryBuying']:
        transaction_decision = "Buying from Community PV"

    # 4. Commercial customers can only buy from commercial customers (if applicable)
    elif price_info['p2pBuying'] > price_info['cPVBuying'] and price_info['cPVBuying'] < price_info['cBatteryBuying']:
        transaction_decision = "Buying from Commercial Customer"
    
    # 5. All customers can buy and sell to/from retailer and battery storage system.
    elif price_info['gridBuying'] > price_info['gridSelling']:
        transaction_decision = "Buying from Retailer"

    # 6. All customers can use community battery (if no better option)
    if transaction_decision == "No Transaction":
        transaction_decision = "Using Community Battery"

    # Prepare output
    output = {
        "active_power": load1_results.p_mw,
        "reactive_power": load1_results.q_mvar,
        "transaction_decision": transaction_decision
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

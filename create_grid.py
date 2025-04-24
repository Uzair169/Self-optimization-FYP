import pandapower as pp
import pandapower.networks as pn
import json

# Create an empty network
net = pp.create_empty_network()

# Create a simple bus system
bus1 = pp.create_bus(net, vn_kv=20, name="Bus 1")
bus2 = pp.create_bus(net, vn_kv=0.4, name="Bus 2")

# Create a transformer
pp.create_transformer(net, bus1, bus2, std_type="0.4 MVA 20/0.4 kV")

# Create a load
pp.create_load(net, bus2, p_mw=0.1, q_mvar=0.05, name="Load")

# Save to JSON
pp.to_json(net, "grid_model.json")
print("✅ Grid model saved as 'grid_model.json'")

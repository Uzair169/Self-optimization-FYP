import pandapower as pp

# Load the existing model
net = pp.from_json("/home/uzair/Desktop/Docker/fyp/grid_model.json")

# Add a generator at bus 0
# pp.create_sgen(net, bus=0, p_mw=10, vm_pu=1.02, name="MainGen")
pp.create_sgen(net, bus=1, p_mw=1.0, q_mvar=0.2)  # Example
pp.create_gen(net, bus=0, p_mw=5.0, vm_pu=1.02)

# Save the updated model
pp.to_json(net, "/home/uzair/Desktop/Docker/fyp/grid_model.json")
print("✅ Generator added successfully!")

import pandapower as pp

model_path = "/home/uzair/Desktop/Docker/fyp/pandapower_example.json"
net = pp.from_json(model_path)

print("Generators:\n", net.gen)
print("Static Generators:\n", net.sgen)  # Controlled generators

# Check generators' P values
print(net.gen)
print(net.sgen)

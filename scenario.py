import mosaik
import pandas as pd
import matplotlib.pyplot as plt
import os
import arrow

sim_config = {
    'Grid': {'cmd': 'python3 /home/uzair/Desktop/Docker/fyp/pandapower_simulator.py %(addr)s'},
    'Emissions': {'python': 'mosaik_components.emissions:Simulator'},
}

grid_model_path = "/home/uzair/Desktop/Docker/fyp/pandapower_example.json"
if not os.path.exists(grid_model_path):
    raise FileNotFoundError(f"⚠ Error: Grid model file '{grid_model_path}' not found.")

world = mosaik.World(sim_config)

grid_sim = world.start('Grid', start=0, end=100, step_size=15, timeout=10)

grid = grid_sim.Grid.create(num=1, model_path=grid_model_path)  # Fixed the argument order
print("Grid entities created:", grid)

start_time = arrow.get('2025-03-04T00:00:00').datetime.isoformat()
end_time = arrow.get('2025-03-04T00:10:00').datetime.isoformat()

emission_config = {'country': 'Germany', 'state': 'SN'}
em_sim = world.start('Emissions', start=0, end=100)
em_entities = em_sim.Emission.create(1, **emission_config)

if not em_entities:
    raise ValueError("⚠ No emission entities created.")

gens = [e for e in grid]

if not gens:
    raise ValueError("⚠ Error: No generators found in the power grid model!")

for gen in gens:
    for em in em_entities:
        print(f"Connecting {gen.full_id} -> {em.full_id}")

if not gens:
    print("No gens")
elif gens:
    print(gens)
    
if not em_entities:
    print("no em_entities")
elif em_entities:
    print(em_entities)
    
    
if gens and em_entities:
    world.connect(gens[0], em_entities[0], ('P[MW]', 'P'))  # Corrected attribute mapping
else:
    raise ValueError("⚠ Error: Either no generators or no emission entities found!")

world.run(until=100)

# Collect and visualize results
try:
    results = em_sim.get_data()
    df = pd.DataFrame(results)
    df.plot()
    plt.show()
except Exception as e:
    print(f"⚠ Error during result processing: {e}")

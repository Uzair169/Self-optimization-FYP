import sys
import time
import mosaik_api_v3
import pandapower as pp
import os

print("🚀 Pandapower Simulator is starting...", file=sys.stderr)

# Ensure HOST:PORT is provided by Mosaik
if len(sys.argv) < 2:
    print("⚠ Error: Missing HOST:PORT argument!", file=sys.stderr)
    sys.exit(1)

HOST_PORT = sys.argv[1].strip()  # Read the host:port argument
print(f"✅ Received HOST:PORT = '{HOST_PORT}'", file=sys.stderr)  # Debugging output

# Validate HOST:PORT format
if ':' not in HOST_PORT:
    print(f"⚠ Error: Invalid HOST:PORT format: '{HOST_PORT}'", file=sys.stderr)
    sys.exit(1)

META = {
    'type': 'time-based',
    'models': {
        'Grid': {
            'public': True,
            'params': ['model_path'],  
            'attrs': ['P[MW]'],  # Ensure 'P[MW]' is in output attributes
        },
    },
}

class PandapowerSimulator(mosaik_api_v3.Simulator):
    def __init__(self):
        super().__init__(META)
        self.entities = {}
        self.start = None
        self.end = None
        self.step_size = 1  # Default step size
        self.timeout = None  

    def init(self, sid, start, end, step_size=1, timeout=None):
        """ Initialize the simulator with start, end, step_size, and optional timeout. """
        self.sid = sid
        self.start = start
        self.end = end
        self.step_size = step_size  
        self.timeout = timeout  
        print(f"✅ PandapowerSimulator initialized: start={start}, end={end}, step_size={step_size}, timeout={timeout}", file=sys.stderr)
        return self.meta
    
    def create(self, num, model, **model_params):
        model_path = model_params.get('model_path', 'pandapower_example.json')
    
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"⚠ Error: Grid model file '{model_path}' not found!")

        net = pp.from_json(model_path)  # Load the Pandapower grid
    
        print(f"✅ Loaded Pandapower model from {model_path}. Number of buses: {len(net.bus)}", file=sys.stderr)
        print(f"✅ Generators in Pandapower model:\n{net.gen}", file=sys.stderr)
        print(f"✅ Static Generators in Pandapower model:\n{net.sgen}", file=sys.stderr)

        entity_id = len(self.entities)  
        self.entities[entity_id] = net
        print(f"✅ Created Grid entity with ID {entity_id}", file=sys.stderr)

        generators = [{'eid': entity_id, 'type': 'Grid'}]  
        return generators

    def step(self, time, inputs, max_advance=None):
        return time + self.step_size  

    def get_data(self, outputs):
        data = {}
        for eid in outputs:
            if eid in self.entities:
                net = self.entities[eid]
                try:
                    pp.runpp(net)  # Ensure power flow is executed
                    p_mw_value = net.res_gen.p_mw.sum()

                    # Ensure P[MW] is never missing
                    if p_mw_value is None:
                        print(f"⚠ Warning: P[MW] is None for entity {eid}, setting to 0!", file=sys.stderr)
                        p_mw_value = 0

                    data[eid] = {'P[MW]': p_mw_value}

                except Exception as e:
                    print(f"⚠ Error running power flow for entity {eid}: {e}", file=sys.stderr)
                    data[eid] = {'P[MW]': 0}  # Default to 0 on failure

            else:
                print(f"⚠ Warning: Requested entity {eid} not found in simulator!", file=sys.stderr)
                data[eid] = {'P[MW]': 0}  # Default to 0 if entity doesn't exist

        return data


sim = PandapowerSimulator()

if __name__ == '__main__':
    mosaik_api_v3.start_simulation(sim, HOST_PORT)  
    
    while True:
        time.sleep(1)

### My Final Year Project (FYP) titled 
# A Distributed Modular Co-simulation Platform for Local Energy Communities with Encapsulated Dynamics 


### How to use it?
Clone the repo and run 
`docker compose up --build` in the main folder

`localhost:9100` for Prometheus Web <br>
`localhost:3000` for Grafana, default username/password is admin/admin.

### Important measures.
`optimization module`, `localhost:5000/optimize` Main Optimization module <br><br>

`rcwopv1`, `localhost:5001/measure` Residential Customer 1 without PV <br>
`rcwpv1`, `http://customer2:5002/measure`, Residential Customer 1 with PV <br>
`ccwopv`, `http://customer3:5003/measure`, Commercial Customer without PV <br>
`ccwpv`, `http://customer4:5004/measure`, Commercial Customer with PV <br>
`rcwopv2`, `http://customer5:5005/measure`, Residential Customer 2 without PV <br>
`rcwpv2`, `http://customer6:5006/measure`, Residential Customer 2 with PV <br>

### End-outcome
A modular platform that enables simulation of a modern distribution system
representing energy community that can further developed to test EV integration,
virtual power plant and cyber security concerns. 

# CloudRouteAI Project Status

## 1. Project Overview
CloudRouteAI is an autonomous, adaptive network routing platform that integrates NS-3 (Network Simulator 3) telemetry with Machine Learning (ML) inference. It dynamically replaces traditional static routing metrics (like physical hop-count) with predicted link health costs to create a self-healing network. The system detects congestion or failures in real-time, reroutes traffic using Dijkstra's algorithm with ML-predicted weights, and visualizes the decisions in a Streamlit-based Explainable AI (XAI) dashboard.

## 2. Current Progress
**Status: Completed / Final Validation Phase**

The system's core phases (1 through 6) have been fully implemented and integrated. 
- **Git Repository:** Successfully initialized, staged, committed, and synced to the remote repository.
- **End-to-End Execution:** The master script `run_all.sh` successfully links all modules—from simulation to the final dashboard.
- **Dashboard & XAI:** A fully functioning Streamlit GUI with Glassmorphism aesthetics visualizes metrics, topology, and routing decisions.
- **Scenarios Validated:** Evaluated successfully against Normal, Congestion, Failure, and Traffic Spike scenarios.

## 3. System Modules & Architecture

### M1: NS-3 Simulation Engine (`ns3_simulation/`)
- **What it does:** Simulates a 10-node network topology featuring a primary backbone and an alternate detour path. It uses `FlowMonitor` to export real-time runtime telemetry (every 2 seconds).
- **Key Files:** `simulation.cc` (main simulator), `config_loader.cc` (loads scenarios).

### M2: Data Processing (`data_processing/`)
- **What it does:** Processes raw XML telemetry from NS-3 into normalized JSON metrics.
- **Key Files:** `parser.py` converts `queue_utilization`, `delay_ms`, `throughput_mbps`, and `packet_loss_rate` into structured formats for the ML module.

### M3: Machine Learning Model (`ml_model/`)
- **What it does:** Infers network link costs based on runtime telemetry using a pre-trained `RandomForestRegressor`. It digests multi-dimensional metrics into a single "Routing Cost" (e.g., Healthy = 10, Congested = 1000, Failed = 9999).
- **Key Files:** `train.py`, `predict.py`, `model.pkl`.

### M4: Threshold Controller & Routing Logic
- **What it does:** Implemented inside the C++ core, it monitors the ML-predicted link costs. If the path cost breaches a baseline threshold (alpha = 0.15), it triggers a reroute. It then runs Dijkstra's algorithm to compute the new optimal path and updates the static routing tables in NS-3.

### M5: GUI & Explainability Dashboard (`dashboard/`)
- **What it does:** A Streamlit-based control center that provides real-time visibility into the network. It features KPI tracking, an Intelligence Feed (explaining AI decisions), role-based topology maps (NetworkX/Plotly), and performance benchmarking graphs.
- **Key Files:** `app.py`, `xai_module.py`, `topology_view.py`, `comparison_view.py`.

## 4. Validated Workloads

1. **Normal:** Baseline traffic flows smoothly along the primary backbone route.
2. **Congestion:** Throttling a link triggers queue spikes. The threshold controller detects the ML cost increase and diverts traffic to the alternate path, recovering throughput.
3. **Failure:** A dead link causes an instant infinite cost spike. The system self-heals by instantly injecting the alternate path, preventing complete packet loss.
4. **Traffic Spike:** A sudden burst affects the entire backbone. The AI correctly determines the alternate path is no better and maintains the current route, preventing route flapping.

## 5. Execution Reference
- **Full Pipeline:** ` ./run_all.sh` (Cleans up, compiles, runs inference, and launches dashboard)
- **Dashboard Only:** `./run_dashboard.sh` (Inspects already generated simulation outputs)

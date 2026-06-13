# CloudRouteAI Project Status

## 1. Project Overview
CloudRouteAI is an autonomous, adaptive network routing platform that integrates Python-based network telemetry with Machine Learning (ML) inference. It dynamically replaces traditional static routing metrics (like physical hop-count) with predicted link health costs to create a self-healing network. The system detects congestion or failures in real-time, reroutes traffic using Dijkstra's algorithm with ML-predicted weights, and visualizes the decisions in a Streamlit-based Explainable AI (XAI) dashboard.

## 2. Current Progress
**Status: Completed / Final Validation Phase**

The system's core phases (1 through 6) have been fully implemented and integrated. 
- **Git Repository:** Successfully initialized, staged, committed, and synced to the remote repository.
- **End-to-End Execution:** The master script `run_all.bat` (Windows) and `run_all.sh` (cross-platform) successfully link all modules—from simulation to the final dashboard.
- **Dashboard & XAI:** A fully functioning Streamlit GUI with Glassmorphism aesthetics visualizes metrics, topology, and routing decisions.
- **Scenarios Validated:** Evaluated successfully against Normal, Congestion, Failure, and Traffic Spike scenarios.

## 3. System Modules & Architecture

### M1: Python Simulation Engine (`dashboard/network_simulator.py`)
- **What it does:** Simulates an 11-node network topology featuring a primary backbone and an alternate detour path. It uses NetworkX graphs to model the network and generates real-time telemetry (every 2 seconds).

### M2: Machine Learning Model (`ml_model/`)
- **What it does:** Infers network link costs based on runtime telemetry using a pre-trained `RandomForestRegressor`. It digests multi-dimensional metrics into a single "Routing Cost" (e.g., Healthy = 10, Congested = 1000, Failed = 9999).
- **Key Files:** `train.py`, `predict.py`, `model.pkl`.

### M3: Threshold Controller & Routing Logic
- **What it does:** Monitors the ML-predicted link costs. If the path cost breaches a baseline threshold (alpha = 0.15), it triggers a reroute. It then runs Dijkstra's algorithm on the ML cost weights to compute the new optimal path and updates the simulated routing tables.

### M4: GUI & Explainability Dashboard (`dashboard/`)
- **What it does:** A Streamlit-based control center that provides real-time visibility into the network. It features KPI tracking, an Intelligence Feed (explaining AI decisions), role-based topology maps (NetworkX/Plotly), and performance benchmarking graphs.
- **Key Files:** `app.py`, `xai_module.py`, `topology_view.py`, `comparison_view.py`.

## 4. Validated Workloads

1. **Normal:** Baseline traffic flows smoothly along the primary backbone route.
2. **Congestion:** Throttling a link triggers queue spikes. The threshold controller detects the ML cost increase and diverts traffic to the alternate path, recovering throughput.
3. **Failure:** A dead link causes an instant infinite cost spike. The system self-heals by instantly injecting the alternate path, preventing complete packet loss.
4. **Traffic Spike:** A sudden burst affects the entire backbone. The AI correctly determines the alternate path is no better and maintains the current route, preventing route flapping.

## 5. Execution Reference
- **Full Pipeline (Windows):** `run_all.bat <scenario>` (Cleans up, runs Python simulation, inference, and generates comparison metrics)
- **Full Pipeline (Linux/Mac):** `./run_all.sh <scenario>`
- **Dashboard (Windows):** `run_dashboard.bat` (Launches Streamlit dashboard)
- **Dashboard (Linux/Mac):** `./run_dashboard.sh`

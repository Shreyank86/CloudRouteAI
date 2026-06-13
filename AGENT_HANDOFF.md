# CloudRouteAI Handoff Report & Project Summary

This document serves as a comprehensive handoff report for **CloudRouteAI**, detailing the project's description, architecture, current status, execution procedures, and structural outline to enable seamless collaboration for the user and future AI agents.

---

## 1. Project Description
**CloudRouteAI** is an autonomous, adaptive network routing platform that integrates **Python NetworkX** telemetry with **Machine Learning (ML)** inference. It dynamically replaces traditional static routing metrics (like physical hop-count) with predicted link health costs. 

The system implements a **self-healing network** that detects congestion or physical link failures in real-time, runs Dijkstra's algorithm using ML-predicted weights, and injects optimal routing paths back into the running simulation—visualized in a Streamlit-based Explainable AI (XAI) dashboard.

---

## 2. Current Project Status

- **Git Repository Synced**: The local workspace has been successfully initialized as a Git repository, staged, committed, and force-pushed to the remote repository [Shreyank86/CloudRouteAI](https://github.com/Shreyank86/CloudRouteAI).
- **Repository Cleanliness**: The `.gitignore` is properly configured to exclude runtime logs (`*.log`), intermediate outputs, and build artifacts, keeping the repository lightweight.
- **End-to-End Execution**: The master script `run_all.bat` (Windows) and `run_all.sh` (cross-platform) successfully execute the dual simulation baseline and adaptive runs, and save comparative telemetry JSONs.
- **Dashboard Implementation**: A tabbed Streamlit GUI visualizes the network metrics, active topology maps (using NetworkX/Plotly), intelligence feeds, and historical performance comparisons.

---

## 3. System Architecture & Component Map

The project is structured into modular components, facilitating independent updates and maintenance:

```
[Python Simulation Engine] ---> (Telemetry JSON) 
          ^                      |
          | (Path Updates)       v
[Adaptive Threshold Controller] <--- (Dynamic Costs) <--- [ML Cost Predictor]
          |
          +---> (Decision Logs) ---> [Streamlit Explainability GUI]
```

### 3.1 Component Breakdown

*   **Simulation Engine (`dashboard/network_simulator.py`)**
    *   `network_simulator.py`: Pure-Python simulation engine simulating an 11-node topology with a primary path and alternate path, using NetworkX graph models and outputting JSON telemetry.
*   **Machine Learning (`ml_model/`)**
    *   `train.py` & `preprocess.py`: Processes telemetry data and trains the random forest classifier.
    *   `predict.py`: Infers link costs based on runtime telemetry inputs.
    *   `model.pkl`: Pre-trained RandomForestRegressor model file mapping telemetry to link health costs (`10` = Healthy, `1000` = Congestion, `9999` = Failed).
*   **GUI Dashboard (`dashboard/`)**
    *   `app.py`: Streamlit entry point.
    *   `xai_module.py` & `xai_view.py`: Observation layer consuming decision logs to output plain-English explanations.
    *   `topology_view.py` & `react_topology.py`: Dynamically highlights active routes, network bottlenecks, and failed nodes.
    *   `comparison_view.py`: Renders performance graphs comparing static vs. adaptive routing.

---

## 4. Workloads & Scenarios

The system evaluates routing adaptability across 4 pre-configured scenarios (`scenarios/`):

1.  **Normal**: Baseline traffic along the primary backbone route.
2.  **Congestion**: Throttles the bottleneck link `4->5` to 1 Mbps, triggering an adaptive reroute to the alternate detour path (`9->10`).
3.  **Failure**: Disables link `4->5` at $t=8s$, forcing the controller to self-heal and reroute the traffic instantly.
4.  **Traffic Spike**: Injects a high traffic burst (1500 pk/sec). The ML model predicts a cost spike but determines the alternate path is worse, preventing unnecessary route flapping.

---

## 5. Execution Reference

### Run the Full Pipeline
The master scripts automate cleanups and python simulation execution:
**Windows:**
```cmd
run_all.bat <scenario>
```
**Linux/Mac:**
```bash
./run_all.sh <scenario>
```

### Run the Dashboard Individually
If you want to launch the Streamlit dashboard:
**Windows:**
```cmd
run_dashboard.bat
```
**Linux/Mac:**
```bash
./run_dashboard.sh
```

---

## 6. Guidelines for Future Agent Sessions

When resuming work, please follow these instructions:
1.  **Read outputs**: The dashboard reads telemetry from `outputs/` subdirectories. Ensure files in these paths are not manually edited.
2.  **Preserve separation of concerns**: Keep the XAI observability layer (`dashboard/xai_module.py`) functionally separate from the core simulation engine (`dashboard/network_simulator.py`).
3.  **Check `.gitignore`**: Ensure no raw large `.xml` files or dynamic runtime logs are committed when updates are made.

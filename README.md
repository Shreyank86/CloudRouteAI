# CloudRouteAI
**Adaptive Network Routing Platform via NS-3 & Machine Learning**

CloudRouteAI is a completely autonomous, adaptive routing network simulation project. Built entirely with NS-3, C++, Python, Scikit-Learn, and Streamlit, the platform successfully bridges the gap between low-level packet simulation and high-level artificial intelligence.

It demonstrates a "self-healing" network capable of monitoring link telemetry, passing runtime metrics to an ML inference engine, identifying congestion, and dynamically re-injecting optimized routes into the active network via Dijkstra's algorithm—all visualized in a beautiful, evaluator-friendly dashboard.

## 🚀 The Architecture Workflow

1. **Phase 1: NS-3 Simulation Engine**  
   Simulates a 10-node complex network with primary and alternate routes. Injects real-world scenarios: Normal, Congestion (link throttling), Link Failure, and massive Traffic Spikes using UDP Echo Applications.
2. **Phase 2: Runtime Monitoring (Telemetry)**  
   C++ modules extract real-time `queue_utilization`, `delay`, `throughput`, and `packet_loss` from NS-3's `FlowMonitor` every 2 seconds, exporting them to `runtime_metrics.json`.
3. **Phase 3: ML Cost Prediction Engine**  
   A `RandomForestRegressor` analyzes the runtime telemetry. Instead of using raw physical metrics, it maps network health to an abstract "Routing Cost" (e.g., 10 for healthy, 9999 for failure).
4. **Phase 4: Adaptive Threshold Controller**  
   The C++ `AdaptiveRoutingController` actively evaluates the network path. If the ML predicted cost degrades by >15% ($\alpha = 0.15$) against the baseline, it triggers a reroute.
5. **Phase 5: Dijkstra Routing & Dynamic Updates**  
   The controller runs Dijkstra's Shortest Path algorithm on the new ML cost graph and dynamically manipulates NS-3's `Ipv4StaticRouting` tables at runtime to divert traffic away from the bottleneck.
6. **Phase 6: The Explanability Dashboard**  
   A Streamlit dashboard visualizes the end-to-end process, rendering the dynamic topology, charting runtime performance metrics, explaining routing decisions, and proving the performance uplift.

## 🛠️ Installation & Execution

### Dependencies

#### System Requirements
- **Linux Environment** (Ubuntu 22.04+ or WSL2 recommended)
- **C++ Toolchain**: GCC 11.1+ or Clang 17+ (supporting C++23 standard)
- **CMake**: version 3.20 or later
- **Python**: version 3.10 or later
- **NS-3**: version `ns-3-dev` or `ns-3.39` or later.
  > [!NOTE]
  > The simulation runner script expects the NS-3 directory to be located at `~/ns-3-dev` (i.e. `/home/username/ns-3-dev`). If your NS-3 installation is elsewhere, you can create a symbolic link (e.g. `ln -s /path/to/your/ns3 ~/ns-3-dev`) or edit `NS3_DIR` in `ns3_simulation/run_simulation.sh`.

#### Python Libraries
Install the python libraries using the provided `requirements.txt`:
```bash
pip3 install -r requirements.txt
```
The project has been tested with the following suitable versions:
- `streamlit` (`>=1.30.0, <2.0.0`)
- `plotly` (`>=5.0.0, <7.0.0`)
- `networkx` (`>=3.0, <4.0`)
- `pandas` (`>=2.0.0, <3.0.0`)
- `lxml` (`>=4.0.0, <5.0.0`)
- `numpy` (`>=1.20.0, <2.0.0`)
- `scipy` (`>=1.7.0, <2.0.0`)
- `scikit-learn` (`>=1.0.0, <2.0.0`)

### Running the End-to-End Pipeline
We have automated the entire project execution. You do not need to run individual files. Simply execute the master script:

```bash
chmod +x run_all.sh
./run_all.sh
```
This script will:
1. Purge stale data.
2. Run the base NS-3 simulation to extract metrics.
3. Parse the data and run the ML Cost Prediction model.
4. Rerun NS-3 with the ML loop enabled, triggering adaptive rerouting.
5. Parse the final performance comparison metrics.
6. Verify routing stability to ensure no route-flapping occurs.
7. Automatically launch the Streamlit Dashboard.

*(Windows users can execute `run_all.bat`)*

## 🔍 Demonstration Scenarios
From the dashboard's left sidebar, you can inspect the four core scenarios:

- **Normal**: The baseline. Traffic flows across the primary path (0→1→2→3→4→5→6→7). No rerouting occurs.
- **Congestion**: Link 4→5 is maliciously throttled to 1 Mbps. The queue backs up, the ML model detects the cost spike, and traffic is diverted to the alternate route (0→1→2→8→9→4→5→6→7).
- **Failure**: Link 4→5 completely dies at $t=8s$. The ML cost hits 9999.0, and the network immediately self-heals by rerouting.
- **Traffic Spike**: A massive burst of 1500 pkt/sec hits the network between $t=5s$ and $t=10s$. The ML detects the spike but realizes the alternate path is worse, so the Threshold Controller wisely decides to *stay* on the current path (preventing oscillation).

## 📊 Evaluation Outputs
All outputs are available in the `outputs/` directory:
- `outputs/raw/`: Base runtime metrics directly from NS-3.
- `outputs/processed/`: Standardized JSON metrics for dashboard consumption.
- `outputs/ml/`: Predicted routing costs from the RandomForestRegressor.
- `outputs/routing/`: Comprehensive JSON logs explaining exactly *when* and *why* every routing decision was made.

---
*Developed for the Advanced Agentic Coding capability showcase.*
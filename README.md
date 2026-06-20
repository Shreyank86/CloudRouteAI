# CloudRouteAI
**Adaptive Network Routing Platform via Kubernetes, Machine Learning & Telemetry**

CloudRouteAI is a completely autonomous, adaptive routing network simulation project. Built with Python, Scikit-Learn, Streamlit, and Kubernetes, the platform bridges the gap between low-level packet simulation and high-level artificial intelligence.

It demonstrates a "self-healing" network capable of monitoring live link telemetry from client agents, passing runtime metrics to an ML inference engine, identifying congestion, and visualizing real-time metrics—all hosted on a scalable Kubernetes cluster.

## 🚀 The Architecture Workflow

1. **Phase 1: Multi-Client Telemetry**  
   Remote client laptops generate network telemetry (bandwidth usage, connections) and stream it to the central server via REST API.
2. **Phase 2: Runtime Monitoring (Telemetry API)**  
   A scalable FastAPI backend running in Kubernetes ingests telemetry data from all connected clients and stores it in a fast Redis cache.
3. **Phase 3: ML Cost Prediction Engine**  
   A `RandomForestRegressor` analyzes the runtime telemetry. Instead of using raw physical metrics, it maps network health to an abstract "Routing Cost" (e.g., 10 for healthy, 9999 for failure).
4. **Phase 4: Adaptive Threshold Controller & Dijkstra Routing**  
   The controller actively evaluates the network path. If the ML predicted cost degrades, it triggers a reroute. It runs Dijkstra's Shortest Path algorithm on the new ML cost graph to dynamically divert traffic.
5. **Phase 5: The Explanability Dashboard**  
   A Streamlit dashboard visualizes the end-to-end process, rendering the dynamic topology, charting runtime performance metrics, explaining routing decisions, and proving the performance uplift.

## 🛠️ Installation & Execution (Server)

The main server application is fully containerized and orchestrated using **Kubernetes**. 

### 1. Prerequisites
- **Docker Desktop** installed and running on your machine.
- **Kubernetes** enabled in Docker Desktop settings.

### 2. Deploying the Application
Open PowerShell or Terminal in the project root folder and apply the Kubernetes configurations:
```bash
kubectl apply -f k8s/
```
*(This automatically deploys the Redis cache, Telemetry API, and Dashboard).*

### 3. Verify Deployment
Verify that the pods are running:
```bash
kubectl get pods
```
You should see `redis`, `dashboard`, and `telemetry-api` pods with a `Running` status.

### 4. Access the Dashboard
Once the pods are running, access the Streamlit dashboard in your browser:
**http://localhost:8501**

## 💻 Client Agent Setup (For Other Users)

If other users want to connect their laptops to your CloudRouteAI network, they do **not** need Docker or Kubernetes. They only need Python and the `client_agent` folder.

1. Find the Server IP address (run `ipconfig` on the Server machine and find the IPv4 address, e.g., `192.168.1.5`).
2. Have the client install requirements on their machine:
   ```bash
   pip install psutil requests
   ```
3. Run the client agent, pointing it to the Server IP:

   **On Windows (PowerShell):**
   ```powershell
   $env:CLOUDROUTE_SERVER_IP="192.168.1.5"
   python client_agent/agent.py
   ```
   
   **On Mac/Linux:**
   ```bash
   export CLOUDROUTE_SERVER_IP="192.168.1.5"
   python3 client_agent/agent.py
   ```

You will immediately see the new client pop up on the Live Dashboard!

## 📊 Evaluation Outputs
All outputs are available in the `outputs/` directory:
- `outputs/raw/`: Base runtime metrics from the telemetry clients.
- `outputs/processed/`: Standardized JSON metrics for dashboard consumption.
- `outputs/ml/`: Predicted routing costs from the RandomForestRegressor.
- `outputs/routing/`: Comprehensive JSON logs explaining exactly *when* and *why* every routing decision was made.

---
*Developed for the Advanced Agentic Coding capability showcase.*
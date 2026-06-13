# CloudRouteAI: Final Project Report

## 1. Executive Summary
CloudRouteAI is an advanced network simulation platform demonstrating the integration of Machine Learning (ML) with dynamic routing algorithms in a pure-Python, Windows-compatible platform. The system successfully replaces purely manual or static routing metrics (like hop-count or fixed link bandwidths) with dynamic, ML-predicted costs derived from real-time network telemetry.

## 2. Problem Statement
Modern networks face rapid fluctuations in traffic patterns, resulting in transient congestion or link failures. Traditional static routing cannot adapt to these changes, leading to severe packet loss and queue bottlenecks. The objective of CloudRouteAI was to design a "self-healing" network that could autonomously detect performance degradation and dynamically reroute traffic in real-time without human intervention.

## 3. Architecture & Technical Decisions

### 3.1 Network Topology
We designed a 10-node topology featuring a primary backbone path and an alternate detour path. 
*   **Primary:** Nodes `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8`
*   **Alternate:** Nodes `3 -> 9 -> 10 -> 5`

**Why:** This specific topology creates a forced choice. The primary path is shorter, making it the default shortest path for Dijkstra. The alternate path is physically longer. This allowed us to prove that the ML routing engine can mathematically override the physical hop-count advantage when congestion occurs on the primary path.

### 3.2 Runtime Monitoring & Telemetry
We designed a pure-Python simulation engine using NetworkX graphs to model the 11-node topology and export runtime statistics every 2 seconds. The telemetry captures `queue_utilization`, `delay_ms`, `throughput_mbps`, and `packet_loss_rate`. 

**Why:** Evaluating the network every 2 seconds provided a fast enough feedback loop to react to traffic spikes, while avoiding computational overload.

### 3.3 ML Cost Prediction
We utilized a `RandomForestRegressor` trained on synthetic routing philosophies.
*   Healthy Link (Low delay, zero loss) = Cost ~10
*   Congested Link (High queue, high delay) = Cost ~1000
*   Failed Link (Dead connection) = Cost 9999

**Why ML?** Network health is non-linear. Combining queue utilization, packet loss, and latency into a single simple formula often fails to capture the true state of a link. The ML model easily digests multi-dimensional telemetry into a single, actionable "Routing Cost".

### 3.4 Threshold Controller & Dijkstra Routing
The Python routing controller implements a Threshold Alpha ($\alpha = 0.15$). The system records the baseline cost of the network at $t=2s$. If the current path's ML cost exceeds `baseline * (1 + alpha)`, a reroute is triggered. When triggered, the system runs Dijkstra's Shortest Path algorithm on the latest ML-cost graph and updates the simulated routing tables.

**Why:** The threshold prevents "route flapping" (oscillation). Without the 15% buffer, the network would constantly ping-pong between paths at the slightest variation in traffic, degrading overall throughput. 

### 3.5 Phase 5: GUI & Explainability Layer
The final phase focused on transforming the dashboard into a premium, interactive control center. Using **Glassmorphism aesthetics** and a **tabbed layout**, the GUI provides real-time visibility into:
*   **KPI Tracking**: Instant metrics for Packet Loss, Network Load, and Throughput.
*   **Intelligence Feed**: A human-readable log explaining the AI's reasoning behind every reroute.
*   **Role-Based Topology**: Color-coded nodes (Source, Destination, Congestion) and active path highlighting.
*   **Performance Benchmarking**: Quantitative comparison between Static and Adaptive routing runs.

## 4. Evaluation & Results

We evaluated the system against 4 distinct scenarios.

### 4.1 Congestion Scenario
*   **Trigger:** Link 4->5 throttled to 1 Mbps.
*   **Result:** Queue utilization hit 100%. The ML cost spiked from 10 to ~3000. At $t=8s$, the Threshold Controller detected a 1.20x cost breach and immediately triggered Dijkstra. Traffic diverted through the alternate path (`9->10`).
*   **Performance:** Adaptive routing recovered the throughput from 1 Mbps back to ~8 Mbps and eliminated packet loss on the primary bottleneck.

### 4.2 Link Failure Scenario
*   **Trigger:** Link 4->5 manually brought down at $t=8s$.
*   **Result:** ML cost registered 9999.0 (infinite). The Threshold Controller detected a 42x cost ratio breach.
*   **Performance:** The system instantaneously injected the alternate path, self-healing the network and preventing 100% packet loss.

### 4.3 Traffic Spike Scenario
*   **Trigger:** Sudden 1500 pkt/sec burst.
*   **Result:** The ML model successfully detected the cost spike. *However*, because the spike affected the entire backbone, Dijkstra found that the alternate path was actually *worse*. 
*   **Performance:** The system intelligently returned `THRESHOLD_BREACHED_NO_BETTER_PATH` and stayed on the current route, proving it will not blindly reroute if a better option does not exist.

## 5. Conclusion
Phase 6 finalizes CloudRouteAI as a robust, automated platform. The Streamlit dashboard successfully serves as the explainability layer, making the black-box AI decisions entirely transparent to evaluators. The final pipeline validates that an AI-driven, threshold-controlled routing engine can effectively eliminate manual network administration during congestion events.

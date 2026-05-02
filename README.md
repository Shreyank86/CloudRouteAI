# CloudRoute AI ☁️

CloudRoute AI is an autonomous, machine-learning-driven routing configuration and simulation pipeline built to analyze and optimize network traffic intelligently.

## 🚀 Project Overview (Pipeline)

The CloudRoute AI pipeline operates across four distinct, fully decoupled modules designed for parallel development and clear responsibility isolation:

1. **`scenario.json`** ➡️ Defines the network event (e.g., normal traffic, congestion, or link failures).
2. **M1 (Simulation):** Reads the scenario, runs the **NS-3 Simulation**, and generates raw logs (`flowmon.xml`).
3. **M2 (Data Processing):** Parses the XML to calculate strict performance metrics (`metrics.json`).
4. **M3 (Machine Learning):** Computes financial and performance cost thresholds (`costs.json`).
5. **M4 (Routing & Evaluation):** Re-applies optimized network configurations (`routing_config.json`) and produces comparative analytics (`comparison.json`).

---

## 🏆 Current Progress: M1 and M2 Completed
**Notice for the Team:** 
The infrastructure up to **Module 2 (M2)** has been successfully developed, integrated, and validated by **Shreyank and Teammate 1**. 

* The NS-3 simulation scripts (M1) are stable.
* The Data Processing parsing engine (`data_processing/parser.py`) flawlessly translates XML outputs into strict JSON schema metrics.

**Next Steps for Teammate 3 and Teammate 4:**
The repository is fully prepped for you to begin implementing **M3 (ML Model)** and **M4 (Routing & Evaluation)** logic. The skeleton architecture is already present. Please stay confined to your respective directories.

---

## 🛠️ Installation & How to Run (M1 + M2)

To allow the rest of the team to run the existing work locally, please execute the following steps precisely.

### 1. Install Dependencies
Ensure you have Python 3 installed, then run:
```bash
pip install lxml
```
*(If you need to install NS-3 on your local machine, please follow the official [NS-3 Installation Guide](https://www.nsnam.org/docs/tutorial/html/getting-started.html)).*

### 2. Run the M1 Simulation
1. Copy `ns3_simulation/simulation.cc` to your ns-3 scratch directory (`ns-3.x/scratch/`).
2. Build ns-3 using `./ns3 build` (or `./waf build` depending on your version).
3. Execute the simulation to generate the `flowmon.xml` and animation files.
4. Move the generated outputs to the `outputs/raw/` directory and explicitly name them: `normal_flow.xml`, `congestion_flow.xml`, and `link_failure.xml`.

*(Note: Raw xml files are already tracked in this repository for testing purposes, so you may skip this step if you simply want to test M2).*

### 3. Run the M2 Parser
Once the XML files are securely stored in `outputs/raw/`, run the parser from the root directory:
```bash
python3 data_processing/parser.py
```

### ✅ Expected Output
After running the M2 parser, the following files will be successfully generated:
- `outputs/processed/normal_metrics.json`
- `outputs/processed/congestion_metrics.json`
- `outputs/processed/failure_metrics.json`

---

## 🛑 Strict Collaboration Rules

To ensure safe team collaboration and maintain pipeline integrity:
- **DO NOT modify M1 + M2:** The simulation (`ns3_simulation/`) and data processing (`data_processing/`) modules are strictly locked.
- **Isolate your work:** Only work inside your assigned module directory (`ml_model/`, `routing/`, `evaluation/`). Do NOT modify the root structure.
- **Output Directory Rule:** ALL modules must write their output **exclusively** to their respective subdirectories within the `outputs/` folder. Do not pollute source directories with generated data.
- **Do NOT change the overall project structure.**

---

## 👥 Team Roles
- **Teammate 1 (Simulation Engineering):** M1 - NS-3 logic, network topologies, XML traces *(Completed)*.
- **Shreyank (Data Engineering):** M2 - XML parsing, metric calculation, JSON sanitization *(Completed)*.
- **Teammate 3 (Machine Learning):** M3 - Training models, inferencing costs, algorithms.
- **Teammate 4 (Routing & Evaluation):** M4 - Algorithmic routing configuration, cost comparison, visual analytics.

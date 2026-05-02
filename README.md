🚀 CloudRoute AI

CloudRoute AI is a modular system for intelligent network routing using simulation, data processing, machine learning, and adaptive routing.

---

🧠 PROJECT OVERVIEW

The system follows a structured pipeline:

scenario.json
→ NS-3 Simulation (M1)
→ flowmon.xml
→ metrics.json (M2)
→ costs.json (M3)
→ routing_config.json (M4)
→ comparison.json

---

📊 CURRENT PROJECT STATUS

✔ M1 (Simulation) → COMPLETED
✔ M2 (Data Processing) → COMPLETED
⏳ M3 (Machine Learning) → PENDING
⏳ M4 (Routing + Evaluation) → PENDING

---

📁 PROJECT STRUCTURE

scenarios/          → Scenario inputs (M1)
ns3_simulation/     → NS-3 simulation code (M1)
data_processing/    → XML → JSON parser (M2)
ml_model/           → Machine Learning (M3)
routing/            → Routing adaptation (M4)
evaluation/         → Comparison & results (M4)
outputs/            → Shared data across modules
shared/             → Common schema & configs
scripts/            → Pipeline execution scripts
docs/               → Documentation

---

🔒 IMPORTANT RULES (READ BEFORE STARTING)

❗ DO NOT MODIFY (M1 + M2 COMPLETE)

- ns3_simulation/
- data_processing/
- outputs/raw/
- outputs/processed/

👉 These modules are finalized and verified.

---

❗ FOR M3 & M4 TEAM MEMBERS

- Work ONLY inside:
  
  - ml_model/
  - routing/
  - evaluation/

- DO NOT:
  
  - Rename files
  - Change structure
  - Modify existing outputs

---

❗ OUTPUT RULE

All generated files MUST go inside:

outputs/

---

⚙️ SYSTEM SETUP (UBUNTU REQUIRED)

🔧 Install Dependencies

sudo apt update
sudo apt upgrade -y

sudo apt install -y build-essential gcc g++ python3 python3-pip cmake git \
libsqlite3-dev libxml2-dev libgtk-3-dev qtbase5-dev qtchooser qt5-qmake \
qtbase5-dev-tools libboost-all-dev libgsl-dev libgcrypt-dev libffi-dev

---

🔧 Install NS-3

cd ~
git clone https://gitlab.com/nsnam/ns-3-dev.git
cd ns-3-dev

./ns3 configure
./ns3 build

---

🚀 HOW TO RUN (M1 + M2 PIPELINE)

---

🔹 STEP 1 — Copy Simulation File

cp ~/Desktop/cloudroute-ai/ns3_simulation/simulation.cc ~/ns-3-dev/scratch/cloudroute.cc

---

🔹 STEP 2 — Run Simulation

Normal Scenario

cd ~/ns-3-dev
./ns3 run "scratch/cloudroute --scenario=normal"
mv flowmon.xml ~/Desktop/cloudroute-ai/outputs/raw/normal_flow.xml

Congestion Scenario

./ns3 run "scratch/cloudroute --scenario=congestion"
mv flowmon.xml ~/Desktop/cloudroute-ai/outputs/raw/congestion_flow.xml

Failure Scenario

./ns3 run "scratch/cloudroute --scenario=failure"
mv flowmon.xml ~/Desktop/cloudroute-ai/outputs/raw/failure_flow.xml

---

🔹 STEP 3 — Run Data Processing (M2)

cd ~/Desktop/cloudroute-ai
python3 data_processing/parser.py

---

✅ EXPECTED OUTPUT (M2)

outputs/processed/
├── normal_metrics.json
├── congestion_metrics.json
├── failure_metrics.json

---

🧪 VALIDATION CHECK

Ensure:

- JSON files exist
- No null values
- All values are float
- scenario_id is correct

---

⚠️ ERROR HANDLING

If any error occurs:

outputs/error/error.json

---

🤖 GUIDE FOR M3 (MACHINE LEARNING)

INPUT

outputs/processed/*.json

---

TASK

- Read metrics.json
- Train / predict model
- Generate link costs

---

OUTPUT

outputs/ml/{scenario}_costs.json

---

🔀 GUIDE FOR M4 (ROUTING + EVALUATION)

INPUT

outputs/ml/*.json

---

TASK

- Apply routing logic
- Re-run simulation
- Compare performance

---

OUTPUT

outputs/routing/{scenario}_routing.json
outputs/evaluation/{scenario}_comparison.json

---

🛑 FINAL WARNING

DO NOT CHANGE STRUCTURE
DO NOT MODIFY COMPLETED MODULES
DO NOT RENAME FILES

Breaking these rules will cause integration failure.

---

🧠 TEAM WORKFLOW

M1 → Simulation
M2 → Data Processing
M3 → Machine Learning
M4 → Routing + Evaluation

---

🚀 NEXT STEPS

👉 M3 Team: Start ML model development
👉 M4 Team: Implement routing + evaluation

---

🟢 PROJECT READY

M1 + M2 are fully functional and validated.

👉 Safe to proceed with M3 and M4.

---
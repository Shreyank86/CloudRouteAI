#!/bin/bash
# CloudRouteAI — End-to-End Master Execution Script
# Phase 6: Final Integration and Automation (Unified Architecture)

set -e # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCENARIO="${1:-normal}"

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}      CloudRouteAI — Unified Pipeline: $SCENARIO      ${NC}"
echo -e "${GREEN}======================================================${NC}"

# Helper function for error handling
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}[ERROR] Required file $1 is missing! Pipeline halted.${NC}"
        exit 1
    fi
}

# --- STEP 0: CLEANUP ---
echo -e "\n${YELLOW}▶ STEP 0: Cleaning previous run data...${NC}"
rm -rf outputs/raw/* outputs/ml/* outputs/routing/* outputs/processed/*
echo "✔ Workspace cleaned."

# --- STEP 1: BASE SIMULATION (No Adaptive Routing) ---
echo -e "\n${YELLOW}▶ STEP 1: Running Base NS-3 Simulation (No Adaptive Routing)...${NC}"
bash ns3_simulation/run_simulation.sh "$SCENARIO" false > /dev/null 2>&1 || { echo -e "${RED}[ERROR] Simulation failed.${NC}"; exit 1; }
check_file "outputs/raw/runtime_metrics.json"
echo "✔ Base simulation complete. Raw metrics generated."

# Use venv python if available
if [ -f "venv/bin/python3" ]; then
    PY="venv/bin/python3"
else
    PY="python3"
fi

# --- STEP 2: DATA PROCESSING (BASE RUN) ---
echo -e "\n${YELLOW}▶ STEP 2: Parsing Base Runtime Metrics...${NC}"
$PY data_processing/parser.py --scenario "$SCENARIO" > /dev/null || { echo -e "${RED}[ERROR] Parser failed.${NC}"; exit 1; }
check_file "outputs/processed/metrics.json"
echo "✔ Base metrics parsed successfully."

# --- STEP 3: ADAPTIVE SIMULATION (Inline Rerouting) ---
echo -e "\n${YELLOW}▶ STEP 3: Running Adaptive Routing Simulation (Inline)...${NC}"
# Ensure routing directory exists and delete old routing JSON to force rewrite
mkdir -p outputs/routing
rm -f outputs/routing/routing.json
bash ns3_simulation/run_simulation.sh "$SCENARIO" true > /dev/null 2>&1 || { echo -e "${RED}[ERROR] Adaptive Simulation failed.${NC}"; exit 1; }
check_file "outputs/routing/routing.json"
echo "✔ Adaptive simulation complete. Routing decisions logged."

# --- STEP 4: DATA PROCESSING (ADAPTIVE RUN) ---
echo -e "\n${YELLOW}▶ STEP 4: Appending Adaptive Metrics for Comparison...${NC}"
$PY data_processing/parser.py --scenario "$SCENARIO" > /dev/null || { echo -e "${RED}[ERROR] Final Parser pass failed.${NC}"; exit 1; }
echo "✔ Adaptive metrics appended successfully."

# --- STEP 5: ML COST CLASSIFICATION ---
# (Dashboard uses costs.json to display the AI's classification state)
echo -e "\n${YELLOW}▶ STEP 5: Generating Final ML Classification...${NC}"
$PY ml_model/predict.py > /dev/null 2>&1 || { echo -e "${RED}[ERROR] ML Engine failed.${NC}"; exit 1; }
check_file "outputs/ml/costs.json"
echo "✔ Scenario classification inferred from telemetry and saved."

# --- STEP 6: LAUNCH NETANIM ---
echo -e "\n${YELLOW}▶ STEP 6: Launching NetAnim Visualization...${NC}"
if [ -f "netanim/NetAnim" ]; then
    # Check if NetAnim is already running and kill it to prevent multiple windows
    if pgrep -x "NetAnim" > /dev/null
    then
        echo "Closing existing NetAnim window..."
        pkill -x "NetAnim"
        sleep 1 # Give it a second to close gracefully
    fi
    
    ./netanim/NetAnim animation.xml &
    echo "✔ NetAnim launched in the background."
else
    echo -e "${RED}[WARNING] NetAnim executable not found in netanim/ directory!${NC}"
fi

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}  Pipeline completed successfully for $SCENARIO!      ${NC}"
echo -e "${GREEN}======================================================${NC}"

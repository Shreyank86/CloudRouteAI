#!/bin/bash
# ============================================================
# CloudRouteAI — Phase 1 Simulation Runner
# ============================================================
# Usage:
#   ./run_simulation.sh <scenario>
# ============================================================

set -e

NS3_DIR="$HOME/ns-3-dev"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RAW_DIR="$PROJECT_DIR/outputs/raw"
SIM_SRC="$PROJECT_DIR/ns3_simulation/simulation.cc"
SCRATCH_DST="$NS3_DIR/scratch/cloudroute.cc"

# Ensure output directories exist
mkdir -p "$RAW_DIR"
mkdir -p "$PROJECT_DIR/outputs/routing"

# Check NS-3 installation
if [ ! -d "$NS3_DIR" ]; then
    echo "ERROR: NS-3 not found at $NS3_DIR"
    echo "Please install NS-3 first. See README.md for instructions."
    exit 1
fi

# Copy simulation source to NS-3 scratch
echo "Copying simulation.cc to NS-3 scratch..."
cp "$SIM_SRC" "$SCRATCH_DST"

SCENARIO="${1:-normal}"
ADAPTIVE="${2:-true}"

echo ""
echo "========================================"
echo "  Running scenario: $SCENARIO (Adaptive=$ADAPTIVE)"
echo "========================================"

cd "$NS3_DIR"
./ns3 run "scratch/cloudroute --scenario=$SCENARIO --adaptive=$ADAPTIVE"

# Copy FlowMonitor output
if [ -f "$NS3_DIR/flowmon.xml" ]; then
    cp "$NS3_DIR/flowmon.xml" "$RAW_DIR/flow.xml"
    echo "  ✔ Copied flowmon.xml -> outputs/raw/flow.xml"
else
    echo "  ✘ WARNING: flowmon.xml not found"
fi

# Copy NetAnim output
if [ -f "$NS3_DIR/animation.xml" ]; then
    cp "$NS3_DIR/animation.xml" "$PROJECT_DIR/animation.xml"
    echo "  ✔ Copied animation.xml -> animation.xml"
else
    echo "  ✘ WARNING: animation.xml not found"
fi

# Copy runtime metrics output
if [ -f "$NS3_DIR/runtime_metrics.json" ]; then
    cp "$NS3_DIR/runtime_metrics.json" "$RAW_DIR/runtime_metrics.json"
    echo "  ✔ Copied runtime_metrics.json -> outputs/raw/runtime_metrics.json"
else
    echo "  ✘ WARNING: runtime_metrics.json not found"
fi

echo ""
echo "========================================"
echo "  Simulation complete!"
echo "========================================"
echo ""
echo "Outputs:"
echo "  FlowMonitor: $RAW_DIR/flow.xml"
echo "  Metrics:     $RAW_DIR/runtime_metrics.json"
echo "  NetAnim:     $PROJECT_DIR/animation.xml"

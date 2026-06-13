#!/bin/bash
# CloudRouteAI — End-to-End Master Execution Script (Cross-Platform)

set -e # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCENARIO="${1:-normal}"

# Use venv python if available
if [ -f "venv/bin/python" ]; then
    PY="venv/bin/python"
elif [ -f "venv/bin/python3" ]; then
    PY="venv/bin/python3"
elif [ -f ".venv/bin/python" ]; then
    PY=".venv/bin/python"
elif [ -f ".venv/bin/python3" ]; then
    PY=".venv/bin/python3"
else
    PY="python3"
fi

$PY run_all.py "$SCENARIO"

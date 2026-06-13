#!/bin/bash
# CloudRouteAI Dashboard Launcher

echo "=================================================="
echo "  CloudRouteAI — Phase 5 Dashboard"
echo "=================================================="
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Starting the interactive dashboard..."
echo "Press Ctrl+C to stop."
echo "=================================================="

python run_dashboard.py

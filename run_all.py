#!/usr/bin/env python3
"""
CloudRouteAI — Windows & Cross-Platform Orchestration Script
Runs the pure-Python NetworkX simulation for baseline & adaptive scenarios,
generates telemetry and comparison reports, and saves them to outputs/.
"""

import os
import sys
import shutil
import argparse

# Define directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
RAW_DIR = os.path.join(OUTPUTS_DIR, "raw")
ML_DIR = os.path.join(OUTPUTS_DIR, "ml")
ROUTING_DIR = os.path.join(OUTPUTS_DIR, "routing")
PROCESSED_DIR = os.path.join(OUTPUTS_DIR, "processed")

# Add dashboard and ml_model to path for imports
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

def clean_directory(dir_path):
    if os.path.exists(dir_path):
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="CloudRouteAI Orchestrator")
    parser.add_argument("scenario", nargs="?", default="normal", 
                        choices=["normal", "congestion", "failure", "spike"],
                        help="Network scenario to simulate (default: normal)")
    args = parser.parse_args()
    
    scenario = args.scenario.lower()
    
    print("======================================================")
    print(f"      CloudRouteAI — Unified Pipeline: {scenario.upper()}")
    print("======================================================")
    
    # STEP 0: CLEANUP
    print("\n> STEP 0: Cleaning previous run data...")
    for d in [RAW_DIR, ML_DIR, ROUTING_DIR, PROCESSED_DIR]:
        os.makedirs(d, exist_ok=True)
        clean_directory(d)
    print("OK: Workspace cleaned.")
    
    # STEP 1: RUN SIMULATIONS
    print(f"\n> STEP 1: Running Python Simulations (Baseline & Adaptive)...")
    try:
        from network_simulator import run_and_save
        
        print(f"  [Sim] Executing NetworkX Simulation Engine for '{scenario}' scenario...")
        run_and_save(scenario)
        print("OK: Simulations complete. Telemetry, cost maps, and comparison metrics generated.")
        
    except Exception as e:
        print(f"\n[ERROR] Simulation execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print("\n======================================================")
    print(f"  Pipeline completed successfully for {scenario}!      ")
    print("======================================================")

if __name__ == "__main__":
    main()

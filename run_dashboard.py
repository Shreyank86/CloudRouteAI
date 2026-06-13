#!/usr/bin/env python3
"""
CloudRouteAI Launcher Script.
Starts the Telemetry Receiver on port 8000 and the Streamlit Dashboard on port 8501.
Cleans up both processes on Ctrl+C.
"""

import sys
import os
import subprocess
import time

def main():
    print("==================================================")
    print("   CloudRouteAI — Unified Dashboard Launcher")
    print("==================================================")
    
    # Identify Python interpreter
    python_exe = sys.executable
    print(f"Using Python: {python_exe}")
    
    # 1. Start Telemetry Receiver
    print("\n> Starting Telemetry Receiver on port 8000...")
    receiver_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telemetry", "receiver.py")
    
    receiver_proc = subprocess.Popen(
        [python_exe, receiver_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Give it a brief moment to check port
    time.sleep(1)
    
    # Check if the process exited early (e.g., port already in use or error)
    ret = receiver_proc.poll()
    if ret is not None:
        print("Telemetry Receiver process ended early. Check if it's already running.")
    else:
        print("Telemetry Receiver started in background.")

    # 2. Start Streamlit Dashboard
    print("\n> Starting Streamlit Dashboard on port 8501...")
    dashboard_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "app.py")
    
    dashboard_proc = subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", dashboard_script, "--server.port", "8501", "--server.headless", "true"]
    )
    
    print("\n==================================================")
    print("CloudRouteAI is running!")
    print("- Telemetry API: http://localhost:8000")
    print("- Dashboard:     http://localhost:8501")
    print("Press Ctrl+C to terminate both services.")
    print("==================================================")
    
    try:
        # Keep launcher running while dashboard runs
        while True:
            # Check if dashboard has exited
            if dashboard_proc.poll() is not None:
                print("Dashboard process stopped.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down CloudRouteAI services...")
    finally:
        # Clean shutdown
        if dashboard_proc.poll() is None:
            print("Terminating Dashboard...")
            dashboard_proc.terminate()
            try:
                dashboard_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                dashboard_proc.kill()
                
        if receiver_proc.poll() is None:
            print("Terminating Telemetry Receiver...")
            receiver_proc.terminate()
            try:
                receiver_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                receiver_proc.kill()
                
        print("Shutdown complete.")

if __name__ == "__main__":
    main()

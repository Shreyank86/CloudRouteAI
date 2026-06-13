from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
import socket

# Add local directory to path to enable clean imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client_registry import register_client

app = FastAPI(title="CloudRouteAI Telemetry Receiver")

@app.post("/telemetry")
async def receive_telemetry_endpoint(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Invalid JSON format"}
        )
        
    device_id = payload.get("device_id")
    if not device_id:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"status": "error", "message": "Missing required field: device_id"}
        )
        
    register_client(device_id, payload)
    return {"status": "success", "message": "Telemetry processed successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a given port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, OSError):
            return False

def run_receiver(host="0.0.0.0", port=8000):
    """
    Programmatic entry point to run uvicorn server in a separate thread.
    Silently skips startup if the port is already bound (e.g. on Streamlit re-runs).
    """
    if is_port_in_use(port):
        # Server is already running — skip silently
        return
    try:
        uvicorn.run(app, host=host, port=port, log_level="warning")
    except OSError as e:
        # Port occupied by a race condition — ignore
        print(f"[TelemetryServer] Port {port} already in use, skipping: {e}")

if __name__ == "__main__":
    print("Starting CloudRouteAI Telemetry Server on port 8000...")
    if is_port_in_use(8000):
        print("Port 8000 is already in use. The Telemetry Server is already running.")
        sys.exit(0)
    run_receiver()

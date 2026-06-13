import requests
from config import SERVER_URL

def send_telemetry(payload):
    """Sends telemetry JSON payload to the FastAPI server receiver endpoint."""
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=2.0)
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, f"Server returned error code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

import os

# Server endpoint URL where telemetry is POSTed
# Can be set via environment variable for remote client deployments
SERVER_IP = os.environ.get("CLOUDROUTE_SERVER_IP", "localhost")
SERVER_URL = f"http://{SERVER_IP}:8000/telemetry"

# Polling and reporting interval in seconds
POLLING_INTERVAL = 1.0

# File path to persist the unique device ID
CONFIG_FILE_PATH = "device_config.json"

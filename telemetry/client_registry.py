try:
    from telemetry.telemetry_storage import storage
except ImportError:
    from telemetry_storage import storage

def register_client(device_id, payload):
    """Registers or updates a client with its latest telemetry data."""
    storage.update_client(device_id, payload)

def get_registered_clients(timeout=5.0):
    """Retrieves all active registered clients."""
    return storage.get_active_clients(timeout_sec=timeout)

def is_client_active(device_id, timeout=5.0):
    """Checks if a specific client is currently active."""
    clients = get_registered_clients(timeout)
    return any(c["device_id"] == device_id for c in clients)

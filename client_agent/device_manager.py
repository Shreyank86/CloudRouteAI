import os
import uuid
import json
from config import CONFIG_FILE_PATH

def get_or_create_device_id():
    """Reads the device UUID from local config or generates and saves a new one."""
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                config = json.load(f)
                device_id = config.get("device_id")
                if device_id:
                    return device_id
        except Exception as e:
            print(f"Error reading local device configuration: {e}")
            
    # Generate a new persistent UUID
    new_device_id = str(uuid.uuid4())
    config_data = {"device_id": new_device_id}
    
    try:
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(config_data, f, indent=2)
        print(f"Registered new client agent device: {new_device_id}")
    except Exception as e:
        print(f"Failed to persist device configuration locally: {e}")
        
    return new_device_id

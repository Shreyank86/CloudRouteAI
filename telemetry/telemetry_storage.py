import time
import threading
import json
import os

# Temp file path shared between the FastAPI thread and Streamlit reads
_STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".telemetry_cache.json")
_lock = threading.Lock()


# Idle threshold (in Mbps) below which we retain the last known active telemetry
IDLE_THRESHOLD_MBPS = 2.0


def _read_file():
    """Read the JSON cache file, returning empty dict on FileNotFoundError, None on other errors."""
    for i in range(10):
        try:
            with open(_STORAGE_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except (PermissionError, json.JSONDecodeError):
            time.sleep(0.05)
        except Exception:
            time.sleep(0.05)
    return None


def _write_file(data: dict):
    """Write the client dict to the JSON cache file atomically with retries on lock collision."""
    tmp = _STORAGE_FILE + ".tmp"
    for i in range(10):
        try:
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(tmp, _STORAGE_FILE)
            return True
        except PermissionError:
            time.sleep(0.05)
        except Exception:
            time.sleep(0.05)
    return False


class TelemetryStorage:
    """
    Thread-safe telemetry store backed by a local JSON file.
    Using a file ensures Streamlit re-runs (new thread contexts) always
    see the data written by the FastAPI request handler thread.
    """

    def __init__(self):
        # In-memory mirror kept in sync with the file
        self._clients: dict = {}
        self._load_from_file()

    def _load_from_file(self):
        with _lock:
            data = _read_file()
            if data is not None:
                self._clients = data

    def update_client(self, device_id: str, payload: dict):
        """Register / refresh a client record and persist to file."""
        total_throughput = round(float(payload.get("total_throughput_mbps", 0.0)), 2)
        upload_rate = round(float(payload.get("upload_rate_mbps", 0.0)), 2)
        download_rate = round(float(payload.get("download_rate_mbps", 0.0)), 2)
        active_connections = int(payload.get("active_connections", 0))

        with _lock:
            # Load current state first to check previous values
            data = _read_file()
            if data is not None:
                self._clients = data

            prev_record = self._clients.get(device_id)
            if prev_record and total_throughput < IDLE_THRESHOLD_MBPS:
                # If we have a previous record and it was above the active threshold,
                # retain the previous active metrics instead of dropping to 0.x.
                prev_throughput = prev_record.get("total_throughput_mbps", 0.0)
                if prev_throughput >= IDLE_THRESHOLD_MBPS:
                    total_throughput = prev_throughput
                    upload_rate = prev_record.get("upload_rate_mbps", 0.0)
                    download_rate = prev_record.get("download_rate_mbps", 0.0)
                    active_connections = prev_record.get("active_connections", 0)

            record = {
                "device_id": device_id,
                "timestamp": payload.get("timestamp", time.time()),
                "bytes_sent": payload.get("bytes_sent", 0),
                "bytes_received": payload.get("bytes_received", 0),
                "upload_rate_mbps": upload_rate,
                "download_rate_mbps": download_rate,
                "total_throughput_mbps": total_throughput,
                "active_connections": active_connections,
                "last_seen": time.time(),
            }
            self._clients[device_id] = record
            _write_file(self._clients)

    def get_active_clients(self, timeout_sec: float = 600.0) -> list:
        """Return list of clients seen within timeout_sec, pruning stale ones."""
        now = time.time()
        # Always reload from file so Streamlit picks up fresh data
        with _lock:
            data = _read_file()
            if data is not None:
                self._clients = data
            stale = [k for k, v in self._clients.items()
                     if now - v.get("last_seen", 0) > timeout_sec]
            for k in stale:
                del self._clients[k]
            if stale:
                _write_file(self._clients)
            return [v.copy() for v in self._clients.values()]

    def get_aggregated_throughput(self, timeout_sec: float = 600.0) -> float:
        """Compute total throughput across all active clients."""
        active = self.get_active_clients(timeout_sec)
        return sum(c["total_throughput_mbps"] for c in active)


# Global singleton
storage = TelemetryStorage()

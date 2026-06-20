import time
import json
import os
import redis
from datetime import datetime

# Idle threshold (in Mbps) below which we retain the last known active telemetry
IDLE_THRESHOLD_MBPS = 2.0

class TelemetryStorage:
    """
    Thread-safe telemetry store backed by Redis.
    Using Redis ensures different Pods (API and Dashboard) can share data seamlessly.
    """

    def __init__(self):
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        port_env = os.environ.get("REDIS_PORT", "6379")
        if port_env.startswith("tcp://"):
            redis_port = 6379
        else:
            try:
                redis_port = int(port_env)
            except ValueError:
                redis_port = 6379
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    def update_client(self, device_id: str, payload: dict):
        """Register / refresh a client record and persist to Redis."""
        total_throughput = round(float(payload.get("total_throughput_mbps", 0.0)), 2)
        upload_rate = round(float(payload.get("upload_rate_mbps", 0.0)), 2)
        download_rate = round(float(payload.get("download_rate_mbps", 0.0)), 2)
        active_connections = int(payload.get("active_connections", 0))

        try:
            prev_record_str = self.redis_client.hget("telemetry_clients", device_id)
            if prev_record_str:
                prev_record = json.loads(prev_record_str)
                if total_throughput < IDLE_THRESHOLD_MBPS:
                    prev_throughput = prev_record.get("total_throughput_mbps", 0.0)
                    if prev_throughput >= IDLE_THRESHOLD_MBPS:
                        total_throughput = prev_throughput
                        upload_rate = prev_record.get("upload_rate_mbps", 0.0)
                        download_rate = prev_record.get("download_rate_mbps", 0.0)
                        active_connections = prev_record.get("active_connections", 0)
        except redis.RedisError:
            pass

        raw_ts = payload.get("timestamp", time.time())
        if isinstance(raw_ts, (int, float)):
            ts_str = datetime.fromtimestamp(raw_ts).isoformat()
        else:
            ts_str = str(raw_ts)

        record = {
            "device_id": device_id,
            "timestamp": ts_str,
            "bytes_sent": payload.get("bytes_sent", 0),
            "bytes_received": payload.get("bytes_received", 0),
            "upload_rate_mbps": upload_rate,
            "download_rate_mbps": download_rate,
            "total_throughput_mbps": total_throughput,
            "active_connections": active_connections,
            "last_seen": datetime.now().isoformat(),
        }
        
        try:
            self.redis_client.hset("telemetry_clients", device_id, json.dumps(record))
        except redis.RedisError as e:
            print(f"[TelemetryStorage] Redis Error: {e}")

    def get_active_clients(self, timeout_sec: float = 600.0) -> list:
        """Return list of clients seen within timeout_sec, pruning stale ones."""
        now_dt = datetime.now()
        active_clients = []
        stale_devices = []

        try:
            all_clients = self.redis_client.hgetall("telemetry_clients")
            for device_id, record_str in all_clients.items():
                record = json.loads(record_str)
                ls = record.get("last_seen", 0)
                is_stale = False
                
                if isinstance(ls, str):
                    try:
                        ls_time = datetime.fromisoformat(ls)
                        if (now_dt - ls_time).total_seconds() > timeout_sec:
                            is_stale = True
                    except ValueError:
                        is_stale = True
                else:
                    if time.time() - float(ls) > timeout_sec:
                        is_stale = True
                
                if is_stale:
                    stale_devices.append(device_id)
                else:
                    active_clients.append(record)
                    
            if stale_devices:
                self.redis_client.hdel("telemetry_clients", *stale_devices)
                
        except redis.RedisError as e:
            print(f"[TelemetryStorage] Redis Error: {e}")

        return active_clients

    def get_aggregated_throughput(self, timeout_sec: float = 600.0) -> float:
        """Compute total throughput across all active clients."""
        active = self.get_active_clients(timeout_sec)
        return sum(c.get("total_throughput_mbps", 0.0) for c in active)

# Global singleton
storage = TelemetryStorage()

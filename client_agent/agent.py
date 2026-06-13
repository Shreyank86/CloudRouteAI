import time
import sys
import os
import psutil

# Add local directory to path for clean imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import POLLING_INTERVAL
from device_manager import get_or_create_device_id
from telemetry_sender import send_telemetry

def get_active_connections():
    """Gathers the count of established network connections, catching permission exceptions."""
    try:
        connections = psutil.net_connections(kind="inet")
        return len([c for c in connections if c.status == "ESTABLISHED"])
    except (psutil.AccessDenied, Exception):
        # Fallback if execution environment doesn't have system admin privileges
        return 0

def main():
    device_id = get_or_create_device_id()
    print("======================================================")
    print("      CloudRouteAI — Client Telemetry Agent            ")
    print("======================================================")
    print(f"Device ID : {device_id}")
    print(f"Sampling  : Every {POLLING_INTERVAL} seconds")
    print("------------------------------------------------------")
    print("Starting client agent telemetry loop...")
    print("Press Ctrl+C to terminate.")
    print("------------------------------------------------------")
    
    # Get initial values
    try:
        io_start = psutil.net_io_counters()
        bytes_sent_prev = io_start.bytes_sent
        bytes_recv_prev = io_start.bytes_recv
        time_prev = time.time()
    except Exception as e:
        print(f"Failed to query system network adapters: {e}")
        sys.exit(1)
        
    while True:
        try:
            time.sleep(POLLING_INTERVAL)
            
            # Query updated network and connection states
            io_now = psutil.net_io_counters()
            time_now = time.time()
            
            bytes_sent_now = io_now.bytes_sent
            bytes_recv_now = io_now.bytes_recv
            
            # Calculate rates in Mbps
            elapsed_time = time_now - time_prev
            if elapsed_time <= 0:
                elapsed_time = 0.001
                
            upload_bps = (bytes_sent_now - bytes_sent_prev) / elapsed_time
            download_bps = (bytes_recv_now - bytes_recv_prev) / elapsed_time
            
            upload_mbps = (upload_bps * 8) / (1024 * 1024)
            download_mbps = (download_bps * 8) / (1024 * 1024)
            total_mbps = upload_mbps + download_mbps
            
            active_conn = get_active_connections()
            
            payload = {
                "device_id": device_id,
                "timestamp": time_now,
                "bytes_sent": bytes_sent_now,
                "bytes_received": bytes_recv_now,
                "upload_rate_mbps": round(upload_mbps, 4),
                "download_rate_mbps": round(download_mbps, 4),
                "total_throughput_mbps": round(total_mbps, 4),
                "active_connections": active_conn
            }
            
            # Print localized status update
            print(f"[{time.strftime('%H:%M:%S')}] Out: {upload_mbps:6.2f} Mbps | In: {download_mbps:6.2f} Mbps | Total: {total_mbps:6.2f} Mbps | Conn: {active_conn:2d}", end="")
            
            # Transmit telemetry
            success, msg = send_telemetry(payload)
            if success:
                print(" | Sent: OK")
            else:
                print(f" | Sent: FAILED ({msg})")
                
            # Update history metrics
            bytes_sent_prev = bytes_sent_now
            bytes_recv_prev = bytes_recv_now
            time_prev = time_now
            
        except KeyboardInterrupt:
            print("\nTerminating client agent telemetry loop. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Telemetry extraction error: {e}")
            time.sleep(2.0)  # Pause before retry

if __name__ == "__main__":
    main()

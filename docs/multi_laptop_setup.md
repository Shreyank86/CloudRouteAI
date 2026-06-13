# Multi-Laptop Setup Guide for Real-Time Telemetry

This guide explains how to connect 2 or more laptops to demonstrate real-time telemetry collection and intelligent routing in **CloudRouteAI**.

In this setup:
1. **Server Laptop**: Runs the main application dashboard (Streamlit) and the telemetry receiver (FastAPI).
2. **Client Laptop(s)**: Run the client agent (`client_agent/agent.py`) to stream system telemetry to the Server Laptop.

---

## Pre-requisites
On all **Client Laptops**, make sure Python and the required libraries are installed:
```bash
pip install psutil requests
```

---

## Phase 1: Establish Network Connectivity
Both laptops must be able to communicate with each other over the network. Choose **one** of the following scenarios:

### Scenario A: Same Wi-Fi Network (Standard)
1. Connect both the **Server Laptop** and all **Client Laptops** to the same Wi-Fi network (home, office, or university Wi-Fi).
> [!WARNING]
> Some public or corporate Wi-Fi networks enable **Client Isolation**, which blocks devices on the same network from talking to each other. If this happens, use **Scenario B**.

### Scenario B: Mobile Hotspot (Recommended for Demos)
If you are at a venue with restricted Wi-Fi, you can use a phone or one of the laptops as a hotspot:
1. Enable the Wi-Fi Hotspot on a smartphone (or configure a Windows Mobile Hotspot on the Server Laptop).
2. Connect all laptops to this hotspot.
3. This creates a secure, local LAN without any firewall blockades or client isolation.

### Scenario C: Direct Ethernet Cable
1. Connect an Ethernet cable directly between the two laptops.
2. If Windows does not automatically assign IP addresses, you may need to configure static IPs manually:
   - **Server Laptop IP**: `192.168.1.1` (Subnet: `255.255.255.0`)
   - **Client Laptop IP**: `192.168.1.2` (Subnet: `255.255.255.0`)

---

## Phase 2: Find the Server Laptop's IP Address
On the **Server Laptop**:
1. Open **Command Prompt** or **PowerShell**.
2. Run the command:
   ```cmd
   ipconfig
   ```
3. Find your active adapter (e.g., `Wireless LAN adapter Wi-Fi` or `Ethernet adapter`).
4. Locate the **IPv4 Address**. Note this down (e.g., `192.168.1.15`).

---

## Phase 3: Configure and Run the Client Agent
On the **Client Laptop(s)**:

### Option 1: Via Environment Variable (Recommended - no file edits)
Open Command Prompt or PowerShell and set the environment variable, then launch the agent:
* **Windows Command Prompt (CMD)**:
  ```cmd
  set CLOUDROUTE_SERVER_IP=192.168.1.15
  python client_agent/agent.py
  ```
* **Windows PowerShell**:
  ```powershell
  $env:CLOUDROUTE_SERVER_IP="192.168.1.15"
  python client_agent/agent.py
  ```
*(Replace `192.168.1.15` with the Server Laptop's IP address found in Phase 2).*

### Option 2: Via Editing Configuration File
1. Open the file `client_agent/config.py`.
2. Locate the line:
   ```python
   SERVER_IP = os.environ.get("CLOUDROUTE_SERVER_IP", "localhost")
   ```
3. Replace `"localhost"` with the Server's IP address:
   ```python
   SERVER_IP = os.environ.get("CLOUDROUTE_SERVER_IP", "192.168.1.15")
   ```
4. Run the agent:
   ```bash
   python client_agent/agent.py
   ```

---

## Phase 4: Troubleshooting Connection Issues

If the client console prints `Sent: FAILED (Connection error...)`, follow these diagnostic steps:

### 1. Test Network Ping
On the **Client Laptop**, open CMD and ping the Server:
```cmd
ping 192.168.1.15
```
* If you get a reply, network connectivity is established. Move to the Firewall check.
* If you get `Request timed out`, the laptops cannot see each other. Double check they are on the same Wi-Fi/Hotspot network.

### 2. Configure Windows Defender Firewall (on Server Laptop)
If ping works but the agent cannot connect, the Server Laptop's firewall is blocking incoming connections on port `8000`.

To allow access:
1. On the **Server Laptop**, press the Windows Key and search for **Windows Defender Firewall with Advanced Security**.
2. Click **Inbound Rules** in the left sidebar.
3. Click **New Rule...** in the right sidebar.
4. Select **Port** and click Next.
5. Choose **TCP**, and under **Specific local ports**, enter `8000`. Click Next.
6. Choose **Allow the connection** and click Next.
7. Leave Domain, Private, and Public checked. Click Next.
8. Name it `CloudRouteAI Telemetry Receiver` and click Finish.
9. Restart the client agent on the client laptop.

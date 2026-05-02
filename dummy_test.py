import json
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processing.parser import parse_flowmon_xml

dummy_xml_content = """<?xml version="1.0" ?>
<FlowMonitor>
  <FlowStats>
    <Flow flowId="1" timeFirstTxPacket="+1.0s" timeFirstRxPacket="+1.1s" timeLastTxPacket="+2.0s" timeLastRxPacket="+2.2s" delaySum="+1.5s" jitterSum="+0.2s" txBytes="1000" rxBytes="900" txPackets="100" rxPackets="90" lostPackets="10" timesForwarded="10">
    </Flow>
    <Flow flowId="2" timeFirstTxPacket="+1.0s" timeFirstRxPacket="+1.1s" timeLastTxPacket="+2.0s" timeLastRxPacket="+2.2s" delaySum="+0.5s" jitterSum="+0.1s" txBytes="500" rxBytes="500" txPackets="50" rxPackets="50" lostPackets="0" timesForwarded="5">
    </Flow>
  </FlowStats>
  <Ipv4FlowClassifier>
    <Flow flowId="1" sourceAddress="10.1.2.1" destinationAddress="10.1.5.2" protocol="17" sourcePort="49153" destinationPort="9">
    </Flow>
    <Flow flowId="2" sourceAddress="10.1.3.1" destinationAddress="10.1.7.2" protocol="17" sourcePort="49154" destinationPort="9">
    </Flow>
  </Ipv4FlowClassifier>
</FlowMonitor>
"""

def main():
    dummy_path = "dummy_flow.xml"
    with open(dummy_path, "w") as f:
        f.write(dummy_xml_content)
    
    print("=== Created dummy_flow.xml ===")
    print("Testing parser on dummy file...\n")
    
    try:
        result = parse_flowmon_xml(dummy_path, "dummy_scenario")
        print("=== Parser Output (JSON) ===")
        print(json.dumps(result, indent=2))
        print("============================")
        
        # Verify specific calculations
        print("\n=== Verification ===")
        print("Flow 1 Expected vs Actual:")
        # delaySum=1.5, rxPackets=90 -> latency_ms = (1.5 / 90) * 1000 = 16.666...
        print(f"Expected latency_ms:  16.666... | Actual: {result['flows'][0]['latency_ms']}")
        # txPackets=100, rxPackets=90 -> loss_rate = (100 - 90) / 100 = 0.1
        print(f"Expected packet_loss: 0.1       | Actual: {result['flows'][0]['packet_loss_rate']}")
        # src_node from 10.1.2.1 -> 2
        print(f"Expected src_node:    2         | Actual: {result['flows'][0]['src_node']}")
        print(f"Expected dst_node:    5         | Actual: {result['flows'][0]['dst_node']}")

    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    main()

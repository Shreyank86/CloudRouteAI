import json
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processing.parser import parse_flowmon_xml, validate_output

dummy_xml_content = """<?xml version="1.0" ?>
<FlowMonitor>
  <FlowStats>
    <Flow flowId="1" timeFirstTxPacket="+1.0s" timeFirstRxPacket="+1.1s" timeLastTxPacket="+2.0s" timeLastRxPacket="+2.2s" delaySum="+1.5s" jitterSum="+0.2s" txBytes="1000" rxBytes="900" txPackets="100" rxPackets="90" lostPackets="10" timesForwarded="10">
    </Flow>
  </FlowStats>
  <Ipv4FlowClassifier>
    <Flow flowId="1" sourceAddress="10.1.2.1" destinationAddress="10.1.5.2" protocol="17" sourcePort="49153" destinationPort="9">
    </Flow>
  </Ipv4FlowClassifier>
</FlowMonitor>
"""

def main():
    dummy_path = "dummy_test_flow.xml"
    with open(dummy_path, "w") as f:
        f.write(dummy_xml_content)
    
    try:
        print("="*60)
        print("  STEP 1: RAW INPUT (XML FORMAT)")
        print("="*60)
        print("File: " + dummy_path)
        print(dummy_xml_content.strip())
        print()
        
        print("="*60)
        print("  STEP 2: TRIGGERING PARSER (M2)")
        print("="*60)
        print("Calling parse_flowmon_xml(dummy_test_flow.xml) ...")
        result = parse_flowmon_xml(dummy_path, "dummy_scenario")
        print("Parsing completed.")
        print()
        
        print("="*60)
        print("  STEP 3: TRIGGERING VALIDATION")
        print("="*60)
        print("Calling validate_output(result) ...")
        errors = validate_output(result, "dummy_scenario")
        if not errors:
            print("Validation PASSED (No nulls, all floats, required fields exist).")
        else:
            print(f"Validation FAILED: {errors}")
        print()
        
        print("="*60)
        print("  STEP 4: PROCESSED OUTPUT (JSON FORMAT)")
        print("="*60)
        print(json.dumps(result, indent=2))
        print("="*60)

    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    main()

#!/bin/bash

cd ~/ns-3-dev || exit

# Run simulation
./ns3 run scratch/cloudroute

# Copy outputs properly
cp flowmon.xml ~/cloudroute-ai/outputs/raw/ 2>/dev/null
cp animation.xml ~/cloudroute-ai/ 2>/dev/null

echo "✔ Simulation complete"

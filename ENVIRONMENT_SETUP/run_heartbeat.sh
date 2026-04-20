#!/bin/bash
python3 /app/ENVIRONMENT_SETUP/heartbeat.py > /app/ENVIRONMENT_SETUP/agent_heartbeat.log 2>&1 &
echo "Heartbeat daemon started."

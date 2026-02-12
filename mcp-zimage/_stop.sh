#!/bin/bash

echo "Stopping Z-Image MCP Server..."
if [ -f server.pid ]; then
    PID=$(cat server.pid)
    echo "Stopping server with PID $PID..."
    kill $PID
    rm server.pid
else
    echo "PID file not found. attempting pkill..."
    pkill -f "src.server"
fi

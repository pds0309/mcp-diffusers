#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

export PYTHONPATH=./src

nohup python -m server > server.log 2>&1 &
echo $! > server.pid
echo "Server started with PID $(cat server.pid)"

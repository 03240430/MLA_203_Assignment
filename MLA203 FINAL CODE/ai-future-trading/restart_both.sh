#!/usr/bin/env bash
# Restart both bots (simple)
pkill -f main.py || true
python main.py &
echo "Started main.py in background"

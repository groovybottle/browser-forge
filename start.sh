#!/bin/bash
cd "$(dirname "$0")"
# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
echo "browser-forge starting (port 19922)..."
python server.py

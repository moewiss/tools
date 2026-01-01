#!/bin/bash
# Quick Start Script (assumes venv already exists)

echo "Starting RKIEH Solutions Media Tool..."

if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Run './setup_and_start.sh' first to set up the environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the app
python3 web_app.py


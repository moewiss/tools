#!/bin/bash
# Kill process using port 5000

echo "Finding process on port 5000..."

# Find process ID using port 5000
PID=$(lsof -ti:5000 2>/dev/null)

if [ -z "$PID" ]; then
    echo "No process found using port 5000"
else
    echo "Found process $PID using port 5000"
    echo "Killing process..."
    kill -9 $PID
    echo "Process killed successfully!"
fi


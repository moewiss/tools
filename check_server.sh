#!/bin/bash
# Check if server is running and show status

echo "=========================================="
echo "  Server Status Check"
echo "=========================================="
echo ""

# Check if port 5001 is in use
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✅ Server is RUNNING on port 5001"
    echo ""
    echo "Process details:"
    lsof -i :5001
    echo ""
    echo "📍 Access URLs:"
    echo "   • http://localhost:5001"
    echo "   • http://$(hostname -I | awk '{print $1}'):5001"
else
    echo "❌ Server is NOT running on port 5001"
    echo ""
    echo "To start the server, run:"
    echo "   bash RUN_SERVER.sh"
fi

echo ""
echo "=========================================="


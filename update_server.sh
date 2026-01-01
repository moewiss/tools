#!/bin/bash

# Quick update script for server
# Run this on the Ubuntu server when you make changes

echo "Updating application from GitHub..."
cd /root/tools
git pull origin main

echo "Restarting service..."
systemctl restart media-tools

echo "Update complete!"
echo "View logs: journalctl -u media-tools -f"


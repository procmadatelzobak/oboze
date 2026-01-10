#!/bin/bash
# Ó bože - Installation Script
# For Ubuntu 24.04 LTS Minimal

set -e

echo "=== Ó bože - Installation ==="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install system dependencies
echo "[1/4] Installing system packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
echo "[2/4] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install dependencies
echo "[3/4] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create config from example if not exists
echo "[4/4] Setting up configuration..."
if [ ! -f "config.yaml" ]; then
    cp config.example.yaml config.yaml
    echo "Created config.yaml from example. Please edit it with your API key."
else
    echo "config.yaml already exists, skipping."
fi

echo ""
echo "=== Installation Complete ==="
echo "Edit config.yaml with your Gemini API key, then run: ./run.sh"

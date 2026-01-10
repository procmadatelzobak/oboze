#!/bin/bash
# Ó bože - Run Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run the server
echo "Starting Ó bože server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/bin/bash

# Investment Property Analyzer - Run Script
# Edmund Bogen Team

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the Flask application
echo ""
echo "======================================"
echo "  Investment Property Analyzer"
echo "  Edmund Bogen Team"
echo "======================================"
echo ""
echo "Starting server at http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py

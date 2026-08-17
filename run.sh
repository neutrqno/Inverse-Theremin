#!/bin/bash
# Inverse Theremin - Quick Start Script (macOS/Linux)

echo "================================"
echo "Inverse Theremin - Quick Start"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your configuration:"
    echo "  - HOME_ASSISTANT_URL"
    echo "  - HOME_ASSISTANT_TOKEN"
    echo ""
    echo "Edit config/default_config.json for advanced settings"
    echo ""
fi

# Run the main application
echo ""
echo "Starting Inverse Theremin..."
echo "Press Ctrl+C to stop"
echo ""

python main.py

#!/bin/bash

echo "=================================================="
echo "      Antigravity Cleaner - Mac/Linux Launcher"
echo "=================================================="
echo ""
# Ensure we are in the script's directory
cd "$(dirname "$0")"


# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in your PATH."
    echo "Please install Python 3 using your package manager (brew, apt, yum, etc.)."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements
if [ -f "src/requirements.txt" ]; then
    echo "Checking dependencies..."
    pip install -r src/requirements.txt > /dev/null 2>&1
fi

# Run script (sudo might be needed for some cleanup operations, but we run as user first)
# The script handles permission errors gracefully or user can run the script with sudo
python src/main.py


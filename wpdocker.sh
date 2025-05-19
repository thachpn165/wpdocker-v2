#!/bin/bash
# Startup script for WP Docker v2
# This script activates the virtual environment and starts the application

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running installation script first..."
    ./installers/install.sh
fi

# Activate virtual environment
source .venv/bin/activate

# Run the application
python src/main.py "$@"
#!/bin/bash
# Installer script for WP Docker v2
# This script installs the package and sets up the environment

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

echo "================================================================="
echo "          WP Docker v2 Installation Script                       "
echo "================================================================="

# Check for Python 3.6+
echo "Checking for Python 3.6+..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if python is Python 3.6+
    if [[ $(python --version 2>&1) == *"Python 3."* ]]; then
        PYTHON_CMD="python"
    else
        echo "Python 3.6+ is required but not found. Please install Python 3.6 or higher."
        exit 1
    fi
else
    echo "Python 3.6+ is required but not found. Please install Python 3.6 or higher."
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Determine installation method
INSTALL_METHOD="wheel"
if [ ! -f "pyproject.toml" ]; then
    echo "pyproject.toml not found, using legacy installation method."
    INSTALL_METHOD="legacy"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
$PYTHON_CMD -m venv .venv
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install the package
if [ "$INSTALL_METHOD" == "wheel" ]; then
    echo "Installing using modern Python package method..."
    pip install -e .
else
    echo "Installing using legacy method..."
    pip install -r requirements.txt
fi

# Finalize installation
echo "Creating config directories..."
mkdir -p data/config

# Initial configuration
echo "Performing initial configuration..."
$PYTHON_CMD -c "from src.common.utils.version_helper import initialize_version_info; initialize_version_info()"

echo "================================================================="
echo "Installation completed successfully!"
echo "To start WP Docker, run: source .venv/bin/activate && python src/main.py"
echo "================================================================="
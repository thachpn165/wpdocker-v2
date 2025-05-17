#!/bin/bash
# Script to check the Python virtual environment
# Usage: ./check_venv.sh

# Load utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASH_UTILS_DIR="$INSTALL_DIR/src/bash"
source "$BASH_UTILS_DIR/messages_utils.sh" 2>/dev/null || true

# Fixed installation path
FIXED_INSTALL_DIR="/opt/wp-docker"

# Actual path (used if fixed path doesn't exist)
ACTUAL_INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Use fixed path if it exists, otherwise use actual path
if [ -d "$FIXED_INSTALL_DIR" ] || [ -L "$FIXED_INSTALL_DIR" ]; then
    INSTALL_DIR="$FIXED_INSTALL_DIR"
    print_msg "info" "Using fixed path: $INSTALL_DIR"
else
    INSTALL_DIR="$ACTUAL_INSTALL_DIR"
    print_msg "info" "Using actual path: $INSTALL_DIR"
fi

VENV_DIR="$INSTALL_DIR/.venv"

# Header
echo "=========================="
print_msg "title" "PYTHON VIRTUAL ENVIRONMENT CHECK"
echo "=========================="
echo

# Check system Python
print_msg "step" "Checking system Python"
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_msg "success" "Python is installed: $PYTHON_VERSION"
else
    print_msg "error" "Python not found in system"
    exit 1
fi

# Check virtualenv directory
print_msg "step" "Checking virtual environment directory"
if [ -d "$VENV_DIR" ]; then
    print_msg "success" "Virtual environment directory exists: $VENV_DIR"
    
    # Check directory structure
    if [ -d "$VENV_DIR/bin" ]; then
        print_msg "success" "Bin directory structure exists"
    else
        print_msg "error" "Bin directory not found in virtual environment"
    fi
    
    # Check activate file
    if [ -f "$VENV_DIR/bin/activate" ]; then
        print_msg "success" "Activate file exists"
    else
        print_msg "error" "Activate file not found"
    fi
    
    # Check python file
    if [ -f "$VENV_DIR/bin/python" ]; then
        print_msg "success" "Python file exists"
        VENV_PYTHON_VERSION=$("$VENV_DIR/bin/python" --version 2>&1)
        print_msg "info" "Python version in virtual environment: $VENV_PYTHON_VERSION"
    else
        print_msg "error" "Python file not found in virtual environment"
    fi
    
    # Check pip file
    if [ -f "$VENV_DIR/bin/pip" ]; then
        print_msg "success" "Pip file exists"
        VENV_PIP_VERSION=$("$VENV_DIR/bin/pip" --version 2>&1)
        print_msg "info" "Pip version in virtual environment: $VENV_PIP_VERSION"
    else
        print_msg "error" "Pip file not found in virtual environment"
    fi
else
    print_msg "error" "Virtual environment directory does not exist: $VENV_DIR"
fi

# Activate and check virtual environment
print_msg "step" "Activating and checking virtual environment"
if [ -f "$VENV_DIR/bin/activate" ]; then
    # Save current Python path
    CURRENT_PYTHON_PATH=$(which python3)
    
    # Activate virtual environment
    print_msg "info" "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Check Python path after activation
    VENV_PYTHON_PATH=$(which python)
    if [[ "$VENV_PYTHON_PATH" == *"$VENV_DIR"* ]]; then
        print_msg "success" "Virtual environment activated successfully"
        print_msg "info" "Python path before activation: $CURRENT_PYTHON_PATH"
        print_msg "info" "Python path after activation: $VENV_PYTHON_PATH"
    else
        print_msg "error" "Virtual environment activation failed"
        print_msg "info" "Python path is still: $VENV_PYTHON_PATH"
    fi
    
    # Check VIRTUAL_ENV environment variable
    if [ -n "$VIRTUAL_ENV" ]; then
        print_msg "success" "VIRTUAL_ENV environment variable is set: $VIRTUAL_ENV"
    else
        print_msg "error" "VIRTUAL_ENV environment variable is not set"
    fi
    
    # Try importing some basic modules
    print_msg "info" "Checking module imports..."
    if python -c "import sys; print('Python path:', sys.path)" &>/dev/null; then
        print_msg "success" "Importing sys was successful"
    else
        print_msg "error" "Importing sys failed"
    fi
    
    # Deactivate virtual environment
    deactivate 2>/dev/null || true
else
    print_msg "error" "Cannot activate virtual environment because activate file does not exist"
fi

# Try running the application with Python in the virtual environment
print_msg "step" "Testing ability to run the application with Python in virtual environment"
if [ -f "$VENV_DIR/bin/python" ] && [ -f "$INSTALL_DIR/src/main.py" ]; then
    print_msg "info" "Trying to import modules from the application..."
    
    # Check importing src and src.common
    cd "$INSTALL_DIR"
    print_msg "info" "Current directory: $(pwd)"
    
    # Try to import the 'src' module (without running the actual application)
    if "$VENV_DIR/bin/python" -c "import sys; print('Python path:', sys.path[:3])" 2>/dev/null; then
        print_msg "success" "Python path import successful"
    else
        print_msg "error" "Python path import failed"
    fi
    
    if "$VENV_DIR/bin/python" -c "import src; print('Imported src module successfully')" 2>/dev/null; then
        print_msg "success" "Import src module successful"
    else
        print_msg "error" "Import src module failed"
        ERROR_OUTPUT=$("$VENV_DIR/bin/python" -c "import src" 2>&1)
        print_msg "info" "Error: $ERROR_OUTPUT"
    fi
    
    # Check installed packages
    print_msg "info" "Checking if project is installed as a package..."
    if "$VENV_DIR/bin/pip" show wpdocker &>/dev/null; then
        print_msg "success" "Project is installed as a package (wpdocker)"
        print_msg "info" "Package information:"
        "$VENV_DIR/bin/pip" show wpdocker | sed 's/^/    /'
    else
        print_msg "error" "Project is not installed as a package (wpdocker)"
        print_msg "recommend" "Run 'pip install -e .' in the project directory to install it"
    fi
else
    print_msg "error" "Cannot test application running ability (missing Python in virtualenv or main.py file)"
fi

# Summary
echo 
echo "=========================="
print_msg "title" "CHECK RESULTS"
echo "=========================="

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ] && [ -f "$VENV_DIR/bin/python" ]; then
    print_msg "success" "Virtual environment exists and appears to be working normally"
    
    # Check if project is installed as a package
    if "$VENV_DIR/bin/pip" show wpdocker &>/dev/null; then
        print_msg "success" "Project is installed as a package (wpdocker)"
    else
        print_msg "warning" "Project is not installed as a package"
        print_msg "recommend" "To install it, run: pip install -e \"$INSTALL_DIR\""
    fi
    
    print_msg "info" "If you still encounter issues running the application, try these steps:"
    print_msg "sub_label" "1. Delete the virtual environment: rm -rf $VENV_DIR"
    print_msg "sub_label" "2. Run init.sh script again to create a new virtual environment"
    print_msg "sub_label" "3. Ensure the project is installed as a package with: pip install -e \"$INSTALL_DIR\""
else
    print_msg "error" "Virtual environment is not working properly"
    print_msg "info" "Try these steps:"
    print_msg "sub_label" "1. Delete the virtual environment: rm -rf $VENV_DIR"
    print_msg "sub_label" "2. Reinstall python3-venv package: sudo apt install python3-venv python3-dev"
    print_msg "sub_label" "3. Run init.sh script again to create a new virtual environment"
fi
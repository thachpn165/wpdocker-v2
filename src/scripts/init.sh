#!/bin/bash

set -e

# Source message utils
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../bash/messages_utils.sh"

# Fixed path for the installation directory
FIXED_INSTALL_DIR="/opt/wp-docker"

# Actual path to the installation directory (used to create symlink if needed)
ACTUAL_INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Check and create symlink only if /opt/wp-docker does not exist
if [ ! -e "$FIXED_INSTALL_DIR" ]; then
    print_msg info "Directory $FIXED_INSTALL_DIR does not exist"
    print_msg info "Creating symlink $FIXED_INSTALL_DIR -> $ACTUAL_INSTALL_DIR"
    
    # Check if parent directory exists
    if [ ! -d "$(dirname "$FIXED_INSTALL_DIR")" ]; then
        print_msg info "Creating directory $(dirname "$FIXED_INSTALL_DIR")"
        mkdir -p "$(dirname "$FIXED_INSTALL_DIR")"
    fi
    
    # Create symlink
    ln -sf "$ACTUAL_INSTALL_DIR" "$FIXED_INSTALL_DIR"
    print_msg success "Symlink created successfully"
else
    print_msg success "Directory $FIXED_INSTALL_DIR already exists, continuing to use it"
fi

# Use the fixed path
INSTALL_DIR="$FIXED_INSTALL_DIR"
VENV_DIR="$INSTALL_DIR/.venv"
PYTHON_EXEC="$VENV_DIR/bin/python"
MAIN_FILE="$INSTALL_DIR/src/main.py"

# Check and create core.env from core.env.sample if needed
CORE_ENV="$INSTALL_DIR/core.env"
CORE_ENV_SAMPLE="$INSTALL_DIR/core.env.sample"

if [ ! -f "$CORE_ENV" ] && [ -f "$CORE_ENV_SAMPLE" ]; then
    print_msg info "Creating core.env from sample..."
    cp "$CORE_ENV_SAMPLE" "$CORE_ENV"
    print_msg success "Created core.env from sample template"
fi

# Check python3
source "$(dirname "${BASH_SOURCE[0]}")/install_python.sh"
install_python

# Initialize Python venv (in .venv directory)
source "$(dirname "${BASH_SOURCE[0]}")/init_python.sh"
init_python_env

# Run backend
print_msg run "Launching WP Docker..."

# Activate virtualenv in current shell
if [ -f "$VENV_DIR/bin/activate" ]; then
    print_msg info "Activating Python virtual environment in main shell..."
    source "$VENV_DIR/bin/activate"
else
    print_msg warning "Could not find activate file. Trying to continue without activating virtualenv..."
fi

# Check if src module can be imported
print_msg check "Checking if src module can be imported..."
if "$PYTHON_EXEC" -c "import src" 2>/dev/null; then
    print_msg success "src module is ready to use"
else
    print_msg warning "Cannot import src module, may need to install package"
    
    # Install package in development mode if not installed
    if [ -f "$INSTALL_DIR/setup.py" ]; then
        print_msg info "Installing project in development mode..."
        pip install -e "$INSTALL_DIR"
    fi
fi

# Run main program
cd "$INSTALL_DIR"  # Ensure current directory is the install directory
"$PYTHON_EXEC" "$MAIN_FILE"
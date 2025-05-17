#!/bin/bash

# Source message utils if not already sourced
if [ -z "$(type -t print_msg)" ] || [ "$(type -t print_msg)" != "function" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/../bash/messages_utils.sh"
fi

init_python_env() {
    # Create virtualenv if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        print_msg info "Creating Python virtual environment..."
        
        # Try standard venv creation first
        if ! python3 -m venv "$VENV_DIR" 2>/tmp/venv_error.log; then
            print_msg warning "Standard venv creation failed. Using fallback method..."
            
            # Check if the fallback helper script exists
            HELPER_SCRIPT="$(dirname "$0")/helpers/create_venv.py"
            if [ -f "$HELPER_SCRIPT" ] && [ -x "$HELPER_SCRIPT" ]; then
                print_msg info "Using helper script to create virtualenv..."
                python3 "$HELPER_SCRIPT" "$VENV_DIR"
            else
                print_msg error "Unable to create virtual environment. Please check Python installation."
                print_msg info "Error details:"
                cat /tmp/venv_error.log
                exit 1
            fi
        fi
        
        # Verify the virtualenv was created successfully
        if [ ! -f "$VENV_DIR/bin/activate" ]; then
            print_msg error "Virtual environment created but activate script is missing."
            print_msg info "Please check Python installation and try again."
            exit 1
        fi
    fi

    # Activate virtualenv and install necessary libraries
    print_msg info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    # PYTHONPATH is no longer needed since we're installing the package with pip install -e

    if [[ ! -f "$VENV_DIR/.installed" && -f "$INSTALL_DIR/requirements.txt" ]]; then
        print_msg info "Installing Python dependencies..."
        pip install --upgrade pip
        pip install -r "$INSTALL_DIR/requirements.txt"
        
        # Install current package in development mode
        print_msg info "Installing project as a development package..."
        pip install -e "$INSTALL_DIR"
        
        touch "$VENV_DIR/.installed"
    else
        # Check if package is already installed
        if ! pip show wpdocker &>/dev/null; then
            print_msg info "Installing project as a development package..."
            pip install -e "$INSTALL_DIR"
        else
            print_msg success "Python dependencies already installed."
        fi
    fi
}
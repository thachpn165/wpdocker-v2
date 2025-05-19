#!/bin/bash

# Source message utils if not already sourced
if [ -z "$(type -t print_msg)" ] || [ "$(type -t print_msg)" != "function" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/../bash/messages_utils.sh"
fi

init_python_env() {
    print_msg step "Setting up Python environment..."
    
    # Create virtualenv first (if it doesn't exist)
    if [[ ! -d "$VENV_DIR" ]]; then
        print_msg info "Creating Python virtual environment at $VENV_DIR..."
        
        # Try to create the virtualenv
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
                print_msg info "Try creating the virtualenv manually with: python3 -m venv $VENV_DIR"
                exit 1
            fi
        fi
        
        # Verify the virtualenv was created successfully
        if [ ! -f "$VENV_DIR/bin/activate" ]; then
            print_msg error "Virtual environment created but activate script is missing."
            print_msg info "Please check Python installation and try creating the virtualenv manually."
            exit 1
        fi
        
        print_msg success "Virtual environment created successfully at $VENV_DIR"
    else
        print_msg info "Using existing virtual environment at $VENV_DIR"
    fi

    # Activate virtualenv
    print_msg info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Verify activation was successful
    if [[ "$VIRTUAL_ENV" != "$VENV_DIR" ]]; then
        print_msg warning "Virtual environment activation may have failed. Proceeding anyway..."
    else
        print_msg success "Virtual environment activated successfully"
    fi

    # Ensure pip is up to date in the virtualenv
    print_msg info "Upgrading pip in virtualenv..."
    python -m pip install --upgrade pip

    # Install dependencies - always run this step to ensure all deps are installed
    print_msg info "Installing Python dependencies..."
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        # Install all requirements at once
        python -m pip install -r "$INSTALL_DIR/requirements.txt"
        
        # Install current package in development mode
        print_msg info "Installing project as a development package..."
        python -m pip install -e "$INSTALL_DIR"
        
        if [ ! -f "$VENV_DIR/.installed" ]; then
            touch "$VENV_DIR/.installed"
        fi
        print_msg success "Dependencies installed successfully"
    else
        print_msg error "Requirements file not found at $INSTALL_DIR/requirements.txt"
        return 1
    fi

    
    print_msg success "Python environment is ready"
    return 0
}
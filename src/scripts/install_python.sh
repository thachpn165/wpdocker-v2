#!/bin/bash

set -e

# Source message utils
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../bash/messages_utils.sh"

install_python_ubuntu() {
    print_msg info "Installing Python on Ubuntu/Debian..."
    apt update
    
    # Get Python version - we'll try multiple methods to ensure we get the right version
    # Try to get the exact version including minor version number
    if command -v python3 &>/dev/null; then
        PYTHON_FULL_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        PYTHON_VERSION=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f1,2)
        print_msg info "Detected active Python version: $PYTHON_FULL_VERSION"
    else
        # Fallback to apt-cache if Python isn't installed yet
        PYTHON_VERSION=$(apt-cache policy python3 | grep -oP 'Candidate: \K[0-9.]+' | cut -d. -f1,2)
        print_msg info "Detected available Python version from apt: $PYTHON_VERSION"
    fi
    
    # Install Python and essential packages
    print_msg info "Installing Python packages..."
    apt install -y python3 python3-pip
    
    # Check again the exact Python version after installation
    PYTHON_FULL_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_VERSION=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f1,2)
    PYTHON_MAJOR=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f2)
    PYTHON_PATCH=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f3)
    
    print_msg info "Confirmed Python version: $PYTHON_FULL_VERSION (Major.Minor: $PYTHON_VERSION)"
    
    # Install python3-full for PEP 668 environments (Ubuntu 22.04+, Debian 12+)
    print_msg info "Installing python3-full package..."
    apt install -y python3-full
    
    # Install exact version of python-venv if available
    print_msg info "Installing virtualenv packages for Python $PYTHON_FULL_VERSION..."
    
    # Try all these variations of the venv package
    # 1. Exact version with full version number (e.g., python3.11.4-venv)
    # 2. Major.Minor version (e.g., python3.11-venv)
    # 3. Just Major version (e.g., python3-venv)
    
    if apt-cache show python$PYTHON_FULL_VERSION-venv &>/dev/null; then
        print_msg info "Installing python$PYTHON_FULL_VERSION-venv"
        apt install -y python$PYTHON_FULL_VERSION-venv
    elif apt-cache show python$PYTHON_VERSION-venv &>/dev/null; then
        print_msg info "Installing python$PYTHON_VERSION-venv"
        apt install -y python$PYTHON_VERSION-venv
    elif apt-cache show python$PYTHON_MAJOR-venv &>/dev/null; then
        print_msg info "Installing python$PYTHON_MAJOR-venv"
        apt install -y python$PYTHON_MAJOR-venv
    elif apt-cache show python3-venv &>/dev/null; then
        print_msg info "Installing python3-venv"
        apt install -y python3-venv
    else
        print_msg warning "Could not find specific venv package, trying alternatives..."
        apt install -y python-venv || python3 -m pip install --user virtualenv
    fi
    
    # Extra safety: Check if python3-venv package exists to handle generic case
    if [ "$PYTHON_VERSION" != "3" ] && apt-cache show python3-venv &>/dev/null; then
        print_msg info "Also installing generic python3-venv package for compatibility"
        apt install -y python3-venv
    fi
    
    # Double check for the specific Python version's venv package using apt-cache search
    VENV_PACKAGE=$(apt-cache search python.*venv | grep -o "python$PYTHON_VERSION-venv\|python$PYTHON_MAJOR.$PYTHON_MINOR-venv" | head -1)
    if [ -n "$VENV_PACKAGE" ]; then
        print_msg info "Found specific venv package: $VENV_PACKAGE"
        apt install -y "$VENV_PACKAGE"
    fi
    
    # Install development headers (needed for some pip packages)
    print_msg info "Installing Python development packages..."
    if apt-cache show python$PYTHON_VERSION-dev &>/dev/null; then
        apt install -y python$PYTHON_VERSION-dev
    elif apt-cache show python3-dev &>/dev/null; then
        apt install -y python3-dev
    fi
    
    # Display confirmation of installed packages
    print_msg info "Installed Python packages:"
    dpkg -l | grep -E "python3|python-venv|python.*venv" | awk '{print $2}'
}

install_python_centos() {
    print_msg info "Installing Python on CentOS/AlmaLinux/RHEL..."
    
    # Check if it's RHEL 8+/CentOS 8+ with dnf
    if command -v dnf &>/dev/null; then
        dnf install -y python3 python3-pip python3-devel
        
        # Install virtualenv packages
        dnf install -y python3-virtualenv || pip3 install virtualenv
        
    # Fallback to yum for older versions
    elif command -v yum &>/dev/null; then
        yum install -y python3 python3-pip python3-devel
        
        # Install virtualenv packages
        yum install -y python3-virtualenv || pip3 install virtualenv
    fi
    
    # Make sure setuptools and wheel are installed
    pip3 install --upgrade pip setuptools wheel
}

install_python_macos() {
    print_msg info "Installing Python on macOS..."

    if ! command -v brew >/dev/null 2>&1; then
        print_msg error "Homebrew is not installed. Please install it first: https://brew.sh/"
        exit 1
    fi

    # Install Python using Homebrew
    brew install python
    
    # Ensure pip is up to date
    pip3 install --upgrade pip setuptools wheel virtualenv
}

# Check pip
check_pip() {
    print_msg step "Checking for pip installation..."
    
    # Check if pip is installed
    if python3 -m pip --version &>/dev/null; then
        print_msg success "Pip is installed: $(python3 -m pip --version)"
        
        # Check if it's an externally managed environment (PEP 668)
        if python3 -m pip install --dry-run --no-user setuptools 2>&1 | grep -q "externally-managed-environment"; then
            print_msg warning "Detected externally managed environment (PEP 668)"
            export EXTERNALLY_MANAGED=1
        else
            export EXTERNALLY_MANAGED=0
        fi
        
        return 0
    else
        print_msg warning "Pip is not installed or not in PATH"
        export EXTERNALLY_MANAGED=0
        return 1
    fi
}

# Install pip
install_pip() {
    print_msg step "Installing pip..."
    local os_name=""
    local os_id=""

    if [[ "$(uname)" == "Darwin" ]]; then
        os_name="macos"
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        os_id="${ID}"
        os_name="${ID_LIKE:-$ID}"
    fi

    case "$os_name" in
    macos)
        # On macOS, pip is usually installed with Python from Homebrew
        brew reinstall python
        ;;
    debian | ubuntu)
        print_msg info "Installing pip for Python on Ubuntu/Debian..."
        # Try to install python3-pip via apt
        apt update && apt install -y python3-pip
        
        # If not successful, try installing pip from getpip
        if ! python3 -m pip --version &>/dev/null; then
            print_msg info "Installing pip using get-pip.py..."
            wget -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            python3 /tmp/get-pip.py
            rm -f /tmp/get-pip.py
        fi
        ;;
    rhel | centos | fedora | almalinux)
        print_msg info "Installing pip for Python on RHEL/CentOS..."
        # Try to install python3-pip through dnf or yum
        if command -v dnf &>/dev/null; then
            dnf install -y python3-pip
        else
            yum install -y python3-pip
        fi
        
        # If not successful, try installing pip from getpip
        if ! python3 -m pip --version &>/dev/null; then
            print_msg info "Installing pip using get-pip.py..."
            curl -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            python3 /tmp/get-pip.py
            rm -f /tmp/get-pip.py
        fi
        ;;
    *)
        print_msg info "Installing pip using get-pip.py..."
        # Try to install pip using the generic method
        if command -v curl &>/dev/null; then
            curl -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
        elif command -v wget &>/dev/null; then
            wget -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
        else
            print_msg error "Neither curl nor wget is available. Cannot download get-pip.py"
            return 1
        fi
        
        python3 /tmp/get-pip.py
        rm -f /tmp/get-pip.py
        ;;
    esac

    # Check again
    if python3 -m pip --version &>/dev/null; then
        print_msg success "Pip installed successfully: $(python3 -m pip --version)"
        return 0
    else
        print_msg error "Failed to install pip"
        return 1
    fi
}

# Check virtualenv
check_virtualenv() {
    print_msg step "Checking for virtualenv support..."
    
    # Get the exact Python version
    PYTHON_FULL_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_VERSION=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f1,2)
    
    print_msg info "Checking venv support for Python $PYTHON_FULL_VERSION..."
    
    # Direct check for Python venv feature
    if python3 -m venv --help &>/dev/null; then
        print_msg success "Python venv module is available"
        
        # Check if ensurepip works by creating test venv
        print_msg info "Testing venv creation functionality..."
        TEST_VENV="/tmp/test_venv_$$"
        
        # Delete test directory if it exists
        if [ -d "$TEST_VENV" ]; then
            rm -rf "$TEST_VENV"
        fi
        
        # Try to create test venv - save log for debugging
        print_msg info "Running: python3 -m venv $TEST_VENV"
        if python3 -m venv "$TEST_VENV" 2>/tmp/venv_error.log; then
            if [ -f "$TEST_VENV/bin/activate" ]; then
                print_msg success "Python venv creation works correctly with activate script"
                rm -rf "$TEST_VENV"
                return 0
            else
                print_msg warning "venv created but missing bin/activate script"
                print_msg info "venv directory contents:"
                ls -la "$TEST_VENV"
                if [ -d "$TEST_VENV/bin" ]; then
                    print_msg info "bin directory contents:"
                    ls -la "$TEST_VENV/bin"
                fi
                rm -rf "$TEST_VENV"
                return 1
            fi
        else
            print_msg warning "Python venv creation failed - likely missing ensurepip support"
            print_msg info "Error output:"
            cat /tmp/venv_error.log
            rm -rf "$TEST_VENV"
            return 1
        fi
    # Check if virtualenv is installed
    elif python3 -m virtualenv --help &>/dev/null; then
        print_msg success "Virtualenv package is available"
        return 0
    # Check if virtualenv package is installed via pip
    elif python3 -m pip show virtualenv &>/dev/null; then
        print_msg success "Virtualenv package is installed via pip"
        return 0
    else
        print_msg warning "No virtualenv support found"
        
        # Additional diagnostic information for debugging
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            print_msg info "OS: $NAME $VERSION_ID"
        fi
        
        if command -v python3 &>/dev/null; then
            print_msg info "Python version: $(python3 --version 2>&1)"
            print_msg info "Python executable: $(which python3)"
            if [ -x /usr/bin/apt ]; then
                print_msg info "Available venv packages:"
                apt-cache search python.*venv | grep -v -e "^lib" -e "^python-" | grep -e "python3" -e "python$PYTHON_VERSION"
            fi
        fi
        
        return 1
    fi
}

# Install virtualenv by OS
install_virtualenv() {
    print_msg step "Installing virtualenv support..."
    local os_name=""
    local os_id=""

    # Get the exact Python version
    PYTHON_FULL_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_VERSION=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f1,2)
    PYTHON_MAJOR=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f2)
    PYTHON_PATCH=$(echo "$PYTHON_FULL_VERSION" | cut -d. -f3)
    
    print_msg info "Setting up virtualenv for Python $PYTHON_FULL_VERSION..."

    if [[ "$(uname)" == "Darwin" ]]; then
        os_name="macos"
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        os_id="${ID}"
        os_name="${ID_LIKE:-$ID}"
    fi

    case "$os_name" in
    macos)
        python3 -m pip install virtualenv
        ;;
    debian | ubuntu)
        # Try to find appropriate venv package for installed Python version
        print_msg info "Searching for appropriate venv packages..."
        
        # List available venv packages
        VENV_PACKAGES=$(apt-cache search python.*venv | grep -v -e "^lib" -e "^python-" | grep -e "python3" -e "python$PYTHON_VERSION")
        print_msg info "Available venv packages:\n$VENV_PACKAGES"
        
        # Install python3-full first
        if apt-cache show python3-full &>/dev/null; then
            print_msg info "Installing python3-full package..."
            apt install -y python3-full
        fi
        
        # Install virtualenv by priority
        print_msg info "Installing venv packages for Python $PYTHON_VERSION..."
        
        # 1. Exact version first
        if apt-cache show python$PYTHON_VERSION-venv &>/dev/null; then
            print_msg info "Installing python$PYTHON_VERSION-venv"
            apt install -y python$PYTHON_VERSION-venv
        else
            # 2. Search for compatible version
            EXACT_PACKAGE=$(apt-cache search "python$PYTHON_VERSION-venv" | head -1 | awk '{print $1}')
            if [ -n "$EXACT_PACKAGE" ]; then
                print_msg info "Found specific package: $EXACT_PACKAGE"
                apt install -y "$EXACT_PACKAGE"
            # 3. Install generic package
            elif apt-cache show python3-venv &>/dev/null; then
                print_msg info "Installing generic python3-venv"
                apt install -y python3-venv
            # 4. If none available, use pip
            else
                print_msg info "No system venv package found, using pip to install virtualenv"
                if [ "$EXTERNALLY_MANAGED" -eq 1 ]; then
                    python3 -m pip install --user virtualenv
                else
                    python3 -m pip install virtualenv
                fi
            fi
        fi
        
        # Install venv for specific Python to ensure proper operation
        print_msg info "Searching for version-specific venv packages..."
        
        # Try to find venv packages with exact version matches
        apt-cache search "^python.*-venv" 2>/dev/null
        PYTHON_SPECIFIC_VENV_PKGS=$(apt-cache search "^python.*-venv" 2>/dev/null | grep -E "$PYTHON_VERSION|$PYTHON_MAJOR\.$PYTHON_MINOR|$PYTHON_MAJOR-venv" | awk '{print $1}')
        
        if [ -n "$PYTHON_SPECIFIC_VENV_PKGS" ]; then
            print_msg info "Found version-specific venv packages:"
            echo "$PYTHON_SPECIFIC_VENV_PKGS"
            echo "$PYTHON_SPECIFIC_VENV_PKGS" | while read pkg; do
                print_msg info "Installing $pkg"
                apt install -y "$pkg"
            done
        else
            print_msg warning "No version-specific venv packages found, trying generic packages"
            apt install -y python3-venv python3-virtualenv
        fi
        
        # Ensure ensurepip is available - This is crucial for venv to work properly
        if apt-cache show python3-venv &>/dev/null; then
            print_msg info "Installing python3-venv"
            apt install -y python3-venv
        fi
        
        # Some distros need python3-ensurepip package specifically
        if apt-cache show python3-ensurepip &>/dev/null; then
            print_msg info "Installing python3-ensurepip"
            apt install -y python3-ensurepip
        fi
        
        # Install development headers
        print_msg info "Installing Python development packages..."
        DEV_PACKAGE=$(apt-cache search "^python.*-dev" | grep "$PYTHON_VERSION\|$PYTHON_MAJOR\.$PYTHON_MINOR" | head -1 | awk '{print $1}')
        if [ -n "$DEV_PACKAGE" ]; then
            print_msg info "Installing $DEV_PACKAGE"
            apt install -y "$DEV_PACKAGE"
        else
            apt install -y python3-dev
        fi
        
        # Report installed packages
        print_msg info "Installed virtualenv packages:"
        dpkg -l | grep -E "python.*venv|virtualenv" | awk '{print $2}'
        ;;
    rhel | centos | fedora | almalinux)
        print_msg info "Installing virtualenv packages for RHEL/CentOS..."
        if command -v dnf &>/dev/null; then
            dnf install -y python3-virtualenv python3-devel
            if ! python3 -m venv --help &>/dev/null; then
                print_msg info "Using pip to install virtualenv"
                python3 -m pip install virtualenv
            fi
        else
            yum install -y python3-virtualenv python3-devel
            if ! python3 -m venv --help &>/dev/null; then
                print_msg info "Using pip to install virtualenv"
                python3 -m pip install virtualenv
            fi
        fi
        ;;
    *)
        print_msg info "Attempting to install virtualenv using pip..."
        if [ "$EXTERNALLY_MANAGED" -eq 1 ]; then
            python3 -m pip install --user virtualenv
        else
            python3 -m pip install virtualenv
        fi
        ;;
    esac

    # Verify installation and try creating test venv
    if python3 -m venv --help &>/dev/null; then
        print_msg success "Python venv module installed successfully"
        
        # Test if venv creation actually works
        TEST_VENV="/tmp/test_venv_after_install_$$"
        if [ -d "$TEST_VENV" ]; then
            rm -rf "$TEST_VENV"
        fi
        
        print_msg info "Testing venv creation after installation..."
        if python3 -m venv "$TEST_VENV" 2>/tmp/venv_test_error.log; then
            if [ -f "$TEST_VENV/bin/activate" ]; then
                print_msg success "venv creation successful with activate script present"
                rm -rf "$TEST_VENV"
                return 0
            else
                print_msg warning "venv created but missing bin/activate script"
                print_msg info "Contents of venv directory:"
                ls -la "$TEST_VENV"
                if [ -d "$TEST_VENV/bin" ]; then
                    ls -la "$TEST_VENV/bin"
                fi
            fi
        else
            print_msg warning "venv creation failed after installation"
            print_msg info "Error output:"
            cat /tmp/venv_test_error.log
        fi
        rm -rf "$TEST_VENV" 2>/dev/null
        
        # Try alternate methods if venv still doesn't work properly
        if [ "$os_name" = "debian" ] || [ "$os_name" = "ubuntu" ]; then
            print_msg info "Trying pip-based virtualenv as fallback..."
            # Try to reinstall distutils and ensurepip directly
            if apt-cache show python3-distutils &>/dev/null; then
                apt install -y python3-distutils
            fi
            
            # Final fallback - use pip-installed virtualenv
            if ! check_virtualenv; then
                python3 -m pip install --user virtualenv
            fi
        fi
    elif python3 -m virtualenv --help &>/dev/null; then
        print_msg success "Virtualenv installed successfully"
        return 0
    elif python3 -m pip show virtualenv &>/dev/null; then
        print_msg success "Virtualenv package installed successfully (via pip)"
        return 0
    else
        # Try reinstalling with pip if all above methods failed
        print_msg warning "System package installation failed, trying pip installation as fallback..."
        
        # Handle externally managed environment
        if [ "$EXTERNALLY_MANAGED" -eq 1 ]; then
            # With PEP 668 environment, use --user
            print_msg info "Using --user flag due to externally managed environment"
            python3 -m pip install --user virtualenv
        else
            # Normal environment
            python3 -m pip install virtualenv
        fi
        
        if python3 -m pip show virtualenv &>/dev/null; then
            print_msg success "Virtualenv installed successfully via pip fallback"
            return 0
        else
            print_msg error "Failed to install virtualenv support"
            return 1
        fi
    fi
}

install_python() {
    if command -v python3 &>/dev/null; then
        print_msg success "Python3 is already installed: $(python3 --version)"
        # Check python3 version
        python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [[ "$(echo "$python_version < 3.0" | bc)" -eq 1 ]]; then
            print_msg error "Python version is too old: $python_version. Python >= 3.0 is required."
            exit 1
        fi
    else
        print_msg step "Python3 is not installed. Attempting to install..."

        local os_name=""
        local os_id=""

        if [[ "$(uname)" == "Darwin" ]]; then
            os_name="macos"
        elif [[ -f /etc/os-release ]]; then
            . /etc/os-release
            os_id="${ID}"
            os_name="${ID_LIKE:-$ID}"
        fi

        case "$os_name" in
        macos)
            install_python_macos
            ;;
        debian | ubuntu)
            install_python_ubuntu
            ;;
        rhel | centos | fedora | almalinux)
            install_python_centos
            ;;
        *)
            print_msg error "Unsupported OS: $os_name. Please install Python 3 manually."
            exit 1
            ;;
        esac

        if command -v python3 &>/dev/null; then
            print_msg success "Python3 installed successfully: $(python3 --version)"
        else
            print_msg error "Python installation failed. Please install it manually."
            exit 1
        fi
    fi
    
    # Check pip
    if ! check_pip; then
        print_msg warning "Python pip is missing. Attempting to install..."
        if ! install_pip; then
            print_msg error "Failed to install pip. Please install it manually."
            print_msg info "Ubuntu/Debian: apt install python3-pip"
            print_msg info "RHEL/CentOS: dnf/yum install python3-pip"
            print_msg info "Or you can install pip using get-pip.py: https://pip.pypa.io/en/stable/installation/"
            exit 1
        fi
    fi
    
    # Ensure pip, setuptools and wheel are updated, if not an externally managed environment
    if [ "$EXTERNALLY_MANAGED" -eq 0 ]; then
        print_msg step "Updating pip, setuptools and wheel..."
        python3 -m pip install --upgrade pip setuptools wheel
    else
        print_msg warning "Skipping global pip packages update due to externally managed environment (PEP 668)"
        print_msg info "Will use a virtual environment for package installation"
    fi
    
    # Check virtualenv support
    if ! check_virtualenv; then
        print_msg warning "Python virtualenv support missing. Attempting to install..."
        if ! install_virtualenv; then
            print_msg warning "Standard virtualenv installation failed. Trying fallback methods..."
            
            # Ultimate fallback - generate a venv helper script
            if [[ "$(uname)" == "Darwin" ]]; then
                os_name="macos"
            elif [[ -f /etc/os-release ]]; then
                . /etc/os-release
                os_id="${ID}"
                os_name="${ID_LIKE:-$ID}"
            fi
            
            if [ "$os_name" = "debian" ] || [ "$os_name" = "ubuntu" ]; then
                print_msg info "Creating a virtualenv helper script as final fallback..."
                
                # Create a helper script to create virtualenvs that works around common issues
                cat > /tmp/create_venv.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import subprocess
import site
import sysconfig

def create_venv(venv_path):
    print(f"Creating virtual environment at: {venv_path}")
    
    # Try different methods in order of preference
    methods = [
        lambda: subprocess.run([sys.executable, "-m", "venv", venv_path]),
        lambda: subprocess.run([sys.executable, "-m", "virtualenv", venv_path]),
        lambda: manual_create_venv(venv_path)
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(os.path.join(venv_path, "bin", "activate")):
                print(f"Successfully created virtual environment at {venv_path}")
                return True
        except Exception as e:
            print(f"Method failed with error: {e}")
    
    return False

def manual_create_venv(venv_path):
    # Manual creation of minimal virtualenv structure
    print("Attempting manual virtualenv creation...")
    
    if not os.path.exists(venv_path):
        os.makedirs(venv_path)
    
    bin_dir = os.path.join(venv_path, "bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    
    # Create basic activate script
    with open(os.path.join(bin_dir, "activate"), "w") as f:
        f.write(f'''
# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

deactivate () {{
    unset -f pydoc >/dev/null 2>&1
    unset -f deactivate
    unset VIRTUAL_ENV
    if [ ! "${{1:-}}" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}}

# unset irrelevant variables
deactivate nondestructive

VIRTUAL_ENV="{venv_path}"
export VIRTUAL_ENV

PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH

if [ -z "${{PYTHONHOME:-}}" ] ; then
    PYTHONHOME="${{PYTHONHOME:-}}"
    export PYTHONHOME
    unset PYTHONHOME
fi

if [ -z "${{PYTHONNOUSERSITE:-}}" ] ; then
    export PYTHONNOUSERSITE=1
fi
''')
    
    # Create python symlink
    os.symlink(sys.executable, os.path.join(bin_dir, "python"))
    os.symlink(sys.executable, os.path.join(bin_dir, "python3"))
    
    # Create pip script
    with open(os.path.join(bin_dir, "pip"), "w") as f:
        f.write(f'''
#!/bin/sh
"{sys.executable}" -m pip "$@"
''')
    os.chmod(os.path.join(bin_dir, "pip"), 0o755)
    
    with open(os.path.join(bin_dir, "pip3"), "w") as f:
        f.write(f'''
#!/bin/sh
"{sys.executable}" -m pip "$@"
''')
    os.chmod(os.path.join(bin_dir, "pip3"), 0o755)
    
    # Return success
    return subprocess.CompletedProcess(args=[], returncode=0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <venv_path>")
        sys.exit(1)
    
    venv_path = sys.argv[1]
    success = create_venv(venv_path)
    
    if success:
        sys.exit(0)
    else:
        print(f"Failed to create virtual environment at {venv_path}")
        sys.exit(1)
EOF
                
                # Make it executable
                chmod +x /tmp/create_venv.py
                
                print_msg info "Testing custom virtualenv creation script..."
                TEST_VENV="/tmp/fallback_venv_$$"
                if [ -d "$TEST_VENV" ]; then
                    rm -rf "$TEST_VENV"
                fi
                
                if python3 /tmp/create_venv.py "$TEST_VENV" && [ -f "$TEST_VENV/bin/activate" ]; then
                    print_msg success "Fallback virtualenv creation successful!"
                    print_msg info "Using custom virtualenv script for future venv creation"
                    # Copy the script to a permanent location
                    mkdir -p "$(dirname "$0")/helpers"
                    cp /tmp/create_venv.py "$(dirname "$0")/helpers/create_venv.py"
                    chmod +x "$(dirname "$0")/helpers/create_venv.py"
                    rm -rf "$TEST_VENV"
                    print_msg info "You can create virtual environments using: python3 $(dirname "$0")/helpers/create_venv.py /path/to/venv"
                else
                    print_msg error "All virtualenv creation methods failed. Please install virtualenv support manually."
                    print_msg info "Ubuntu/Debian: apt install python3-venv python3-distutils python3-ensurepip"
                    print_msg info "RHEL/CentOS: dnf/yum install python3-virtualenv" 
                    print_msg info "macOS: pip3 install virtualenv"
                    exit 1
                fi
            else
                print_msg error "Failed to install virtualenv support. Please install it manually."
                print_msg info "Ubuntu/Debian: apt install python3-venv"
                print_msg info "RHEL/CentOS: dnf/yum install python3-virtualenv" 
                print_msg info "macOS: pip3 install virtualenv"
                exit 1
            fi
        fi
    fi
    
    print_msg success "Python environment is ready"
}
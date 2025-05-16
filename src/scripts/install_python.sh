#!/bin/bash

set -e

print_msg() {
    local type="$1"
    local msg="$2"
    case "$type" in
    step) echo -e "\033[1;34m🔹 $msg\033[0m" ;;
    info) echo -e "\033[1;36mℹ️  $msg\033[0m" ;;
    success) echo -e "\033[1;32m✅ $msg\033[0m" ;;
    warning) echo -e "\033[1;33m⚠️  $msg\033[0m" ;;
    error) echo -e "\033[1;31m$msg\033[0m" ;;
    esac
}

install_python_ubuntu() {
    print_msg info "Installing Python on Ubuntu/Debian..."
    apt update
    
    # Get Python version
    PYTHON_VERSION=$(apt-cache policy python3 | grep -oP 'Candidate: \K[0-9.]+' | cut -d. -f1,2)
    print_msg info "Detected Python version: $PYTHON_VERSION"
    
    # Install Python and essential packages
    apt install -y python3 python3-pip
    
    # Install virtualenv packages based on Python version
    if apt-cache show python$PYTHON_VERSION-venv &>/dev/null; then
        apt install -y python$PYTHON_VERSION-venv
    elif apt-cache show python3-venv &>/dev/null; then
        apt install -y python3-venv
    else
        apt install -y python3-venv || apt install -y python-venv || pip3 install virtualenv
    fi
    
    # Install development headers (needed for some pip packages)
    apt install -y python3-dev
    
    # Make sure setuptools and wheel are installed
    pip3 install --upgrade pip setuptools wheel
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

# Kiểm tra pip
check_pip() {
    print_msg step "Checking for pip installation..."
    
    # Kiểm tra pip đã cài đặt chưa
    if python3 -m pip --version &>/dev/null; then
        print_msg success "Pip is installed: $(python3 -m pip --version)"
        return 0
    else
        print_msg warning "Pip is not installed or not in PATH"
        return 1
    fi
}

# Cài đặt pip
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
        # Trên macOS, pip thường được cài đặt cùng với Python từ Homebrew
        brew reinstall python
        ;;
    debian | ubuntu)
        print_msg info "Installing pip for Python on Ubuntu/Debian..."
        # Thử cài đặt python3-pip qua apt
        apt update && apt install -y python3-pip
        
        # Nếu không thành công, thử cài đặt pip từ getpip
        if ! python3 -m pip --version &>/dev/null; then
            print_msg info "Installing pip using get-pip.py..."
            wget -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            python3 /tmp/get-pip.py
            rm -f /tmp/get-pip.py
        fi
        ;;
    rhel | centos | fedora | almalinux)
        print_msg info "Installing pip for Python on RHEL/CentOS..."
        # Thử cài đặt python3-pip thông qua dnf hoặc yum
        if command -v dnf &>/dev/null; then
            dnf install -y python3-pip
        else
            yum install -y python3-pip
        fi
        
        # Nếu không thành công, thử cài đặt pip từ getpip
        if ! python3 -m pip --version &>/dev/null; then
            print_msg info "Installing pip using get-pip.py..."
            curl -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            python3 /tmp/get-pip.py
            rm -f /tmp/get-pip.py
        fi
        ;;
    *)
        print_msg info "Installing pip using get-pip.py..."
        # Thử cài đặt pip bằng phương pháp generic
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

    # Kiểm tra lại
    if python3 -m pip --version &>/dev/null; then
        print_msg success "Pip installed successfully: $(python3 -m pip --version)"
        return 0
    else
        print_msg error "Failed to install pip"
        return 1
    fi
}

# Kiểm tra virtualenv
check_virtualenv() {
    print_msg step "Checking for virtualenv support..."
    
    # Kiểm tra trực tiếp tính năng venv của Python
    if python3 -m venv --help &>/dev/null; then
        print_msg success "Python virtualenv support is available"
        return 0
    else
        print_msg warning "Python virtualenv support is not available"
        return 1
    fi
}

# Cài đặt virtualenv theo hệ điều hành
install_virtualenv() {
    print_msg step "Installing virtualenv support..."
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
        python3 -m pip install virtualenv
        ;;
    debian | ubuntu)
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        print_msg info "Installing virtualenv packages for Python $PYTHON_VERSION on Ubuntu/Debian..."
        
        # Thử cài đặt gói venv cụ thể cho phiên bản trước
        if apt-cache show python$PYTHON_VERSION-venv &>/dev/null; then
            apt install -y python$PYTHON_VERSION-venv
        elif apt-cache show python3-venv &>/dev/null; then
            apt install -y python3-venv
        else
            # Fallback to pip if system packages not available
            print_msg info "System packages not available, attempting to install virtualenv via pip..."
            python3 -m pip install virtualenv
        fi
        
        # Cài đặt python3-dev nếu cần
        if ! apt-cache show python$PYTHON_VERSION-dev &>/dev/null || ! apt-cache show python3-dev &>/dev/null; then
            print_msg info "Installing Python development headers..."
            apt install -y python$PYTHON_VERSION-dev || apt install -y python3-dev
        fi
        ;;
    rhel | centos | fedora | almalinux)
        print_msg info "Installing virtualenv packages for RHEL/CentOS..."
        if command -v dnf &>/dev/null; then
            dnf install -y python3-virtualenv python3-devel || python3 -m pip install virtualenv
        else
            yum install -y python3-virtualenv python3-devel || python3 -m pip install virtualenv
        fi
        ;;
    *)
        print_msg info "Attempting to install virtualenv using pip..."
        python3 -m pip install virtualenv
        ;;
    esac

    # Kiểm tra lại cài đặt
    if python3 -m venv --help &>/dev/null; then
        print_msg success "Python venv module installed successfully"
        return 0
    elif python3 -m virtualenv --help &>/dev/null; then
        print_msg success "Virtualenv installed successfully"
        return 0
    elif python3 -m pip show virtualenv &>/dev/null; then
        print_msg success "Virtualenv package installed successfully (via pip)"
        return 0
    else
        # Thử cài đặt lại bằng pip nếu các phương pháp trên đều không thành công
        print_msg warning "System package installation failed, trying pip installation as fallback..."
        python3 -m pip install virtualenv
        
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
    
    # Kiểm tra pip
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
    
    # Đảm bảo pip, setuptools và wheel được cập nhật
    print_msg step "Updating pip, setuptools and wheel..."
    python3 -m pip install --upgrade pip setuptools wheel
    
    # Kiểm tra hỗ trợ virtualenv
    if ! check_virtualenv; then
        print_msg warning "Python virtualenv support missing. Attempting to install..."
        if ! install_virtualenv; then
            print_msg error "Failed to install virtualenv support. Please install it manually."
            print_msg info "Ubuntu/Debian: apt install python3-venv"
            print_msg info "RHEL/CentOS: dnf/yum install python3-virtualenv" 
            print_msg info "macOS: pip3 install virtualenv"
            exit 1
        fi
    fi
    
    print_msg success "Python environment is ready"
}

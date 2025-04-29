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
    apt install -y python3 python3-venv python3-pip
}

install_python_centos() {
    print_msg info "Installing Python on CentOS/AlmaLinux/RHEL..."
    dnf install -y python3 python3-pip
}

install_python_macos() {
    print_msg info "Installing Python on macOS..."

    if ! command -v brew >/dev/null 2>&1; then
        print_msg error "Homebrew is not installed. Please install it first: https://brew.sh/"
        exit 1
    fi

    brew install python
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
        return
    fi

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
}

#!/bin/bash
# WP Docker Auto-Installer Script
# Automatically downloads and installs the chosen release channel
# Supports stable and nightly channels

set -e

# Define colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base repository info
REPO_OWNER="thachpn165"  # Update this to your actual GitHub username
REPO_NAME="wpdocker-v2"
GITHUB_API="https://api.github.com"
INSTALL_DIR="$HOME/wpdocker-v2"

# Temporary directory for downloads
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Function to print messages
print_msg() {
    local type=$1
    local message=$2
    
    case $type in
        "info")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        *)
            echo -e "$message"
            ;;
    esac
}

# Check if required commands are available
check_requirements() {
    local missing_requirements=false
    
    for cmd in curl unzip python3 git; do
        if ! command -v $cmd &> /dev/null; then
            print_msg "error" "$cmd is required but not installed."
            missing_requirements=true
        fi
    done
    
    if $missing_requirements; then
        print_msg "error" "Please install the missing requirements and try again."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 --version | cut -d ' ' -f 2)
    if [[ $(echo $python_version | cut -d '.' -f 1) -lt 3 || ($(echo $python_version | cut -d '.' -f 1) -eq 3 && $(echo $python_version | cut -d '.' -f 2) -lt 6) ]]; then
        print_msg "error" "Python 3.6 or higher is required. You have $python_version."
        exit 1
    fi
    
    print_msg "success" "All requirements satisfied."
}

# Function to select installation channel
select_channel() {
    echo -e "\n${BLUE}=== Select Installation Channel ===${NC}"
    echo "1) Stable (recommended for production)"
    echo "2) Nightly (latest development version)"
    
    while true; do
        read -p "Enter your choice [1-2]: " choice
        case $choice in
            1)
                echo "stable"
                return
                ;;
            2)
                echo "nightly"
                return
                ;;
            *)
                print_msg "error" "Invalid selection. Please try again."
                ;;
        esac
    done
}

# Function to get latest release for a channel
get_release_info() {
    local channel=$1
    
    if [[ "$channel" == "stable" ]]; then
        # Get latest stable release
        curl -s "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
    else
        # Get nightly release (tag="nightly")
        curl -s "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases/tags/nightly"
    fi
}

# Function to download appropriate release asset
download_release() {
    local channel=$1
    local release_info=$2
    local download_url=""
    
    if [[ "$channel" == "stable" ]]; then
        # Find the .zip asset from the stable release
        download_url=$(echo "$release_info" | grep -o '"browser_download_url": "[^"]*\.zip"' | head -1 | cut -d '"' -f 4)
    else
        # Get the fixed-name nightly zip
        download_url="https://github.com/$REPO_OWNER/$REPO_NAME/releases/download/nightly/wpdocker-nightly-latest.zip"
    fi
    
    if [[ -z "$download_url" ]]; then
        print_msg "error" "Could not find download URL for the selected channel."
        exit 1
    fi
    
    # Get release version
    if [[ "$channel" == "stable" ]]; then
        release_version=$(echo "$release_info" | grep -o '"tag_name": "[^"]*"' | head -1 | cut -d '"' -f 4)
    else
        # For nightly, we'll extract date from the release name
        release_date=$(echo "$release_info" | grep -o '"name": "[^"]*"' | head -1 | cut -d '"' -f 4 | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}')
        release_version="nightly-$release_date"
    fi
    
    local zip_file="$TMP_DIR/wpdocker.zip"
    
    print_msg "info" "Downloading $channel release ($release_version)..."
    curl -L "$download_url" -o "$zip_file"
    
    if [[ ! -f "$zip_file" ]]; then
        print_msg "error" "Download failed."
        exit 1
    fi
    
    print_msg "success" "Download complete."
    
    # Return file path and version
    echo "$zip_file:$release_version:$channel"
}

# Function to extract and install WP Docker
install_wpdocker() {
    local info=$1
    local zip_file=$(echo "$info" | cut -d ':' -f 1)
    local version=$(echo "$info" | cut -d ':' -f 2)
    local channel=$(echo "$info" | cut -d ':' -f 3)
    
    print_msg "info" "Installing WP Docker v2 ($version)..."
    
    # Create installation directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
    
    # Extract the zip file
    unzip -o "$zip_file" -d "$INSTALL_DIR"
    
    # Navigate to installation directory
    cd "$INSTALL_DIR"
    
    # Run the installer script
    print_msg "info" "Running installer..."
    bash installers/install.sh
    
    # Update config with selected channel
    print_msg "info" "Updating configuration with selected channel..."
    config_dir="$INSTALL_DIR/data/config"
    mkdir -p "$config_dir"
    
    # Activate virtual environment if exists
    if [[ -d "$INSTALL_DIR/.venv" ]]; then
        source "$INSTALL_DIR/.venv/bin/activate"
    fi
    
    # Use Python to update channel in config.json
    python3 -c "
import json
import os

config_file = '$config_dir/config.json'
channel = '$channel'

# Create or load config
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}
else:
    config = {}

# Update core section if it exists, otherwise create it
if 'core' not in config:
    config['core'] = {}

# Set channel
config['core']['channel'] = channel

# Save config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=4)

print(f'Updated config.json with channel: {channel}')
"
    
    print_msg "success" "WP Docker v2 ($version) has been installed successfully!"
    print_msg "info" "To start WP Docker, run:"
    echo -e "${GREEN}cd \"$INSTALL_DIR\" && ./wpdocker.sh${NC}"
    
    # Create a symlink to make it easier to run
    if [[ "$HOME/bin" != "" && -d "$HOME/bin" ]]; then
        print_msg "info" "Creating symlink in ~/bin for easier access..."
        ln -sf "$INSTALL_DIR/wpdocker.sh" "$HOME/bin/wpdocker"
        print_msg "success" "Symlink created. You can now run 'wpdocker' from anywhere."
    fi
}

# Main function
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   WP Docker v2 Automated Installer    ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check requirements
    check_requirements
    
    # Select channel
    channel=$(select_channel)
    print_msg "info" "Selected channel: $channel"
    
    # Get release info
    print_msg "info" "Fetching release information..."
    release_info=$(get_release_info "$channel")
    
    if [[ -z "$release_info" || "$release_info" == *"Not Found"* ]]; then
        print_msg "error" "Could not fetch release information."
        exit 1
    fi
    
    # Download release
    download_info=$(download_release "$channel" "$release_info")
    
    # Install WP Docker
    install_wpdocker "$download_info"
}

# Run main function
main
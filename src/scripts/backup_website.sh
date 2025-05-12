#!/bin/bash

# Script to create a backup of a website using the BackupManager
# Usage: backup_website.sh website_name [--provider provider_name]

# Load environment variables and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASH_UTILS_DIR="$INSTALL_DIR/src/bash"
source "$BASH_UTILS_DIR/get_path.sh" 2>/dev/null || true
source "$BASH_UTILS_DIR/load_config.sh" 2>/dev/null || true
source "$BASH_UTILS_DIR/messages_utils.sh" 2>/dev/null || true

# Default values
PROVIDER="local"

# Parse command line arguments
WEBSITE_NAME="$1"
shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if website name is provided
if [ -z "$WEBSITE_NAME" ]; then
    error "Usage: backup_website.sh website_name [--provider provider_name]"
    exit 1
fi

info "Creating backup for website $WEBSITE_NAME using provider $PROVIDER"

# Activate the Python virtual environment if it exists
if [ -f "${VENV_PATH}/bin/activate" ]; then
    source "${VENV_PATH}/bin/activate"
else
    warn "Virtual environment not found at ${VENV_PATH}"
fi

# Set the PYTHONPATH
export PYTHONPATH="${INSTALL_DIR}"

# Run the backup using BackupManager - updated to use new structure
python -c "
from src.features.backup.backup_manager import BackupManager;
manager = BackupManager();
success, result = manager.create_backup('${WEBSITE_NAME}', '${PROVIDER}');
print(result);
exit(0 if success else 1)
"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    success "Backup for $WEBSITE_NAME created successfully using provider $PROVIDER"
else
    error "Failed to create backup for $WEBSITE_NAME"
fi

exit $EXIT_CODE
#!/bin/bash

# This script creates a backup of a website and then uploads it to a remote storage using Rclone
# Usage: backup_to_remote.sh website_name remote_name

# Load environment variables and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASH_UTILS_DIR="$INSTALL_DIR/src/bash"
source "$BASH_UTILS_DIR/get_path.sh"
source "$BASH_UTILS_DIR/load_config.sh"
source "$BASH_UTILS_DIR/messages_utils.sh"

# Check arguments
if [ $# -lt 2 ]; then
    error "Usage: backup_to_remote.sh website_name remote_name"
    exit 1
fi

WEBSITE_NAME="$1"
REMOTE_NAME="$2"

# Create a timestamp for the backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${WEBSITE_NAME}_${TIMESTAMP}.tar.gz"
# Create the full backup path in host system (this will be converted to container path in the Python code)
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Create the backup
info "Creating backup of ${WEBSITE_NAME}..."
"$SCRIPTS_DIR/backup_website.sh" "$WEBSITE_NAME" "$BACKUP_NAME"

if [ $? -ne 0 ]; then
    error "Failed to create backup of ${WEBSITE_NAME}"
    exit 1
fi

# Activate the Python virtual environment
if [ -f "${VENV_PATH}/bin/activate" ]; then
    source "${VENV_PATH}/bin/activate"
else
    error "Virtual environment not found at ${VENV_PATH}"
    exit 1
fi

# Set the PYTHONPATH
export PYTHONPATH="${INSTALL_DIR}"

# Upload the backup to the remote - updated to use new structure
info "Uploading backup to ${REMOTE_NAME}..."
python -c "
from src.features.rclone.backup_integration import RcloneBackupIntegration;
integration = RcloneBackupIntegration();
success, message = integration.backup_to_remote('${REMOTE_NAME}', '${WEBSITE_NAME}', '${BACKUP_PATH}');
print(message);
exit(0 if success else 1)
"

UPLOAD_RESULT=$?
if [ $UPLOAD_RESULT -eq 0 ]; then
    success "Backup successfully uploaded to ${REMOTE_NAME}"
else
    error "Failed to upload backup to ${REMOTE_NAME}"
    exit 1
fi

exit 0
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

# Validate inputs
if [ -z "$WEBSITE_NAME" ]; then
    error "Website name cannot be empty"
    exit 1
fi

if [ -z "$REMOTE_NAME" ]; then
    error "Remote name cannot be empty"
    exit 1
fi

# Determine the correct backup directory
if [ -z "$BACKUP_DIR" ]; then
    # Use domain-specific backup path if BACKUP_DIR is not set
    if [ -n "$SITES_DIR" ] && [ -d "$SITES_DIR" ]; then
        SITE_BACKUP_DIR="${SITES_DIR}/${WEBSITE_NAME}/backups"
        
        # Create the directory if it doesn't exist
        if [ ! -d "$SITE_BACKUP_DIR" ]; then
            mkdir -p "$SITE_BACKUP_DIR"
            if [ $? -ne 0 ]; then
                error "Failed to create backup directory: ${SITE_BACKUP_DIR}"
                exit 1
            fi
        fi
        
        BACKUP_DIR="$SITE_BACKUP_DIR"
        info "Using site-specific backup directory: ${BACKUP_DIR}"
    else
        # Fallback to a temp directory if SITES_DIR is not set
        BACKUP_DIR="/tmp/wp_docker_backups/${WEBSITE_NAME}"
        mkdir -p "$BACKUP_DIR"
        if [ $? -ne 0 ]; then
            error "Failed to create temporary backup directory: ${BACKUP_DIR}"
            exit 1
        fi
        warn "SITES_DIR not set, using temporary directory: ${BACKUP_DIR}"
    fi
else
    # Ensure BACKUP_DIR exists
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        if [ $? -ne 0 ]; then
            error "Failed to create backup directory: ${BACKUP_DIR}"
            exit 1
        fi
    fi
    
    info "Using configured backup directory: ${BACKUP_DIR}"
fi

# Create a timestamp for the backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${WEBSITE_NAME}_${TIMESTAMP}.tar.gz"
# Create the full backup path in host system (this will be converted to container path in the Python code)
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Create the backup
info "Creating backup of ${WEBSITE_NAME}..."
"$INSTALL_DIR/src/scripts/backup_website.sh" "$WEBSITE_NAME" "$BACKUP_NAME"

BACKUP_RESULT=$?
if [ $BACKUP_RESULT -ne 0 ]; then
    error "Failed to create backup of ${WEBSITE_NAME}"
    exit 1
fi

# Verify the backup file exists
if [ ! -f "$BACKUP_PATH" ]; then
    error "Backup file not found at: ${BACKUP_PATH}"
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

# Upload the backup to the remote
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
    
    # Optionally clean up the backup file after successful upload
    # Uncomment the following lines if you want to remove local backups after cloud upload
    # info "Cleaning up local backup file..."
    # rm -f "${BACKUP_PATH}"
    # if [ $? -eq 0 ]; then
    #     info "Local backup file removed"
    # else
    #     warn "Failed to remove local backup file: ${BACKUP_PATH}"
    # fi
else
    error "Failed to upload backup to ${REMOTE_NAME}"
    error "Local backup file remains at: ${BACKUP_PATH}"
    exit 1
fi

exit 0
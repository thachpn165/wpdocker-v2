#!/bin/bash
# File: scripts/cron/run_cron_jobs.sh
# Script to execute cron jobs in the virtual environment.

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Set environment variables
export WP_DOCKER_HOME="$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"
export PATH="$PROJECT_ROOT/bin:$PATH"

# Python virtual environment
VENV_DIR="$PROJECT_ROOT/.venv"

# Create logs directory
LOG_DIR="$PROJECT_ROOT/logs/cron"
mkdir -p "$LOG_DIR"

# Create log filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/cron_$TIMESTAMP.log"

# Job ID if provided
JOB_ID="$1"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Write header to log
log "===== STARTING CRON JOB EXECUTION ====="
log "Project directory: $PROJECT_ROOT"

# If a specific Job ID is provided, add to log
if [ -n "$JOB_ID" ]; then
    log "Job ID: $JOB_ID"
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    log "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Check for virtual environment
if [ ! -d "$VENV_DIR" ]; then
    log "❌ Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Activate virtual environment
log "Activating Python virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    log "❌ Failed to activate virtual environment"
    exit 1
fi

# Check if new structure exists
if [ -f "$PROJECT_ROOT/src/features/cron/cli.py" ]; then
    CLI_PATH="$PROJECT_ROOT/src/features/cron/cli.py"
elif [ -f "$PROJECT_ROOT/core/backend/modules/cron/cli.py" ]; then
    # Fallback to old structure if new structure not found
    CLI_PATH="$PROJECT_ROOT/core/backend/modules/cron/cli.py"
else
    log "❌ Could not find cron CLI script in either new or old structure"
    exit 1
fi

# Command to execute
CMD="$CLI_PATH run"

# If a Job ID parameter is provided, add it to the command
if [ -n "$JOB_ID" ]; then
    CMD="$CMD --job-id $JOB_ID"
fi

# Make CLI script executable if needed
chmod +x "$CLI_PATH"

# Log Python and environment information
log "Python version: $(python3 --version)"
log "PYTHONPATH: $PYTHONPATH"
log "Virtual env: $VIRTUAL_ENV"

# Execute command
log "Executing command: $CMD"
python3 $CMD >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# Check result
if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Execution completed successfully."
else
    log "❌ Error executing cron job. Exit code: $EXIT_CODE"
fi

# Deactivate virtual environment
deactivate

# Write footer to log
log "===== CRON JOB EXECUTION COMPLETE ====="

# Limit number of log files (keep 100 most recent)
find "$LOG_DIR" -name "cron_*.log" -type f | sort -r | tail -n +101 | xargs -r rm

exit $EXIT_CODE
#!/bin/bash
# Upgrade script for WP Docker v2
# This script upgrades an existing installation

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

echo "================================================================="
echo "          WP Docker v2 Upgrade Script                            "
echo "================================================================="

# Check for Python virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Using virtual environment: $VIRTUAL_ENV"
else
    echo "Python virtual environment not found. Creating a new one..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Virtual environment created and activated."
fi

# Backup existing configuration
echo "Backing up configuration..."
CONFIG_DIR="data/config"
if [ -d "$CONFIG_DIR" ]; then
    BACKUP_FILE="wpdocker_config_backup_$(date +%Y%m%d_%H%M%S).zip"
    zip -r "$BACKUP_FILE" "$CONFIG_DIR"
    echo "Configuration backed up to $BACKUP_FILE"
fi

# Determine upgrade method
UPGRADE_METHOD="wheel"
if [ ! -f "pyproject.toml" ]; then
    echo "pyproject.toml not found, using legacy upgrade method."
    UPGRADE_METHOD="legacy"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Upgrade the package
if [ "$UPGRADE_METHOD" == "wheel" ]; then
    echo "Upgrading using modern Python package method..."
    pip install -e . --upgrade
else
    echo "Upgrading using legacy method..."
    pip install -r requirements.txt --upgrade
fi

# Run migration if available
echo "Running migrations..."
if python -c "import src.core.migration.migrator; print('Migration module exists')" 2>/dev/null; then
    python -c "from src.core.migration.migrator import Migrator; Migrator().run_migrations()"
    echo "Migrations completed."
else
    echo "No migration module found. Skipping migrations."
fi

echo "================================================================="
echo "Upgrade completed successfully!"
echo "To start WP Docker, run: source .venv/bin/activate && python src/main.py"
echo "================================================================="
@echo off
:: Upgrade script for WP Docker v2 on Windows
:: This script upgrades an existing installation

echo =================================================================
echo           WP Docker v2 Upgrade Script                           
echo =================================================================

:: Check for Python virtual environment
if exist .venv (
    call .venv\Scripts\activate.bat
    echo Using virtual environment: %VIRTUAL_ENV%
) else (
    echo Python virtual environment not found. Creating a new one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Virtual environment created and activated.
)

:: Backup existing configuration
echo Backing up configuration...
set CONFIG_DIR=data\config
if exist %CONFIG_DIR% (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
    set BACKUP_FILE=wpdocker_config_backup_%mydate%_%mytime%.zip
    powershell -Command "Compress-Archive -Path '%CONFIG_DIR%' -DestinationPath '%BACKUP_FILE%'"
    echo Configuration backed up to %BACKUP_FILE%
)

:: Determine upgrade method
set UPGRADE_METHOD=wheel
if not exist pyproject.toml (
    echo pyproject.toml not found, using legacy upgrade method.
    set UPGRADE_METHOD=legacy
)

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Upgrade the package
if "%UPGRADE_METHOD%"=="wheel" (
    echo Upgrading using modern Python package method...
    python -m pip install -e . --upgrade
) else (
    echo Upgrading using legacy method...
    python -m pip install -r requirements.txt --upgrade
)

:: Run migration if available
echo Running migrations...
python -c "import src.core.migration.migrator; print('Migration module exists')" 2>nul
if %ERRORLEVEL% equ 0 (
    python -c "from src.core.migration.migrator import Migrator; Migrator().run_migrations()"
    echo Migrations completed.
) else (
    echo No migration module found. Skipping migrations.
)

echo =================================================================
echo Upgrade completed successfully!
echo To start WP Docker, run: .venv\Scripts\activate.bat ^&^& python src\main.py
echo =================================================================

pause
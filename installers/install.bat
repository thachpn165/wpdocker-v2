@echo off
:: Installer script for WP Docker v2 on Windows
:: This script installs the package and sets up the environment

echo =================================================================
echo           WP Docker v2 Installation Script                      
echo =================================================================

:: Check for Python 3.6+
echo Checking for Python 3.6+...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python 3.6+ is required but not found. Please install Python 3.6 or higher.
    exit /b 1
)

:: Verify Python version
python --version
if %ERRORLEVEL% neq 0 (
    echo Failed to run Python. Please ensure Python 3.6+ is installed and in your PATH.
    exit /b 1
)

:: Determine installation method
set INSTALL_METHOD=wheel
if not exist pyproject.toml (
    echo pyproject.toml not found, using legacy installation method.
    set INSTALL_METHOD=legacy
)

:: Create virtual environment
echo Creating Python virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install the package
if "%INSTALL_METHOD%"=="wheel" (
    echo Installing using modern Python package method...
    python -m pip install -e .
) else (
    echo Installing using legacy method...
    python -m pip install -r requirements.txt
)

:: Finalize installation
echo Creating config directories...
if not exist data\config mkdir data\config

:: Initial configuration
echo Performing initial configuration...
python -c "from src.common.utils.version_helper import initialize_version_info; initialize_version_info()"

echo =================================================================
echo Installation completed successfully!
echo To start WP Docker, run: .venv\Scripts\activate.bat ^&^& python src\main.py
echo =================================================================

pause
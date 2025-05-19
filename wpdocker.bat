@echo off
:: Startup script for WP Docker v2 on Windows
:: This script activates the virtual environment and starts the application

:: Check for virtual environment
if not exist .venv (
    echo Virtual environment not found. Running installation script first...
    call installers\install.bat
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Run the application
python src\main.py %*
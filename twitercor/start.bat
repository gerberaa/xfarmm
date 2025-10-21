@echo off
echo 🚀 Twitter/X Automation System
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\twscrape" (
    echo 📥 Installing dependencies...
    pip install -r requirements_full.txt
)

REM Check if config exists
if not exist ".env" (
    if exist "config.env" (
        echo 📋 Copying config template...
        copy config.env .env
        echo ⚠️ Please edit .env file with your settings before running the bot
    )
)

REM Run the main script
echo ✅ Starting automation system...
echo.
python main.py

pause
@echo off
:: PID Annotator - Easy Launch Script with Virtual Environment
:: This script automatically creates a virtual environment and starts the application

echo ========================================
echo    PID Annotator - Starting...
echo ========================================
echo.

:: Check if Python is installed - try both 'python' and 'py' commands
set PYTHON_CMD=
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
) else (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
%PYTHON_CMD% --version
echo.

:: Check if virtual environment exists
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    echo This is a one-time setup and may take a minute...
    echo.
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo Try running: %PYTHON_CMD% -m pip install --upgrade pip
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
) else (
    echo [OK] Virtual environment found
    echo.
)

:: Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo Try deleting the venv folder and running this script again
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

:: Note: After venv activation, 'python' command always works regardless of system setup
:: Check if dependencies are installed
echo [SETUP] Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    echo This may take a few minutes on first run...
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt --no-warn-script-location
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        echo Troubleshooting:
        echo 1. Check your internet connection
        echo 2. Try deleting the venv folder and run this script again
        echo 3. Make sure you have administrator privileges
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed successfully
) else (
    echo [OK] Core dependencies found
    echo [SETUP] Ensuring all dependencies are up to date...
    python -m pip install -r requirements.txt --no-warn-script-location --quiet
    if errorlevel 1 (
        echo [WARNING] Some dependencies may not have been updated
    )
)

echo.
echo ========================================
echo Starting PID Annotator on port 5001...
echo ========================================
echo.
echo The application will open in your browser automatically.
echo.
echo To stop the server, press Ctrl+C in this window.
echo.
echo ========================================
echo.

:: Start browser in background after 3 seconds
start "" cmd /c "timeout /t 3 /nobreak >nul 2>&1 && start http://localhost:5001"

:: Start the Flask application
python app.py

:: If the application exits, pause so user can see any error messages
echo.
echo ========================================
echo Application stopped
echo ========================================
echo.
pause

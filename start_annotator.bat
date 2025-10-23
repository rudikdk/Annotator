@echo off
:: PID Annotator - Easy Launch Script
:: This script starts the PID Annotator web application

echo ========================================
echo    PID Annotator - Starting...
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

:: Check if required packages are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Flask not found. Installing dependencies...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependencies are installed
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

:: Wait a moment then open browser
start "" timeout /t 2 /nobreak >nul 2>&1 && start http://localhost:5001

:: Start the Flask application
python app.py

:: If the application exits, pause so user can see any error messages
echo.
echo ========================================
echo Application stopped
echo ========================================
pause

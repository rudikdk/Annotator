@echo off
:: PID Annotator - Python 3.13 Compatibility Fix
:: This script fixes eventlet compatibility issues with Python 3.13

echo ========================================
echo    PID Annotator - Python 3.13 Fix
echo ========================================
echo.
echo This script will:
echo 1. Uninstall eventlet (not compatible with Python 3.13)
echo 2. Reinstall dependencies for threading mode
echo.
echo ========================================
echo.

:: Uninstall eventlet if present
echo Uninstalling eventlet...
python -m pip uninstall -y eventlet
echo.

:: Reinstall dependencies
echo Installing/updating dependencies...
python -m pip install -r requirements.txt
echo.

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Fix applied successfully!
echo ========================================
echo.
echo You can now run start_annotator.bat
echo.
pause

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

:: Check for Microsoft Visual C++ Redistributable
echo [CHECK] Checking for Microsoft Visual C++ Redistributable...
set VCREDIST_FOUND=0

:: Check for VC++ 2015-2022 Redistributable (x64) - the most common modern version
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if not errorlevel 1 set VCREDIST_FOUND=1

:: Check for VC++ 2015-2022 Redistributable (x86) as fallback
if "%VCREDIST_FOUND%"=="0" (
    reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86" /v Version >nul 2>&1
    if not errorlevel 1 set VCREDIST_FOUND=1
)

:: Check for older VC++ 2013 (x64)
if "%VCREDIST_FOUND%"=="0" (
    reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\12.0\VC\Runtimes\x64" /v Version >nul 2>&1
    if not errorlevel 1 set VCREDIST_FOUND=1
)

if "%VCREDIST_FOUND%"=="0" (
    echo.
    echo [WARNING] Microsoft Visual C++ Redistributable not found!
    echo This is required for some Python packages to work correctly.
    echo.
    echo Do you want to download and install it now? (Y/N)
    set /p INSTALL_VCREDIST=

    if /i "%INSTALL_VCREDIST%"=="Y" (
        echo.
        echo [SETUP] Downloading Microsoft Visual C++ Redistributable...
        echo Please wait, this may take a moment...
        echo.

        :: Download the latest VC++ 2015-2022 Redistributable (x64)
        set VCREDIST_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe
        set VCREDIST_FILE=%TEMP%\vc_redist.x64.exe

        :: Use PowerShell to download the file
        powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%VCREDIST_URL%' -OutFile '%VCREDIST_FILE%'}"

        if errorlevel 1 (
            echo [ERROR] Failed to download VC++ Redistributable
            echo Please download it manually from:
            echo https://aka.ms/vs/17/release/vc_redist.x64.exe
            echo.
            pause
            exit /b 1
        )

        echo [SETUP] Installing Microsoft Visual C++ Redistributable...
        echo Please follow the installation wizard...
        echo.

        :: Install silently with /quiet /norestart, or use /install for GUI
        "%VCREDIST_FILE%" /install /quiet /norestart

        if errorlevel 1 (
            echo [WARNING] Installation may have failed or requires restart
            echo If problems persist, try installing manually from:
            echo %VCREDIST_FILE%
            echo.
            pause
        ) else (
            echo [OK] Microsoft Visual C++ Redistributable installed successfully
            echo.

            :: Clean up the installer
            del "%VCREDIST_FILE%" >nul 2>&1
        )
    ) else (
        echo.
        echo [WARNING] Continuing without VC++ Redistributable
        echo Some features may not work correctly. If you encounter errors,
        echo please download and install it from:
        echo https://aka.ms/vs/17/release/vc_redist.x64.exe
        echo.
        pause
    )
) else (
    echo [OK] Microsoft Visual C++ Redistributable found
    echo.
)

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

@echo off
REM Phantasmagoric Manuscriptum - Dependency Installation Script (Windows)
REM This script installs all required Python dependencies for the application

title PHANTASMAGORIC MANUSCRIPTUM - Dependency Installer (Windows)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  PHANTASMAGORIC MANUSCRIPTUM - Dependency Installer       ║
echo ║  Windows Version                                          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Error: Python is not installed or not in PATH.
    echo.
    echo    Please install Python 3.7 or higher from https://www.python.org/
    echo    Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python %PYTHON_VERSION% detected
echo.

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo [!] Error: pip is not installed.
    echo.
    echo    Please reinstall Python and ensure pip is selected during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
echo [✓] pip %PIP_VERSION% detected
echo.

echo Installing dependencies...
echo.

REM Install required packages
setlocal enabledelayedexpansion

set "packages=pyfiglet tqdm rich"

for %%p in (%packages%) do (
    echo [→] Installing %%p...
    pip install %%p
    if errorlevel 1 (
        echo [!] Failed to install %%p
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Installation Complete!                                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo You can now run the application:
echo   python Phantasmagoric-Manuscriptum.py 
echo.
pause

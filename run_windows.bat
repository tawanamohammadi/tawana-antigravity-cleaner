@echo off
TITLE Antigravity Cleaner
CLS

echo ==================================================
echo       Antigravity Cleaner - Windows Launcher
echo ==================================================
echo.
:: Ensure we are in the script's directory
cd /d "%~dp0"


:: Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from https://python.org or the Microsoft Store.
    pause
    exit /b
)

:: install requirements
if exist "src\requirements.txt" (
    echo Checking dependencies...
    python -m pip install --user -r src\requirements.txt

)

:: Run script
python src\main.py

pause

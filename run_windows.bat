@echo off
TITLE Antigravity Cleaner
CLS

echo ==================================================
echo       Antigravity Cleaner - Windows Launcher
echo ==================================================
echo.

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
    pip install -r src\requirements.txt >nul 2>&1
)

:: Run script
python src\main.py

pause

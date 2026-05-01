@echo off
chcp 65001 >nul
echo ========================================
echo TaikoMini - Simplified Taiko Game
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found!
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/2] Installing dependencies...
pip install -q pygame
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [2/2] Starting game...
echo.
python TaikoMini.py

if errorlevel 1 (
    echo.
    echo Game exited with error
    pause
)

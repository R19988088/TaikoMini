@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "REPO=R19988088/TaikoMini"

where gh >nul 2>nul
if errorlevel 1 (
    echo Error: GitHub CLI ^(gh^) not found.
    echo Install: winget install --id GitHub.cli
    echo Then login: gh auth login
    pause
    exit /b 1
)

gh auth status >nul 2>nul
if errorlevel 1 (
    echo Please login first:
    echo gh auth login
    pause
    exit /b 1
)

echo Latest runs:
gh run list --repo %REPO% --limit 5

echo.
echo Failed log from latest run:
gh run view --repo %REPO% --log-failed

echo.
echo If needed, download artifacts/logs with:
echo gh run download --repo %REPO%
pause

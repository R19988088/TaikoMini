@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "REMOTE_URL=https://github.com/R19988088/TaikoMini.git"
set "BRANCH=main"
set "STAGE=%TEMP%\taikomini_push_stage_%RANDOM%%RANDOM%"

where git >nul 2>nul
if errorlevel 1 (
    echo Error: git not found. Please install Git first.
    pause
    exit /b 1
)

if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"

echo [1/5] Copying project without songs...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$src=(Resolve-Path '%~dp0').Path; $dst='%STAGE%'; $exclude=@('.git','songs','.buildozer','bin','__pycache__'); Get-ChildItem -LiteralPath $src -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $dst -Recurse -Force }; Get-ChildItem -LiteralPath $dst -Recurse -Force -Filter *.pyc | Remove-Item -Force"
if errorlevel 1 (
    echo Error: copy failed.
    pause
    exit /b 1
)

cd /d "%STAGE%"

echo [2/5] Creating clean git history...
git init
if errorlevel 1 goto git_failed
git checkout -b %BRANCH%
if errorlevel 1 goto git_failed
git config core.autocrlf false

echo [3/5] Committing files...
git add -A
if errorlevel 1 goto git_failed
git commit -m "Replace TaikoMini Android build source"
if errorlevel 1 goto git_failed

echo [4/5] Connecting remote...
git remote add origin "%REMOTE_URL%"
if errorlevel 1 goto git_failed

echo [5/5] Force pushing. This clears existing GitHub %BRANCH% contents...
git push --force origin %BRANCH%
if errorlevel 1 goto git_failed

echo.
echo Done. GitHub Actions will build the APK on GitHub.
echo Open: https://github.com/R19988088/TaikoMini/actions
cd /d "%~dp0"
rmdir /s /q "%STAGE%"
pause
exit /b 0

:git_failed
echo.
echo Error: git command failed. Check login/permissions for %REMOTE_URL%.
echo Staged repo kept at: %STAGE%
pause
exit /b 1

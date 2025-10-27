@echo off
chcp 65001 >nul
echo =========================================
echo GitHub Repository Cleanup
echo =========================================
echo.

echo This will clean up the repository structure.
echo.
pause

echo.
echo Creating backup...
git add .
git commit -m "Backup before cleanup"
if errorlevel 1 (
    echo No changes to commit
)

echo.
echo Creating backup branch...
git checkout -b backup-before-cleanup
git push origin backup-before-cleanup
git checkout main

echo.
echo Moving files...

:: Move lib directory
if exist "lib" (
    echo Removing old lib...
    rmdir /s /q lib
)
if exist "216 github\lib" (
    echo Moving lib...
    move "216 github\lib" lib
)

:: Move main files
if exist "216 github\main.py" move "216 github\main.py" main.py
if exist "216 github\buildozer.spec" move "216 github\buildozer.spec" buildozer.spec
if exist "216 github\android_manifest.xml" move "216 github\android_manifest.xml" android_manifest.xml
if exist "216 github\requirements.txt" move "216 github\requirements.txt" requirements.txt

:: Move markdown files
if exist "216 github\README.md" move "216 github\README.md" README.md
if exist "216 github\QUICK_START.md" move "216 github\QUICK_START.md" QUICK_START.md
if exist "216 github\BUILD_GUIDE.md" move "216 github\BUILD_GUIDE.md" BUILD_GUIDE.md
if exist "216 github\DEBUG_GUIDE.md" move "216 github\DEBUG_GUIDE.md" DEBUG_GUIDE.md
if exist "216 github\FIX_SUMMARY.md" move "216 github\FIX_SUMMARY.md" FIX_SUMMARY.md
if exist "216 github\RESTRUCTURE_PLAN.md" move "216 github\RESTRUCTURE_PLAN.md" RESTRUCTURE_PLAN.md

:: Move other files
if exist "216 github\test_android_compatibility.py" move "216 github\test_android_compatibility.py" test_android_compatibility.py
if exist "216 github\parse_tja.py" move "216 github\parse_tja.py" parse_tja.py
if exist "216 github\TaikoMini.py" move "216 github\TaikoMini.py" TaikoMini.py
if exist "216 github\run.bat" move "216 github\run.bat" run.bat

:: Move directories
if exist "res" (
    echo Removing old res...
    rmdir /s /q res
)
if exist "216 github\res" (
    echo Moving res...
    move "216 github\res" res
)

if exist "taikomini" (
    echo Removing old taikomini...
    rmdir /s /q taikomini
)
if exist "216 github\taikomini" (
    echo Moving taikomini...
    move "216 github\taikomini" taikomini
)

echo.
echo Removing 216 github directory...
if exist "216 github" rmdir /s /q "216 github"

echo.
echo =========================================
echo Cleanup Complete!
echo =========================================
echo.
echo Next steps:
echo   1. Check status: git status
echo   2. Commit changes: git add . ^&^& git commit -m "Clean up repository structure"
echo   3. Push to GitHub: git push origin main
echo.
pause


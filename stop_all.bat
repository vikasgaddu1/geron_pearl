@echo off
REM PEARL Full Stack Stopper
REM Stops backend and React frontend servers, kills ALL Python processes, clears cache

echo ========================================
echo   PEARL Full Stack Stopper
echo ========================================
echo.

setlocal enabledelayedexpansion

echo [1/5] Stopping Backend Server...
call "%~dp0stop_backend.bat"

echo.
echo [2/5] Stopping React Frontend Server...
call "%~dp0stop_react_frontend.bat"

echo.
echo [3/5] Killing ALL remaining Python processes...
REM Kill ALL Python processes to ensure no orphaned processes remain
REM This is more aggressive but ensures a clean slate
powershell -Command "Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
powershell -Command "Get-Process py* -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -like 'py*'} | Stop-Process -Force -ErrorAction SilentlyContinue"
echo All Python processes terminated.

echo.
echo [4/5] Clearing Python cache (__pycache__ and .pyc files)...
REM Clear cache from entire backend directory
powershell -Command "Get-ChildItem -Path '%~dp0backend' -Recurse -Filter '*.pyc' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue"
powershell -Command "Get-ChildItem -Path '%~dp0backend' -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
REM Also clear .pytest_cache if exists
powershell -Command "Get-ChildItem -Path '%~dp0backend' -Recurse -Directory -Filter '.pytest_cache' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
echo Python cache cleared.

echo.
echo [5/5] Cleaning up temp files...
del /Q "%~dp0tmpclaude-*-cwd" 2>nul
echo Temp files cleaned.

echo.
echo ========================================
echo   All PEARL servers have been stopped
echo   Python cache has been cleared
echo ========================================
echo.
echo NOTE: If you still have issues after restart,
echo       close this terminal and open a new one.
echo.
echo TIP: To reset the Quick Start wizard, clear localStorage in your browser:
echo      1. Open DevTools (F12)
echo      2. Go to Application ^> Local Storage
echo      3. Delete 'pearl-onboarding-completed' key

timeout /t 5 >nul



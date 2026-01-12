@echo off
REM PEARL Full Stack Stopper
REM Stops backend and React frontend servers

echo ========================================
echo   PEARL Full Stack Stopper
echo ========================================
echo.

setlocal enabledelayedexpansion

echo Stopping Backend Server...
call "%~dp0stop_backend.bat"

echo.
echo Stopping React Frontend Server...
call "%~dp0stop_react_frontend.bat"

echo.
echo Clearing Python cache...
REM Clear cache from entire backend directory (not just app subfolder)
powershell -Command "Get-ChildItem -Path '%~dp0backend' -Recurse -Filter '*.pyc' -ErrorAction SilentlyContinue | Remove-Item -Force"
powershell -Command "Get-ChildItem -Path '%~dp0backend' -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force"
echo Python cache cleared.

echo.
echo Cleaning up temp files...
del /Q "%~dp0tmpclaude-*-cwd" 2>nul
echo Temp files cleaned.

echo.
echo ========================================
echo   All PEARL servers have been stopped
echo ========================================

timeout /t 3 >nul



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
echo ========================================
echo   All PEARL servers have been stopped
echo ========================================

timeout /t 3 >nul



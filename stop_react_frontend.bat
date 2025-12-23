@echo off
REM PEARL React Frontend Stopper - Kills Vite dev server on port 3000

echo ========================================
echo   Stopping PEARL React Frontend
echo ========================================
echo.

setlocal enabledelayedexpansion

REM Find and kill process using port 3000
set "found=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    set "found=1"
    echo Found process on port 3000: PID %%a
    taskkill /F /PID %%a >nul 2>&1
    echo Stopped process %%a
)

if "!found!"=="0" (
    echo No process found on port 3000
)

echo.
echo React frontend server stopped.
timeout /t 2 >nul



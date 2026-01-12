@echo off
REM PEARL Backend Stopper - Kills FastAPI/Uvicorn processes on port 8000

echo ========================================
echo   Stopping PEARL Backend Server
echo ========================================
echo.

setlocal enabledelayedexpansion

REM Find and kill process using port 8000
set "found=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    set "found=1"
    echo Found process on port 8000: PID %%a
    taskkill /F /PID %%a >nul 2>&1
    echo Stopped process %%a
)

if "!found!"=="0" (
    echo No process found on port 8000
)

REM Also try to kill any uvicorn processes
taskkill /F /IM uvicorn.exe >nul 2>&1

REM Kill any Python processes running from the backend directory
REM This catches zombie processes that may not be listening on port 8000
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%backend%%run.py%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo Found backend Python process: PID %%a
    taskkill /F /PID %%a >nul 2>&1
    echo Stopped process %%a
)

echo.
echo Backend server stopped.
timeout /t 2 >nul











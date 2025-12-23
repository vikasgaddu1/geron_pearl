@echo off
REM PEARL Frontend Stopper - Kills R Shiny processes on port 3838

echo ========================================
echo   Stopping PEARL Frontend Server
echo ========================================
echo.

setlocal enabledelayedexpansion

REM Find and kill process using port 3838
set "found=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3838 ^| findstr LISTENING 2^>nul') do (
    set "found=1"
    echo Found process on port 3838: PID %%a
    taskkill /F /PID %%a >nul 2>&1
    echo Stopped process %%a
)

if "!found!"=="0" (
    echo No process found on port 3838
)

REM Also try to kill any R processes (be careful - only kills rsession)
taskkill /F /IM rsession.exe >nul 2>&1

echo.
echo Frontend server stopped.
timeout /t 2 >nul


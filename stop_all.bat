@echo off
REM PEARL Full Stack Stopper
REM Stops backend, R Shiny frontend, and React frontends

echo ========================================
echo   PEARL Full Stack Stopper
echo ========================================
echo.

setlocal enabledelayedexpansion

echo Stopping Backend Server...
call "%~dp0stop_backend.bat"

echo.
echo Stopping R Shiny Frontend Server...
call "%~dp0stop_frontend.bat"

echo.
echo Stopping React Frontend Servers...
echo ----------------------------------------

REM Stop React frontends on ports 3000, 3001, 3002
for %%p in (3000 3001 3002) do (
    set "found=0"
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p ^| findstr LISTENING 2^>nul') do (
        set "found=1"
        echo Found process on port %%p: PID %%a
        taskkill /F /PID %%a >nul 2>&1
        echo Stopped process %%a
    )
    if "!found!"=="0" (
        echo No process found on port %%p
    )
)

echo.
echo ========================================
echo   All PEARL servers have been stopped
echo ========================================

timeout /t 3 >nul



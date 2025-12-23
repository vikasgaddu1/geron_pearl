@echo off
REM PEARL Backend Starter - FastAPI Server
REM Starts the FastAPI backend on port 8000

echo ========================================
echo   PEARL Backend Server (FastAPI)
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Starting FastAPI backend on http://localhost:8000 ...
echo Press Ctrl+C to stop the server
echo.

python run.py

pause


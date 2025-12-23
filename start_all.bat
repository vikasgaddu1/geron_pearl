@echo off
REM PEARL Full Stack Starter
REM Starts both backend (FastAPI) and frontend (React) servers

echo ========================================
echo   PEARL Full Stack Starter
echo ========================================
echo.

REM Start backend in a new window
echo Starting Backend Server (FastAPI on port 8000)...
start "PEARL Backend" cmd /k "%~dp0start_backend.bat"

REM Wait a moment for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 >nul

REM Start frontend in a new window
echo Starting Frontend Server (React on port 5173)...
start "PEARL React Frontend" cmd /k "%~dp0start_react_frontend.bat"

echo.
echo ========================================
echo   Both servers are starting...
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo   Close the server windows to stop them,
echo   or run stop_all.bat
echo ========================================

timeout /t 3 >nul

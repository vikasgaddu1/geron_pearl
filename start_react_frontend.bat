@echo off
REM PEARL React Frontend Starter - Vite Dev Server
REM Starts the React frontend on port 3000

echo ========================================
echo   PEARL React Frontend (Vite)
echo ========================================
echo.

cd /d "%~dp0react-frontend"

REM Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies...
    npm install
    echo.
)

echo Starting React frontend on http://localhost:3000 ...
echo Make sure the backend is running on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause



@echo off
REM PEARL Frontend Starter - R Shiny Server
REM Starts the R Shiny frontend on port 3838

echo ========================================
echo   PEARL Frontend Server (R Shiny)
echo ========================================
echo.

cd /d "%~dp0admin-frontend"

REM Check if renv is activated
if exist "renv\activate.R" (
    echo Using renv environment...
)

echo Starting R Shiny frontend on http://localhost:3838 ...
echo Make sure the backend is running on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Try Rscript first, fall back to R
where Rscript >nul 2>nul
if %errorlevel% equ 0 (
    Rscript run_app.R
) else (
    R --vanilla -f run_app.R
)

pause


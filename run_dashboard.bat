@echo off
rem CloudRouteAI — Windows Dashboard Launcher

echo ==================================================
echo   CloudRouteAI — Phase 5 Dashboard
echo ==================================================

if exist "%~dp0venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%~dp0venv\Scripts\activate.bat"
) else (
    if exist "%~dp0.venv\Scripts\activate.bat" (
        echo Activating virtual environment...
        call "%~dp0.venv\Scripts\activate.bat"
    )
)

echo Starting the interactive dashboard...
echo Press Ctrl+C to stop.
echo ==================================================

python "%~dp0run_dashboard.py"

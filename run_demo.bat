@echo off
REM KULIMA OS Pilot Demo - Windows Batch Script
REM ============================================
REM This script runs the KULIMA OS pilot demonstration on Windows.
REM No external dependencies required - just Python 3.

echo.
echo ========================================================================
echo   KULIMA OS PILOT DEMONSTRATION
echo   Coordination-First Infrastructure Planning
echo ========================================================================
echo.
echo Starting demo...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python 3 from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo Using Python:
python --version
echo.

REM Run the demo
echo Running KULIMA OS pilot demo...
echo.
python kulima_pilot_demo.py

REM Check if demo ran successfully
if %errorlevel% neq 0 (
    echo.
    echo ========================================================================
    echo   ERROR: Demo failed to run
    echo ========================================================================
    echo.
    echo Troubleshooting:
    echo 1. Make sure you're in the correct folder (should contain kulima_pilot_demo.py)
    echo 2. Check that all Python files are present
    echo 3. See RUN_DEMO.md for detailed instructions
    echo.
    pause
    exit /b 1
)

REM Success message
echo.
echo ========================================================================
echo   DEMO COMPLETED SUCCESSFULLY
echo ========================================================================
echo.
echo Generated files:
echo   - demand_signal_prospectus.json (machine-readable)
echo   - demand_signal_prospectus.md (human-readable)
echo.
echo Next steps:
echo   1. Open demand_signal_prospectus.md to see the results
echo   2. Read AGENTS.md to understand system invariants
echo   3. Explore the Python source code
echo.
echo For detailed instructions, see RUN_DEMO.md
echo.
pause

@REM Made with Bob

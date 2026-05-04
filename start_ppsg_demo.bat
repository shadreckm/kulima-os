@echo off
REM ============================================================================
REM PPSG Live Demo Launcher (Windows)
REM ============================================================================
REM 
REM Purpose: One-click startup for the Privacy-Preserving Signal Gateway
REM Status: Canonical Demo for Reviewers & Judges
REM 
REM This launcher starts the PPSG reference implementation gateway.
REM It demonstrates architectural refusal of PII, Zero-PII enforcement,
REM and Temporal Moat protection without requiring manual commands.

echo.
echo ========================================================================
echo PPSG Live Demo - Privacy-Preserving Signal Gateway
echo ========================================================================
echo.
echo Status: CANONICAL DEMO FOR REVIEWERS AND JUDGES
echo Version: ppsg-reference-v1.0
echo.
echo This demo proves what the system REFUSES to do, not just what it can do.
echo.
echo ========================================================================
echo.

REM Check if we're in the correct directory
if not exist "ppsg\gateway.py" (
    echo ERROR: Cannot find ppsg/gateway.py
    echo Please run this script from the kulima-os-hackathon directory.
    echo.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
echo.

REM Check if FastAPI is installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing PPSG dependencies...
    cd ppsg
    pip install -r requirements.txt --quiet
    cd ..
    echo Dependencies installed.
    echo.
) else (
    echo Dependencies OK.
    echo.
)

echo [2/3] Starting PPSG Gateway...
echo.
echo The gateway will start on http://localhost:8000
echo.
echo ========================================================================
echo DEMO INSTRUCTIONS:
echo ========================================================================
echo.
echo 1. Open your browser to: http://localhost:8000/docs
echo    (Swagger UI will load automatically)
echo.
echo 2. Try these demonstrations:
echo.
echo    A. VALID SIGNAL (should accept):
echo       POST /signal/submit
echo       {
echo         "activity_type": "irrigation",
echo         "time_window": "morning",
echo         "zone_id": "zone_a",
echo         "signal_source_type": "human"
echo       }
echo.
echo    B. PII REJECTION (should reject GPS coordinates):
echo       POST /signal/submit
echo       {
echo         "activity_type": "irrigation",
echo         "time_window": "morning",
echo         "zone_id": "-1.286389,36.817223",
echo         "signal_source_type": "human"
echo       }
echo.
echo    C. EXTRA FIELD REJECTION (should reject):
echo       POST /signal/submit
echo       {
echo         "activity_type": "irrigation",
echo         "time_window": "morning",
echo         "zone_id": "zone_a",
echo         "signal_source_type": "human",
echo         "user_id": "user123"
echo       }
echo.
echo 3. Check GET /health for operational metrics (no sensitive data)
echo.
echo 4. Check GET /zones for approved zone whitelist
echo.
echo ========================================================================
echo.
echo Press CTRL+C to stop the gateway when done.
echo.
echo ========================================================================
echo.

echo [3/3] Gateway starting...
echo.

REM Start the PPSG gateway
cd ppsg
python -m gateway

REM If we get here, the gateway has stopped
cd ..
echo.
echo ========================================================================
echo PPSG Gateway stopped.
echo ========================================================================
echo.
pause

@REM Made with Bob

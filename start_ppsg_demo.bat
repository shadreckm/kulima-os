@echo off
echo ================================
echo  KULIMA OS – PPSG LIVE DEMO
echo ================================
echo.

REM Ensure we are in the repo root (this file’s directory)
cd /d "%~dp0"

REM Activate virtual environment
call ppsg\venv\Scripts\activate

echo.
echo Starting Privacy-Preserving Signal Gateway...
echo.
echo When ready, open:
echo   http://localhost:8000/docs
echo.
echo Press CTRL+C here to stop the demo.
echo.

REM IMPORTANT: run as module, not file
python -m ppsg.gateway
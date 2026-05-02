#!/bin/bash
# KULIMA OS Pilot Demo - Unix/Linux/Mac Shell Script
# ===================================================
# This script runs the KULIMA OS pilot demonstration on Unix-like systems.
# No external dependencies required - just Python 3.

echo ""
echo "========================================================================"
echo "  KULIMA OS PILOT DEMONSTRATION"
echo "  Coordination-First Infrastructure Planning"
echo "========================================================================"
echo ""
echo "Starting demo..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH."
        echo ""
        echo "Please install Python 3 from https://python.org/downloads/"
        echo "Or use your system's package manager:"
        echo "  - Ubuntu/Debian: sudo apt-get install python3"
        echo "  - macOS: brew install python3"
        echo "  - Fedora: sudo dnf install python3"
        echo ""
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Display Python version
echo "Using Python:"
$PYTHON_CMD --version
echo ""

# Run the demo
echo "Running KULIMA OS pilot demo..."
echo ""
$PYTHON_CMD kulima_pilot_demo.py

# Check if demo ran successfully
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================================================"
    echo "  ERROR: Demo failed to run"
    echo "========================================================================"
    echo ""
    echo "Troubleshooting:"
    echo "1. Make sure you're in the correct folder (should contain kulima_pilot_demo.py)"
    echo "2. Check that all Python files are present"
    echo "3. See RUN_DEMO.md for detailed instructions"
    echo ""
    exit 1
fi

# Success message
echo ""
echo "========================================================================"
echo "  DEMO COMPLETED SUCCESSFULLY"
echo "========================================================================"
echo ""
echo "Generated files:"
echo "  - demand_signal_prospectus.json (machine-readable)"
echo "  - demand_signal_prospectus.md (human-readable)"
echo ""
echo "Next steps:"
echo "  1. Open demand_signal_prospectus.md to see the results"
echo "  2. Read AGENTS.md to understand system invariants"
echo "  3. Explore the Python source code"
echo ""
echo "For detailed instructions, see RUN_DEMO.md"
echo ""

# Made with Bob

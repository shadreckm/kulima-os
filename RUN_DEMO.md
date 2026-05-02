# How to Run the KULIMA OS Pilot Demo

This guide will help you run the KULIMA OS pilot demonstration on your computer.

## Prerequisites

You need **Python 3** installed on your computer. That's it! No other software or libraries are required.

### Check if Python is Installed

Open a terminal or command prompt and type:

```bash
python --version
```

or

```bash
python3 --version
```

You should see something like `Python 3.8.0` or higher. If you don't have Python installed, download it from [python.org](https://www.python.org/downloads/).

## Running the Demo

### Option 1: Use the Automated Script (Easiest)

#### On Windows:
1. Open the folder containing the KULIMA OS files
2. Double-click `run_demo.bat`
3. The demo will run automatically in a command window

Or from Command Prompt:
```cmd
run_demo.bat
```

#### On Mac/Linux:
1. Open Terminal
2. Navigate to the KULIMA OS folder:
   ```bash
   cd path/to/kulima-os-hackathon
   ```
3. Make the script executable (first time only):
   ```bash
   chmod +x run_demo.sh
   ```
4. Run the script:
   ```bash
   ./run_demo.sh
   ```

### Option 2: Run Python Directly

If the automated scripts don't work, you can run the demo directly:

#### On Windows (Command Prompt):
```cmd
python kulima_pilot_demo.py
```

#### On Mac/Linux (Terminal):
```bash
python3 kulima_pilot_demo.py
```

## What to Expect

When you run the demo, you'll see:

1. **Step 1: Synthetic Coordination Signals**
   - The system generates identity-free coordination signals
   - Press Enter to continue

2. **Step 2: LUMOZA - Coordination Engine**
   - Processes signals through 7-cycle coordination logic
   - Identifies stable patterns
   - Press Enter to continue

3. **Step 3: ZENTARI - Trust Engine**
   - Evaluates coordination confidence
   - Generates trust scores
   - Press Enter to continue

4. **Step 4: Demand-Signal Prospectus**
   - Generates institutional outputs
   - Creates two files (see below)

5. **Demo Complete**
   - Summary of results
   - List of generated files

## Generated Files

After running the demo, you'll find two new files in the same folder:

1. **`demand_signal_prospectus.json`**
   - Machine-readable format
   - For software systems and APIs

2. **`demand_signal_prospectus.md`**
   - Human-readable format
   - Open with any text editor or Markdown viewer
   - **Start here** to see the results!

## Viewing the Results

### View the Markdown File (Recommended)

**On Windows:**
- Right-click `demand_signal_prospectus.md`
- Choose "Open with" → Notepad or any text editor
- Or open it in VS Code for better formatting

**On Mac:**
- Right-click `demand_signal_prospectus.md`
- Choose "Open With" → TextEdit or any text editor
- Or use `open demand_signal_prospectus.md` in Terminal

**On Linux:**
- Use any text editor: `nano demand_signal_prospectus.md`
- Or: `cat demand_signal_prospectus.md` to view in terminal

### View the JSON File (Optional)

Open `demand_signal_prospectus.json` in any text editor or JSON viewer to see the structured data format.

## Troubleshooting

### "Python is not recognized" or "command not found"

**Problem:** Python is not installed or not in your system PATH.

**Solution:**
1. Install Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart your terminal/command prompt
4. Try again

### "No module named 'pilot_signals'"

**Problem:** You're running the script from the wrong folder.

**Solution:**
1. Make sure you're in the `kulima-os-hackathon` folder
2. You should see files like `pilot_signals.py`, `lumoza_engine.py`, etc.
3. Run the demo from this folder

### Script won't run on Mac/Linux

**Problem:** The script doesn't have execute permissions.

**Solution:**
```bash
chmod +x run_demo.sh
./run_demo.sh
```

### Demo runs but no files are created

**Problem:** You might not have write permissions in the folder.

**Solution:**
1. Check if you can create files in this folder
2. Try running from a different location (like your Documents folder)
3. Copy the entire `kulima-os-hackathon` folder to your home directory

## What the Demo Shows

The KULIMA OS pilot demonstrates:

- ✅ **Identity-free signal processing** - No personal data anywhere
- ✅ **7-cycle coordination logic** - Detects stable patterns over weekly cycles
- ✅ **Trust-as-a-Service** - Trust derived from coordination, not individuals
- ✅ **Infrastructure planning** - Generates bankable prospectuses for decision-makers
- ✅ **Privacy by design** - All system invariants enforced architecturally

## Next Steps

After running the demo:

1. **Read the prospectus**: Open `demand_signal_prospectus.md` to see the results
2. **Explore the code**: Look at the Python files to understand how it works
3. **Read AGENTS.md**: Learn about the system invariants and architecture
4. **Read README.md**: Get the full project overview

## Need Help?

If you're still having trouble:

1. Make sure Python 3 is installed: `python --version` or `python3 --version`
2. Make sure you're in the correct folder (you should see `kulima_pilot_demo.py`)
3. Try running directly: `python kulima_pilot_demo.py` or `python3 kulima_pilot_demo.py`

---

**Enjoy exploring KULIMA OS!** 🚀
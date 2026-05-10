# Roblox Stonks Helper

This is a lightweight local helper for the Roblox game `Stonks`.

It does two things:

1. Captures your primary screen into `screen.png` on a fast loop.
2. Reads the stock chart from that screenshot and prints a simple `BUY`, `SELL`, `HOLD`, or `WAIT` signal.

The helper is tuned around the Roblox chart layout we used while testing. It is meant as a bankroll-preservation aid, not a guaranteed profit bot.

## Files

- `auto_screenshot.ps1`
  Captures the primary screen every 100ms and writes `screen.png`.
- `stonks_helper.py`
  Reads `screen.png`, extracts the chart line, and writes the latest signal to `stonks_signal.txt`.
- `start_stonks_helper.ps1`
  Starts the Python signal helper with the fast polling loop.

## Requirements

- Windows
- PowerShell
- Python 3
- Python packages:
  - `pillow`
  - `numpy`

## Setup

Clone or download the repo, then open PowerShell in the project folder.

Install Python packages if you need them:

```powershell
pip install -r requirements.txt
```

## How To Run

Open two PowerShell windows in the project folder.

Window 1:

```powershell
powershell -ExecutionPolicy Bypass -File .\auto_screenshot.ps1
```

Window 2:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_stonks_helper.ps1
```

## What It Outputs

The helper writes the latest signal to:

```text
stonks_signal.txt
```

Example:

```text
[11:01:59] HOLD: movement is flat right now (score=0.00 short=0.0 medium=0.0 pos=0.00 range=2.0)
```

Signal meanings:

- `BUY`: momentum is improving and price is not too extended
- `SELL`: momentum is fading from a stronger area
- `HOLD`: the move is mostly flat
- `WAIT`: mixed setup or a risky chase

## Notes

- `screen.png`, `stonks_debug.png`, and logs are generated locally and should not be committed.
- The capture loop deletes the screenshot file when you stop it with `Ctrl+C`.
- If `CopyFromScreen` fails on a frame, the capture loop now skips that frame and keeps going.
- This helper is based on chart shape only. It does not read full game state and it does not place clicks for you.

## Troubleshooting

If `start_stonks_helper.ps1` says the file does not exist, make sure you first run:

```powershell
cd path\to\the\project
```

If `auto_screenshot.ps1` throws `The handle is invalid`, restart it and keep Roblox on the primary screen.

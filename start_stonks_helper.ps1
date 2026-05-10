$ErrorActionPreference = "Stop"

$python = "C:\Users\engra\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$script = Join-Path $PSScriptRoot "stonks_helper.py"

Write-Host "Starting Stonks signal helper."
Write-Host "Keep auto_screenshot.ps1 running in another PowerShell window."
Write-Host "Press Ctrl+C to stop."

& $python $script --interval 0.1 --debug --beep

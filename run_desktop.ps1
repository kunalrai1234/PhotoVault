# PhotoVault Local AI Desktop Launcher
Write-Host "Starting PhotoVault Local AI Desktop Application..." -ForegroundColor Cyan

$pythonExe = if (Test-Path "venv\Scripts\python.exe") { "venv\Scripts\python.exe" } else { "python" }
& $pythonExe backend\app.py --desktop

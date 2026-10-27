@echo off
title PhotoVault Local AI
echo Starting PhotoVault Local AI Desktop Application...
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe backend\app.py --desktop
) else (
    python backend\app.py --desktop
)

pause

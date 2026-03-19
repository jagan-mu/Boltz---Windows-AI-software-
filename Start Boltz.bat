@echo off
title Boltz — Windows AI Agent
color 0B

echo.
echo  ██████╗  ██████╗ ██╗  ████████╗███████╗
echo  ██╔══██╗██╔═══██╗██║  ╚══██╔══╝╚════██║
echo  ██████╔╝██║   ██║██║     ██║       ██╔╝
echo  ██╔══██╗██║   ██║██║     ██║      ██╔╝
echo  ██████╔╝╚██████╔╝███████╗██║      ██║
echo  ╚═════╝  ╚═════╝ ╚══════╝╚═╝      ╚═╝
echo.
echo  Windows AI Agent — Starting...
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo  [OK] Python found.

:: Install requests if missing
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo  [..] Installing 'requests' package...
    pip install requests --quiet
    if errorlevel 1 (
        echo  [ERROR] pip install failed. Run manually: pip install requests
        pause & exit /b 1
    )
    echo  [OK] requests installed.
) else (
    echo  [OK] Dependencies ready.
)

echo.
echo  [>>] Starting Boltz on http://127.0.0.1:7825
echo  [>>] Browser will open automatically.
echo.
echo  Press Ctrl+C to stop Boltz.
echo  ─────────────────────────────────────────
echo.

cd /d "%~dp0"
python boltz_server.py
pause

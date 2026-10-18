@echo off
title JARVIS Command Center Launcher
cd /d "%~dp0"
echo ========================================================
echo       JARVIS PERSONAL AI AGENT -- COMMAND CENTER
echo ========================================================
echo.

netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [INFO] Backend is already running on http://127.0.0.1:8000
) else (
    echo [INFO] Launching FastAPI Backend on http://127.0.0.1:8000 ...
    if exist ".venv\Scripts\python.exe" (
        start "JARVIS Backend Server" /min .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
    ) else (
        start "JARVIS Backend Server" /min python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
    )
    timeout /t 2 /nobreak >nul
)

echo [INFO] Opening JARVIS Command Center in your browser...
start http://127.0.0.1:8000/app

echo.
echo ========================================================
echo   HUD Frontend : http://127.0.0.1:8000/app
echo   API Docs     : http://127.0.0.1:8000/docs
echo   Health Check : http://127.0.0.1:8000/health
echo ========================================================
echo.
pause
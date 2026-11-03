@echo off
setlocal
cd /d "%~dp0"
if not exist backend\.venv\Scripts\python.exe (echo Run setup.bat first.& pause& exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first.& pause& exit /b 1)
start "MediSense API" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "MediSense Web" /D "%~dp0frontend" cmd /k "npm run dev"
echo Backend: http://localhost:8000/docs
echo Frontend: http://localhost:5173

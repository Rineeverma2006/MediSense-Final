@echo off
setlocal
cd /d "%~dp0"
echo [1/3] Setting up Python backend...
where python >nul 2>nul || (echo Python 3.10-3.12 was not found.& pause & exit /b 1)
where npm >nul 2>nul || (echo Node.js/npm was not found.& pause & exit /b 1)
cd backend
if not exist .venv python -m venv .venv
if errorlevel 1 (echo Could not create Python virtual environment.& pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 (echo Could not prepare pip.& pause & exit /b 1)
pip install -r requirements.txt
if errorlevel 1 (echo Backend dependency installation failed.& pause & exit /b 1)
if not exist .env copy .env.example .env
python seed_demo.py
if errorlevel 1 (echo Demo seeding failed.& pause & exit /b 1)
cd ..
echo [2/3] Installing frontend packages...
cd frontend
call npm ci
if errorlevel 1 (echo Frontend dependency installation failed.& pause & exit /b 1)
cd ..
echo [3/3] Setup complete.
echo Run start-backend.bat and start-frontend.bat in separate terminals.
pause

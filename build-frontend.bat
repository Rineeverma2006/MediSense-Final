@echo off
setlocal
cd /d "%~dp0frontend"
if not exist node_modules (echo Run setup.bat first.& pause& exit /b 1)
call npm run build
if errorlevel 1 (echo Frontend production build failed.& pause& exit /b 1)
echo Frontend production build passed.

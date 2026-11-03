@echo off
cd /d "%~dp0frontend"
if not exist node_modules (
 echo Frontend dependencies missing. Run setup.bat first.
 pause
 exit /b 1
)
call npm run dev

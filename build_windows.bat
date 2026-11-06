@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run start_windows.bat first to install dependencies.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m pip install pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name "CampaignForge" --add-data "assets;assets" --icon "assets\CampaignForge.ico" app.py
if errorlevel 1 (echo Build failed. & pause & exit /b 1)
echo.
echo Your executable is dist\CampaignForge\CampaignForge.exe
pause

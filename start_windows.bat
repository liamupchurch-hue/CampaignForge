@echo off
setlocal
cd /d "%~dp0"
if not exist ".beta_notice_ack" goto beta_notice
goto launch
:beta_notice
echo.
echo --------------------------------------------------------
echo CAMPAIGN FORGE v1.1.0-beta.1 - EXPERIMENTAL PUBLIC BETA
echo No warranty. Bugs and data loss are possible. Keep backups.
echo Optional APIs may incur charges and send data online.
echo Optional AI downloads may use substantial disk/data/GPU.
echo Read BETA_DISCLAIMER.md and API_AND_DATA_NOTICE.md.
echo --------------------------------------------------------
echo.
choice /C YN /M "Have you reviewed the notices and wish to continue?"
if errorlevel 2 exit /b 1
> ".beta_notice_ack" echo Beta notices displayed.
:launch
where py >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.11 or newer from python.org first.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Creating local Python environment ...
    py -3 -m venv .venv
    if errorlevel 1 (echo Could not create environment. & pause & exit /b 1)
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (echo Could not install requirements. & pause & exit /b 1)
)
".venv\Scripts\python.exe" app.py
if errorlevel 1 pause

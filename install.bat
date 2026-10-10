@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
if exist .venv\Scripts\python.exe (
  .venv\Scripts\pip install -r requirements-local.txt && .venv\Scripts\python install.py %*
)
set rc=%errorlevel%
pause
exit /b %rc%

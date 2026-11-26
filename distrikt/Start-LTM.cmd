@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys,sqlite3; assert sys.version_info >= (3,9)" >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0app\launcher.py" %*
  if errorlevel 1 pause
  exit /b
)
python -c "import sys,sqlite3; assert sys.version_info >= (3,9)" >nul 2>&1
if not errorlevel 1 (
  python "%~dp0app\launcher.py" %*
  if errorlevel 1 pause
  exit /b
)
echo Installer Python 3.9 eller nyere fra python.org og proev igen.
start "" https://www.python.org/downloads/windows/
pause

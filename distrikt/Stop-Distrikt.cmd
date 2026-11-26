@echo off
setlocal
cd /d "%~dp0"
py -3 "%~dp0app\server.py" --stop 2>nul
if errorlevel 1 python "%~dp0app\server.py" --stop

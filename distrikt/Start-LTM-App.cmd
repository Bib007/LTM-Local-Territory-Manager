@echo off
rem Purpose-specific Windows local-app launcher. Data stay outside this program folder.
call "%~dp0Start-LTM.cmd" --mode local %*

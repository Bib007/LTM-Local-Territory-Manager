@echo off
rem Purpose-specific Windows private-server launcher. It prompts for a private LAN address.
call "%~dp0Start-LTM.cmd" --mode server %*

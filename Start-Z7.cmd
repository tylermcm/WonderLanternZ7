@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Z7.ps1" -OpenBrowser
if errorlevel 1 pause

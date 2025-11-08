@echo off
REM Close Unused Processes - Batch wrapper
REM This bypasses PowerShell execution policy

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0close_unused_processes.ps1"

exit /b %ERRORLEVEL%


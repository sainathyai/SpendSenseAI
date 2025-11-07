@echo off
REM Git Merge and Push Script (Batch wrapper)
REM This ensures proper termination

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0git_merge_and_push.ps1"

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM Explicitly exit
exit /b %EXIT_CODE%


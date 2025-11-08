@echo off
echo Starting Amplify Frontend Deployment...
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0deploy_amplify_simple.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Script failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Script completed successfully!
pause



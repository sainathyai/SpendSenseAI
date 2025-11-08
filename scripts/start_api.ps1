# PowerShell script to start the API server
# Run this from the project root directory

Set-Location $PSScriptRoot\..

Write-Host "Starting SpendSenseAI API Server..." -ForegroundColor Green
Write-Host ""
Write-Host "API will be available at http://localhost:8000" -ForegroundColor Yellow
Write-Host "API docs at http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""

# Add current directory to Python path
$env:PYTHONPATH = $PWD.Path

# Start API server
python scripts/run_api.py


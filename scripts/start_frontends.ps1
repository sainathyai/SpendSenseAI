# PowerShell script to start both Operator and User dashboards
# Run this from the project root directory

Set-Location $PSScriptRoot\..

Write-Host "Starting SpendSenseAI Frontends..." -ForegroundColor Green
Write-Host ""
Write-Host "Operator Dashboard will be available at http://localhost:5173" -ForegroundColor Yellow
Write-Host "User Dashboard will be available at http://localhost:5174" -ForegroundColor Yellow
Write-Host ""
Write-Host "Make sure the API server is running at http://localhost:8000" -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
Set-Location frontend

# Start Operator Dashboard in background
Write-Host "Starting Operator Dashboard on port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev:operator"

# Wait a moment
Start-Sleep -Seconds 2

# Start User Dashboard in background
Write-Host "Starting User Dashboard on port 5174..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev:user"

Write-Host ""
Write-Host "Both dashboards are starting..." -ForegroundColor Green
Write-Host "Operator Dashboard: http://localhost:5173" -ForegroundColor Yellow
Write-Host "User Dashboard: http://localhost:5174/dashboard/CUST000001" -ForegroundColor Yellow


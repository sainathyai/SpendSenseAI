# PowerShell script to start the Operator Dashboard
# Run this from the project root directory

Set-Location $PSScriptRoot\..

Write-Host "Starting SpendSenseAI Operator Dashboard..." -ForegroundColor Green
Write-Host ""
Write-Host "Make sure the API server is running at http://localhost:8000" -ForegroundColor Yellow
Write-Host "Dashboard will be available at http://localhost:8501" -ForegroundColor Yellow
Write-Host ""

# Add current directory to Python path
$env:PYTHONPATH = $PWD.Path

# Start Streamlit
python -m streamlit run ui/dashboard.py --server.port 8501


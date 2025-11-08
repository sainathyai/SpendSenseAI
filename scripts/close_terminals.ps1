# Close Unused Terminal Processes (PowerShell)
# This script helps identify and close hanging terminal processes

$ErrorActionPreference = "Stop"

Write-Host "Checking for hanging terminal processes..." -ForegroundColor Yellow
Write-Host ""

# Find PowerShell processes that might be hanging
$powershellProcesses = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -eq "" -or $_.MainWindowTitle -match "PowerShell|Command"
}

if ($powershellProcesses) {
    Write-Host "Found PowerShell processes:" -ForegroundColor Cyan
    foreach ($proc in $powershellProcesses) {
        Write-Host "  PID: $($proc.Id) - $($proc.ProcessName) - $($proc.MainWindowTitle)" -ForegroundColor White
    }
    Write-Host ""
    
    $response = Read-Host "Do you want to close these processes? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        foreach ($proc in $powershellProcesses) {
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Host "Closed process PID: $($proc.Id)" -ForegroundColor Green
            } catch {
                Write-Host "Could not close process PID: $($proc.Id)" -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "No hanging PowerShell processes found." -ForegroundColor Green
}

# Find cmd.exe processes
$cmdProcesses = Get-Process -Name "cmd" -ErrorAction SilentlyContinue

if ($cmdProcesses) {
    Write-Host ""
    Write-Host "Found CMD processes:" -ForegroundColor Cyan
    foreach ($proc in $cmdProcesses) {
        Write-Host "  PID: $($proc.Id) - $($proc.ProcessName) - $($proc.MainWindowTitle)" -ForegroundColor White
    }
    Write-Host ""
    
    $response = Read-Host "Do you want to close these processes? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        foreach ($proc in $cmdProcesses) {
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Host "Closed process PID: $($proc.Id)" -ForegroundColor Green
            } catch {
                Write-Host "Could not close process PID: $($proc.Id)" -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "No hanging CMD processes found." -ForegroundColor Green
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green

# Explicitly exit
exit 0


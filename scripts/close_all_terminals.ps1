# Close All Unused Terminal Processes (PowerShell)
# This script closes all hanging terminal processes

$ErrorActionPreference = "Stop"

Write-Host "Closing Unused Terminal Processes..." -ForegroundColor Yellow
Write-Host ""

# Get all terminal processes
$bashProcesses = Get-Process -Name "bash" -ErrorAction SilentlyContinue
$cmdProcesses = Get-Process -Name "cmd" -ErrorAction SilentlyContinue
$powershellProcesses = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    # Exclude the current PowerShell process
    $_.Id -ne $PID
}

$totalCount = ($bashProcesses.Count) + ($cmdProcesses.Count) + ($powershellProcesses.Count)

if ($totalCount -eq 0) {
    Write-Host "No unused terminal processes found." -ForegroundColor Green
    exit 0
}

Write-Host "Found $totalCount terminal processes:" -ForegroundColor Cyan
Write-Host "  - Bash: $($bashProcesses.Count)" -ForegroundColor White
Write-Host "  - CMD: $($cmdProcesses.Count)" -ForegroundColor White
Write-Host "  - PowerShell: $($powershellProcesses.Count)" -ForegroundColor White
Write-Host ""

# Close bash processes
if ($bashProcesses) {
    Write-Host "Closing bash processes..." -ForegroundColor Yellow
    foreach ($proc in $bashProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  Closed bash process PID: $($proc.Id)" -ForegroundColor Gray
        } catch {
            # Ignore errors (process might already be closed)
        }
    }
}

# Close cmd processes
if ($cmdProcesses) {
    Write-Host "Closing cmd processes..." -ForegroundColor Yellow
    foreach ($proc in $cmdProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  Closed cmd process PID: $($proc.Id)" -ForegroundColor Gray
        } catch {
            # Ignore errors
        }
    }
}

# Close PowerShell processes (excluding current)
if ($powershellProcesses) {
    Write-Host "Closing PowerShell processes..." -ForegroundColor Yellow
    foreach ($proc in $powershellProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  Closed PowerShell process PID: $($proc.Id)" -ForegroundColor Gray
        } catch {
            # Ignore errors
        }
    }
}

Write-Host ""
Write-Host "Done! Closed $totalCount terminal processes." -ForegroundColor Green

# Explicitly exit
exit 0


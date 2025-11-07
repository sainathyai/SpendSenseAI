# Close Unused Cursor-Related Processes (PowerShell)
# This script closes only unused/hanging processes, keeping essential ones

$ErrorActionPreference = "Stop"

Write-Host "Closing Unused Processes..." -ForegroundColor Yellow
Write-Host ""

$closedCount = 0
$keptCount = 0

# Get all processes
$allProcesses = Get-Process | Where-Object {
    $_.ProcessName -match "bash|cmd|powershell|git|node" -or
    ($_.ProcessName -match "Cursor" -and $_.ProcessName -ne "Cursor")
} | Sort-Object ProcessName, Id

# Close terminal processes with no window (likely unused)
$terminals = $allProcesses | Where-Object { $_.ProcessName -match "bash|cmd|powershell" }
$unusedTerminals = $terminals | Where-Object {
    [string]::IsNullOrWhiteSpace($_.MainWindowTitle) -or
    $_.MainWindowTitle -eq ""
}

Write-Host "Terminal Processes:" -ForegroundColor Cyan
foreach ($proc in $terminals) {
    if ($unusedTerminals -contains $proc) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Closed unused terminal PID: $($proc.Id) ($($proc.ProcessName))" -ForegroundColor Green
            $closedCount++
        } catch {
            Write-Host "  [FAIL] Could not close PID: $($proc.Id)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  -> Keeping active terminal PID: $($proc.Id) ($($proc.ProcessName)) - $($proc.MainWindowTitle)" -ForegroundColor Gray
        $keptCount++
    }
}

Write-Host ""

# Close git processes (likely hanging from pager)
$gitProcesses = $allProcesses | Where-Object { $_.ProcessName -eq "git" }
if ($gitProcesses.Count -gt 3) {
    Write-Host "Git Processes (likely hanging):" -ForegroundColor Cyan
    foreach ($proc in $gitProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Closed git process PID: $($proc.Id)" -ForegroundColor Green
            $closedCount++
        } catch {
            Write-Host "  [FAIL] Could not close PID: $($proc.Id)" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Close small node processes (might be orphaned)
$nodeProcesses = $allProcesses | Where-Object { $_.ProcessName -eq "node" }
$orphanedNode = $nodeProcesses | Where-Object {
    [string]::IsNullOrWhiteSpace($_.MainWindowTitle) -and
    $_.WorkingSet64 -lt 50MB
}

if ($orphanedNode) {
    Write-Host "Orphaned Node Processes:" -ForegroundColor Cyan
    foreach ($proc in $orphanedNode) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Closed node process PID: $($proc.Id)" -ForegroundColor Green
            $closedCount++
        } catch {
            Write-Host "  [FAIL] Could not close PID: $($proc.Id)" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Closed: $closedCount processes" -ForegroundColor Green
Write-Host "Kept: $keptCount active processes" -ForegroundColor Green
Write-Host ""

# Explicitly exit
exit 0


# Analyze and Clean Cursor Processes (PowerShell)
# This script identifies all Cursor-related processes and helps clean up unused ones

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cursor Process Analysis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get all processes related to Cursor
$cursorProcesses = Get-Process | Where-Object {
    $_.ProcessName -match "Cursor|cursor" -or
    $_.MainWindowTitle -match "Cursor" -or
    $_.Path -like "*Cursor*"
} | Sort-Object ProcessName, Id

# Get terminal processes
$bashProcesses = Get-Process -Name "bash" -ErrorAction SilentlyContinue
$cmdProcesses = Get-Process -Name "cmd" -ErrorAction SilentlyContinue
$powershellProcesses = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.Id -ne $PID
}

# Get all processes that might be related
$allProcesses = Get-Process | Where-Object {
    $_.ProcessName -match "Cursor|cursor|bash|cmd|powershell|node|npm|git" -or
    $_.MainWindowTitle -match "Cursor|Terminal|Git"
} | Sort-Object ProcessName, Id

Write-Host "Found Processes:" -ForegroundColor Yellow
Write-Host ""

# Group by process name
$grouped = $allProcesses | Group-Object ProcessName | Sort-Object Count -Descending

foreach ($group in $grouped) {
    $count = $group.Count
    $name = $group.Name
    
    Write-Host "$name ($count processes):" -ForegroundColor Cyan
    
    foreach ($proc in $group.Group) {
        $cpu = if ($proc.CPU) { "{0:N2}" -f $proc.CPU } else { "0.00" }
        $memory = "{0:N2} MB" -f ($proc.WorkingSet64 / 1MB)
        $title = if ($proc.MainWindowTitle) { $proc.MainWindowTitle } else { "(no window)" }
        
        Write-Host "  PID: $($proc.Id) | CPU: $cpu | Memory: $memory | Window: $title" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Process Categories" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Categorize processes
$cursorMain = $allProcesses | Where-Object { $_.ProcessName -eq "Cursor" }
$cursorHelper = $allProcesses | Where-Object { $_.ProcessName -match "Cursor" -and $_.ProcessName -ne "Cursor" }
$terminals = $allProcesses | Where-Object { $_.ProcessName -match "bash|cmd|powershell" }
$nodeProcesses = $allProcesses | Where-Object { $_.ProcessName -eq "node" }
$gitProcesses = $allProcesses | Where-Object { $_.ProcessName -eq "git" }

Write-Host "Cursor Main Processes: $($cursorMain.Count)" -ForegroundColor Green
Write-Host "  These are the main Cursor application windows - KEEP THESE" -ForegroundColor Gray
Write-Host ""

Write-Host "Cursor Helper Processes: $($cursorHelper.Count)" -ForegroundColor Yellow
Write-Host "  These are Cursor helper processes (extensions, language servers) - Usually KEEP" -ForegroundColor Gray
Write-Host ""

Write-Host "Terminal Processes: $($terminals.Count)" -ForegroundColor $(if ($terminals.Count -gt 5) { "Red" } else { "Yellow" })
Write-Host "  These are terminal sessions - May be UNUSED if count is high" -ForegroundColor Gray
Write-Host ""

Write-Host "Node Processes: $($nodeProcesses.Count)" -ForegroundColor Yellow
Write-Host "  These might be from npm/node scripts - Check if needed" -ForegroundColor Gray
Write-Host ""

Write-Host "Git Processes: $($gitProcesses.Count)" -ForegroundColor $(if ($gitProcesses.Count -gt 3) { "Red" } else { "Yellow" })
Write-Host "  These are git operations - May be HANGING if count is high" -ForegroundColor Gray
Write-Host ""

# Identify likely unused processes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Likely Unused Processes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$unused = @()

# Terminal processes with no window title (likely background/hanging)
$unusedTerminals = $terminals | Where-Object {
    [string]::IsNullOrWhiteSpace($_.MainWindowTitle) -or
    $_.MainWindowTitle -eq ""
}

if ($unusedTerminals) {
    Write-Host "Unused Terminal Processes (no window):" -ForegroundColor Red
    foreach ($proc in $unusedTerminals) {
        Write-Host "  PID: $($proc.Id) | $($proc.ProcessName) | Memory: $("{0:N2} MB" -f ($proc.WorkingSet64 / 1MB))" -ForegroundColor Yellow
        $unused += $proc
    }
    Write-Host ""
}

# Git processes that are likely hanging
if ($gitProcesses.Count -gt 3) {
    Write-Host "Likely Hanging Git Processes:" -ForegroundColor Red
    foreach ($proc in $gitProcesses) {
        Write-Host "  PID: $($proc.Id) | Memory: $("{0:N2} MB" -f ($proc.WorkingSet64 / 1MB))" -ForegroundColor Yellow
        $unused += $proc
    }
    Write-Host ""
}

# Node processes that might be orphaned
$orphanedNode = $nodeProcesses | Where-Object {
    [string]::IsNullOrWhiteSpace($_.MainWindowTitle) -and
    $_.WorkingSet64 -lt 50MB  # Small memory usage might indicate orphaned
}

if ($orphanedNode) {
    Write-Host "Possibly Orphaned Node Processes:" -ForegroundColor Yellow
    foreach ($proc in $orphanedNode) {
        Write-Host "  PID: $($proc.Id) | Memory: $("{0:N2} MB" -f ($proc.WorkingSet64 / 1MB))" -ForegroundColor Gray
    }
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Processes Found: $($allProcesses.Count)" -ForegroundColor White
Write-Host "Likely Unused: $($unused.Count)" -ForegroundColor $(if ($unused.Count -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($unused.Count -gt 0) {
    Write-Host "Would you like to close the unused processes?" -ForegroundColor Yellow
    Write-Host "Run: .\scripts\close_unused_processes.ps1" -ForegroundColor Cyan
} else {
    Write-Host "No obviously unused processes found." -ForegroundColor Green
}

Write-Host ""
Write-Host "To close unused processes, run:" -ForegroundColor Cyan
Write-Host "  .\scripts\close_unused_processes.ps1" -ForegroundColor White
Write-Host ""

# Explicitly exit
exit 0


# Fix file timestamps that are before 1980 (ZIP format limitation)

$ErrorActionPreference = "Continue"

$cutoffDate = Get-Date "1980-01-01"
$fixedCount = 0

Write-Host "Fixing file timestamps before 1980..." -ForegroundColor Yellow

Get-ChildItem -Recurse -File | ForEach-Object {
    if ($_.LastWriteTime -lt $cutoffDate) {
        Write-Host "Fixing: $($_.FullName) - $($_.LastWriteTime)" -ForegroundColor Yellow
        $_.LastWriteTime = $cutoffDate
        $fixedCount++
    }
}

Write-Host "Fixed $fixedCount files" -ForegroundColor Green





# Git Merge and Push Script
# This script properly handles git operations and ensures clean termination

$ErrorActionPreference = "Stop"

Write-Host "Git Merge and Push Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Configure git to not use pager
$env:GIT_PAGER = "cat"
git config --global core.pager cat

# Get current branch
$CURRENT_BRANCH = git rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $CURRENT_BRANCH" -ForegroundColor Yellow
Write-Host ""

# Check if there are uncommitted changes
$STATUS = git status --porcelain
if ($STATUS) {
    Write-Host "Uncommitted changes detected:" -ForegroundColor Yellow
    Write-Host $STATUS
    Write-Host ""
    
    $response = Read-Host "Do you want to commit these changes? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Staging all changes..." -ForegroundColor Yellow
        git add -A
        
        $commitMessage = Read-Host "Enter commit message (or press Enter for default)"
        if ([string]::IsNullOrWhiteSpace($commitMessage)) {
            $commitMessage = "Update: Route53 and Amplify deployment setup"
        }
        
        Write-Host "Committing changes..." -ForegroundColor Yellow
        git commit -m $commitMessage
        Write-Host "Changes committed" -ForegroundColor Green
    } else {
        Write-Host "Skipping commit. Please commit or stash changes manually." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Switching to main branch..." -ForegroundColor Yellow
git checkout main
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Could not switch to main branch" -ForegroundColor Red
    exit 1
}

Write-Host "Pulling latest changes from main..." -ForegroundColor Yellow
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not pull from main. Continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Merging $CURRENT_BRANCH into main..." -ForegroundColor Yellow
git merge $CURRENT_BRANCH --no-edit
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Merge failed. Please resolve conflicts manually." -ForegroundColor Red
    Write-Host "Run: git merge --abort to cancel the merge" -ForegroundColor Yellow
    exit 1
}

Write-Host "Merge successful!" -ForegroundColor Green
Write-Host ""

Write-Host "Pushing to origin/main..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Push failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Merged $CURRENT_BRANCH into main and pushed to origin" -ForegroundColor Green
Write-Host ""

# Explicitly exit
exit 0


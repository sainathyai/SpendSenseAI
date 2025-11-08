# Create Amplify Branches for Operator and User Dashboards (PowerShell)

$ErrorActionPreference = "Stop"

# Configuration
$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"
$REGION = "us-east-1"
# Branch configuration - can be overridden
$BRANCH_NAME = if ($env:AMPLIFY_BRANCH) { $env:AMPLIFY_BRANCH } else { "main" }  # Default branch name

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating Amplify Branches" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if logged in
$awsCheck = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -ne 0 -and $awsCheck -match "error|Error|ERROR") {
    Write-Host "ERROR: Not logged into AWS. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ AWS CLI configured" -ForegroundColor Green
Write-Host ""

# Step 1: Create Branch for Operator Dashboard
Write-Host "Step 1: Creating branch for Operator Dashboard..." -ForegroundColor Yellow

# Check if branch already exists
$OPERATOR_BRANCHES = aws amplify list-branches --app-id $OPERATOR_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
$OPERATOR_BRANCH_EXISTS = $OPERATOR_BRANCHES.branches | Where-Object { $_.branchName -eq $BRANCH_NAME }

if ($OPERATOR_BRANCH_EXISTS) {
    Write-Host "✅ Branch '$BRANCH_NAME' already exists for Operator Dashboard" -ForegroundColor Green
    Write-Host "   Branch ARN: $($OPERATOR_BRANCH_EXISTS.branchArn)" -ForegroundColor Gray
} else {
    Write-Host "Creating branch '$BRANCH_NAME' for Operator Dashboard..." -ForegroundColor Cyan
    
    try {
        $OPERATOR_BRANCH = aws amplify create-branch `
            --app-id $OPERATOR_APP_ID `
            --branch-name $BRANCH_NAME `
            --region $REGION `
            --enable-auto-build `
            --enable-pull-request-preview `
            --framework "React" 2>&1 | ConvertFrom-Json
        
        Write-Host "✅ Created branch '$BRANCH_NAME' for Operator Dashboard" -ForegroundColor Green
        Write-Host "   Branch ARN: $($OPERATOR_BRANCH.branch.branchArn)" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️  Could not create branch automatically. Error: $_" -ForegroundColor Yellow
        Write-Host "   You may need to create it manually in Amplify Console" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 2: Create Branch for User Dashboard
Write-Host "Step 2: Creating branch for User Dashboard..." -ForegroundColor Yellow

# Check if branch already exists
$USER_BRANCHES = aws amplify list-branches --app-id $USER_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
$USER_BRANCH_EXISTS = $USER_BRANCHES.branches | Where-Object { $_.branchName -eq $BRANCH_NAME }

if ($USER_BRANCH_EXISTS) {
    Write-Host "✅ Branch '$BRANCH_NAME' already exists for User Dashboard" -ForegroundColor Green
    Write-Host "   Branch ARN: $($USER_BRANCH_EXISTS.branchArn)" -ForegroundColor Gray
} else {
    Write-Host "Creating branch '$BRANCH_NAME' for User Dashboard..." -ForegroundColor Cyan
    
    try {
        $USER_BRANCH = aws amplify create-branch `
            --app-id $USER_APP_ID `
            --branch-name $BRANCH_NAME `
            --region $REGION `
            --enable-auto-build `
            --enable-pull-request-preview `
            --framework "React" 2>&1 | ConvertFrom-Json
        
        Write-Host "✅ Created branch '$BRANCH_NAME' for User Dashboard" -ForegroundColor Green
        Write-Host "   Branch ARN: $($USER_BRANCH.branch.branchArn)" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️  Could not create branch automatically. Error: $_" -ForegroundColor Yellow
        Write-Host "   You may need to create it manually in Amplify Console" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 3: Configure Branch Build Settings
Write-Host "Step 3: Configuring branch build settings..." -ForegroundColor Yellow

# Update Operator branch build settings
Write-Host "Configuring Operator Dashboard branch..." -ForegroundColor Cyan
try {
    $OPERATOR_BUILD_SPEC = @"
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build:operator
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
"@

    $OPERATOR_BUILD_SPEC | Out-File -FilePath "$env:TEMP\operator-buildspec.yml" -Encoding utf8NoBOM
    
    # Note: Amplify CLI doesn't have a direct API to update build spec via AWS CLI
    # This needs to be done in the Amplify Console or via amplify.yml file in repo
    Write-Host "✅ Build spec file created at: $env:TEMP\operator-buildspec.yml" -ForegroundColor Green
    Write-Host "   Copy this to: frontend/amplify-operator.yml in your repository" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️  Could not create build spec file" -ForegroundColor Yellow
}

# Update User branch build settings
Write-Host ""
Write-Host "Configuring User Dashboard branch..." -ForegroundColor Cyan
try {
    $USER_BUILD_SPEC = @"
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build:user
  artifacts:
    baseDirectory: frontend/dist-user
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*

"@

    $USER_BUILD_SPEC | Out-File -FilePath "$env:TEMP\user-buildspec.yml" -Encoding utf8NoBOM
    
    Write-Host "✅ Build spec file created at: $env:TEMP\user-buildspec.yml" -ForegroundColor Green
    Write-Host "   Copy this to: frontend/amplify-user.yml in your repository" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️  Could not create build spec file" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: List all branches
Write-Host "Step 4: Listing all branches..." -ForegroundColor Yellow

Write-Host ""
Write-Host "Operator Dashboard Branches:" -ForegroundColor Cyan
$OPERATOR_BRANCHES = aws amplify list-branches --app-id $OPERATOR_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
foreach ($branch in $OPERATOR_BRANCHES.branches) {
    Write-Host "  - $($branch.branchName) (Active: $($branch.active))" -ForegroundColor White
}

Write-Host ""
Write-Host "User Dashboard Branches:" -ForegroundColor Cyan
$USER_BRANCHES = aws amplify list-branches --app-id $USER_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
foreach ($branch in $USER_BRANCHES.branches) {
    Write-Host "  - $($branch.branchName) (Active: $($branch.active))" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Branch Setup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Branches created/verified" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Connect GitHub repository in Amplify Console for both apps" -ForegroundColor White
Write-Host "2. Ensure build spec files exist in repository:" -ForegroundColor White
Write-Host "   - frontend/amplify-operator.yml (for Operator Dashboard)" -ForegroundColor Gray
Write-Host "   - frontend/amplify-user.yml (for User Dashboard)" -ForegroundColor Gray
Write-Host "3. Push to '$BRANCH_NAME' branch to trigger deployment" -ForegroundColor White
Write-Host ""
Write-Host "Operator App ID: $OPERATOR_APP_ID" -ForegroundColor Cyan
Write-Host "User App ID: $USER_APP_ID" -ForegroundColor Cyan
Write-Host "Branch Name: $BRANCH_NAME" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


# Create Amplify apps for Operator and User Dashboards (PowerShell)

$ErrorActionPreference = "Stop"

$BACKEND_URL = "https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$REPO_URL = "https://github.com/sainathyai/SpendSenseAI.git"
$BRANCH = "phase3-advanced-features"
$REGION = "us-east-1"

Write-Host "Creating Amplify Apps for Frontend Dashboards" -ForegroundColor Green
Write-Host ""

# Check if apps already exist
$OPERATOR_APP = aws amplify list-apps --region $REGION --query "apps[?name=='spendsenseai-operator']" --output json | ConvertFrom-Json
$USER_APP = aws amplify list-apps --region $REGION --query "apps[?name=='spendsenseai-user']" --output json | ConvertFrom-Json

# Create Operator Dashboard App
if ($OPERATOR_APP.Count -eq 0) {
    Write-Host "Creating Operator Dashboard app..." -ForegroundColor Yellow
    
    $OPERATOR_APP_ID = (aws amplify create-app `
        --name "spendsenseai-operator" `
        --region $REGION `
        --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" | ConvertFrom-Json).app.appId
    
    Write-Host "SUCCESS: Created Operator app: $OPERATOR_APP_ID" -ForegroundColor Green
    
    # Create branch
    Write-Host "Creating branch..." -ForegroundColor Yellow
    aws amplify create-branch `
        --app-id $OPERATOR_APP_ID `
        --branch-name $BRANCH `
        --region $REGION | Out-Null
    
    Write-Host "SUCCESS: Created branch: $BRANCH" -ForegroundColor Green
} else {
    $OPERATOR_APP_ID = $OPERATOR_APP[0].appId
    Write-Host "Operator app already exists: $OPERATOR_APP_ID" -ForegroundColor Green
}

# Create User Dashboard App
if ($USER_APP.Count -eq 0) {
    Write-Host "Creating User Dashboard app..." -ForegroundColor Yellow
    
    $USER_APP_ID = (aws amplify create-app `
        --name "spendsenseai-user" `
        --region $REGION `
        --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" | ConvertFrom-Json).app.appId
    
    Write-Host "SUCCESS: Created User app: $USER_APP_ID" -ForegroundColor Green
    
    # Create branch
    Write-Host "Creating branch..." -ForegroundColor Yellow
    aws amplify create-branch `
        --app-id $USER_APP_ID `
        --branch-name $BRANCH `
        --region $REGION | Out-Null
    
    Write-Host "SUCCESS: Created branch: $BRANCH" -ForegroundColor Green
} else {
    $USER_APP_ID = $USER_APP[0].appId
    Write-Host "User app already exists: $USER_APP_ID" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Connect GitHub repository in Amplify Console for both apps"
Write-Host "2. Configure build settings:"
Write-Host "   - Operator: Base dir: frontend, Build: npm ci && npm run build:operator, Output: dist"
Write-Host "   - User: Base dir: frontend, Build: npm ci && npm run build:user, Output: dist-user"
Write-Host "3. Add custom domains:"
Write-Host "   - Operator: $OPERATOR_DOMAIN"
Write-Host "   - User: $USER_DOMAIN"
Write-Host ""
Write-Host "Operator App ID: $OPERATOR_APP_ID"
Write-Host "User App ID: $USER_APP_ID"


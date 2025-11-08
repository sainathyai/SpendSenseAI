# Deploy both Operator and User Dashboards to AWS Amplify (PowerShell)

$ErrorActionPreference = "Stop"

$BACKEND_URL = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com" }
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$ROOT_DOMAIN = "sainathyai.com"

Write-Host "Deploying Frontend Dashboards to AWS Amplify" -ForegroundColor Green
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Check Amplify CLI
if (-not (Get-Command amplify -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Amplify CLI..." -ForegroundColor Yellow
    npm install -g @aws-amplify/cli
}

Set-Location frontend

Write-Host "Step 1: Deploying Operator Dashboard..." -ForegroundColor Yellow
Write-Host "This will create an Amplify app for the Operator Dashboard"
Write-Host ""
Write-Host "Please follow these steps in AWS Console:"
Write-Host "1. Go to AWS Amplify Console"
Write-Host "2. Click 'New app' -> 'Host web app'"
Write-Host "3. Connect your GitHub repository"
Write-Host "4. Configure build settings:"
Write-Host "   - App name: spendsenseai-operator"
Write-Host "   - Branch: phase3-advanced-features"
Write-Host "   - Base directory: frontend"
Write-Host "   - Build command: npm ci && npm run build:operator"
Write-Host "   - Output directory: dist"
Write-Host "   - Build spec file: frontend/amplify-operator.yml"
Write-Host "5. Add environment variable:"
Write-Host "   - VITE_API_BASE_URL: $BACKEND_URL"
Write-Host "6. Deploy"
Write-Host ""

Write-Host "Step 2: Deploying User Dashboard..." -ForegroundColor Yellow
Write-Host "1. Go to AWS Amplify Console"
Write-Host "2. Click 'New app' -> 'Host web app'"
Write-Host "3. Connect your GitHub repository"
Write-Host "4. Configure build settings:"
Write-Host "   - App name: spendsenseai-user"
Write-Host "   - Branch: phase3-advanced-features"
Write-Host "   - Base directory: frontend"
Write-Host "   - Build command: npm ci && npm run build:user"
Write-Host "   - Output directory: dist-user"
Write-Host "   - Build spec file: frontend/amplify-user.yml"
Write-Host "5. Add environment variable:"
Write-Host "   - VITE_API_BASE_URL: $BACKEND_URL"
Write-Host "6. Deploy"
Write-Host ""

Write-Host "Step 3: Configure Custom Domains" -ForegroundColor Yellow
Write-Host "For each app, go to Domain Management and add:"
Write-Host "  - Operator: $OPERATOR_DOMAIN"
Write-Host "  - User: $USER_DOMAIN"
Write-Host ""

Write-Host "Deployment instructions complete!" -ForegroundColor Green
Write-Host ""
Write-Host "After deploying both apps, run:"
Write-Host "  .\scripts\setup_route53_domains.ps1"





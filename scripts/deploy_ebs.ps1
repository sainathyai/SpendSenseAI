# Deploy SpendSenseAI to AWS Elastic Beanstalk (PowerShell)

$ErrorActionPreference = "Stop"

# Configuration
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$APP_NAME = "spendsenseai"
$ENV_NAME = "$APP_NAME-env"
$PLATFORM = "Python 3.11"
$INSTANCE_TYPE = "t3.small"

Write-Host "Starting Elastic Beanstalk Deployment" -ForegroundColor Green
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Check EB CLI
if (-not (Get-Command eb -ErrorAction SilentlyContinue)) {
    Write-Host "EB CLI not found. Installing..." -ForegroundColor Yellow
    pip install awsebcli
}

# Check if logged in
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "ERROR: Not logged into AWS" -ForegroundColor Red
    exit 1
}

Write-Host "SUCCESS: AWS CLI configured" -ForegroundColor Green

# Initialize EB if not already done
if (-not (Test-Path ".elasticbeanstalk\config.yml")) {
    Write-Host ""
    Write-Host "Initializing Elastic Beanstalk..." -ForegroundColor Yellow
    eb init -p $PLATFORM -r $AWS_REGION $APP_NAME --region $AWS_REGION
} else {
    Write-Host "Elastic Beanstalk already initialized" -ForegroundColor Green
}

# Create environment if it doesn't exist
Write-Host ""
Write-Host "Checking environment..." -ForegroundColor Yellow
$ENV_EXISTS = $false
try {
    $STATUS_OUTPUT = eb status $ENV_NAME 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ENV_EXISTS = $true
    }
} catch {
    $ENV_EXISTS = $false
}

if (-not $ENV_EXISTS) {
    Write-Host "Creating environment: $ENV_NAME" -ForegroundColor Yellow
    eb create $ENV_NAME `
        --instance-type $INSTANCE_TYPE `
        --platform $PLATFORM `
        --region $AWS_REGION `
        --envvars "SPENDSENSE_DB_PATH=/var/app/data/spendsense.db,ENABLE_LLM=true,USE_AWS_SECRETS=true,AWS_REGION=$AWS_REGION"
} else {
    Write-Host "Environment exists: $ENV_NAME" -ForegroundColor Green
}

# Deploy
Write-Host ""
Write-Host "Deploying application..." -ForegroundColor Yellow
eb deploy $ENV_NAME

# Get URL
Write-Host ""
Write-Host "Getting application URL..." -ForegroundColor Green
try {
    $STATUS = eb status $ENV_NAME
    $CNAME_LINE = $STATUS | Select-String "CNAME"
    if ($CNAME_LINE) {
        $APP_URL = ($CNAME_LINE.ToString() -split ":")[1].Trim()
        Write-Host "Application URL: https://$APP_URL" -ForegroundColor Green
    } else {
        Write-Host "Environment is still deploying. Check status with: eb status $ENV_NAME" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not get URL. Check status with: eb status $ENV_NAME" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Update frontend VITE_API_BASE_URL to: https://$APP_URL"
Write-Host "2. Deploy frontend to Amplify"


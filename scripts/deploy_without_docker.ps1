# AWS Deployment Script for SpendSenseAI (Without Local Docker)
# Uses AWS CodeBuild to build Docker image

$ErrorActionPreference = "Stop"

# Configuration
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$APP_NAME = "spendsenseai"
$BACKEND_SERVICE_NAME = "$APP_NAME-backend"
$ACCOUNT_ID = "971422717446"

Write-Host "Starting AWS Deployment for SpendSenseAI (Using CodeBuild)" -ForegroundColor Green
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if logged in
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "ERROR: Not logged into AWS. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "SUCCESS: AWS CLI configured" -ForegroundColor Green

# Step 1: Create ECR repository
Write-Host ""
Write-Host "Step 1: Setting up ECR repository..." -ForegroundColor Yellow
$ECR_REPO_NAME = "$APP_NAME-backend"

try {
    $ECR_REPO_URI = aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty repositories | Select-Object -First 1 -ExpandProperty repositoryUri
} catch {
    $ECR_REPO_URI = $null
}

if (-not $ECR_REPO_URI) {
    Write-Host "Creating ECR repository..."
    $ECR_REPO_URI = (aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION | ConvertFrom-Json).repository.repositoryUri
    Write-Host "SUCCESS: Created ECR repository: $ECR_REPO_URI" -ForegroundColor Green
} else {
    Write-Host "SUCCESS: ECR repository exists: $ECR_REPO_URI" -ForegroundColor Green
}

# Step 2: Create CodeBuild project
Write-Host ""
Write-Host "Step 2: Setting up AWS CodeBuild..." -ForegroundColor Yellow

$CODEBUILD_PROJECT_NAME = "$APP_NAME-build"

# Create buildspec.yml if it doesn't exist
if (-not (Test-Path "buildspec.yml")) {
    $BUILDSPEC = @"
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $ECR_REPO_NAME .
      - docker tag $ECR_REPO_NAME`:latest $ECR_REPO_URI`:latest
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $ECR_REPO_URI`:latest
"@
    $BUILDSPEC | Out-File -FilePath "buildspec.yml" -Encoding utf8
    Write-Host "Created buildspec.yml" -ForegroundColor Green
}

# Check if CodeBuild project exists
try {
    $PROJECT_EXISTS = aws codebuild batch-get-projects --names $CODEBUILD_PROJECT_NAME --region $AWS_REGION 2>$null | ConvertFrom-Json
} catch {
    $PROJECT_EXISTS = $null
}

if (-not $PROJECT_EXISTS) {
    Write-Host "Creating CodeBuild project..."
    
    # Create IAM role for CodeBuild (if needed)
    $CODEBUILD_ROLE_NAME = "$APP_NAME-codebuild-role"
    
    # Create CodeBuild project
    $PROJECT_CONFIG = @{
        name = $CODEBUILD_PROJECT_NAME
        description = "Build Docker image for SpendSenseAI backend"
        source = @{
            type = "S3"
            location = "s3://$APP_NAME-source/build.zip"
        }
        artifacts = @{
            type = "NO_ARTIFACTS"
        }
        environment = @{
            type = "LINUX_CONTAINER"
            image = "aws/codebuild/standard:7.0"
            computeType = "BUILD_GENERAL1_SMALL"
            privilegedMode = $true
        }
        serviceRole = "arn:aws:iam::$ACCOUNT_ID`:role/$CODEBUILD_ROLE_NAME"
    } | ConvertTo-Json -Depth 10
    
    Write-Host "WARNING: CodeBuild setup requires manual configuration." -ForegroundColor Yellow
    Write-Host "Please use AWS Console to create CodeBuild project or install Docker Desktop." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "RECOMMENDATION: Install Docker Desktop for easier deployment" -ForegroundColor Yellow
Write-Host "Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
Write-Host ""
Write-Host "After installing Docker, run: .\scripts\deploy_aws.ps1" -ForegroundColor Green


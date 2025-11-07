# AWS Deployment Script for SpendSenseAI (PowerShell)
# Deploys backend to App Runner and frontend to Amplify

$ErrorActionPreference = "Stop"

# Configuration
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$APP_NAME = "spendsenseai"
$BACKEND_SERVICE_NAME = "$APP_NAME-backend"
$FRONTEND_APP_NAME = "$APP_NAME-frontend"

Write-Host "Starting AWS Deployment for SpendSenseAI" -ForegroundColor Green
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

# Step 2: Build and push Docker image
Write-Host ""
Write-Host "Step 2: Building and pushing Docker image..." -ForegroundColor Yellow

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker not found. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

$ECR_LOGIN = aws ecr get-login-password --region $AWS_REGION
$ECR_REPO_DOMAIN = ($ECR_REPO_URI -split '/')[0]
$ECR_LOGIN | docker login --username AWS --password-stdin $ECR_REPO_DOMAIN

$IMAGE_TAG = "latest"
$FULL_IMAGE_URI = "$ECR_REPO_URI`:$IMAGE_TAG"

Write-Host "Building Docker image..."
docker build -t "$APP_NAME-backend" .
docker tag "$APP_NAME-backend`:latest" $FULL_IMAGE_URI

Write-Host "Pushing to ECR..."
docker push $FULL_IMAGE_URI
Write-Host "SUCCESS: Docker image pushed: $FULL_IMAGE_URI" -ForegroundColor Green

# Step 3: Create App Runner service
Write-Host ""
Write-Host "Step 3: Deploying to AWS App Runner..." -ForegroundColor Yellow

# Check if service exists
try {
    $SERVICE_ARN = (aws apprunner list-services --region $AWS_REGION | ConvertFrom-Json).ServiceSummaryList | Where-Object { $_.ServiceName -eq $BACKEND_SERVICE_NAME } | Select-Object -First 1 -ExpandProperty ServiceArn
} catch {
    $SERVICE_ARN = $null
}

if (-not $SERVICE_ARN) {
    Write-Host "Creating App Runner service..."
    
    $CONFIG = @{
        ServiceName = $BACKEND_SERVICE_NAME
        SourceConfiguration = @{
            ImageRepository = @{
                ImageIdentifier = $FULL_IMAGE_URI
                ImageConfiguration = @{
                    Port = "8000"
                    RuntimeEnvironmentVariables = @{
                        SPENDSENSE_DB_PATH = "/app/data/spendsense.db"
                        ENABLE_LLM = "true"
                        USE_AWS_SECRETS = "true"
                        AWS_REGION = $AWS_REGION
                    }
                }
                ImageRepositoryType = "ECR"
            }
            AutoDeploymentsEnabled = $true
        }
        InstanceConfiguration = @{
            Cpu = "1 vCPU"
            Memory = "2 GB"
            InstanceRoleArn = "arn:aws:iam::971422717446:role/sainathyai-application-role"
        }
        HealthCheckConfiguration = @{
            Protocol = "HTTP"
            Path = "/health"
            Interval = 10
            Timeout = 5
            HealthyThreshold = 1
            UnhealthyThreshold = 5
        }
    } | ConvertTo-Json -Depth 10
    
    $CONFIG | Out-File -FilePath "$env:TEMP\apprunner-config.json" -Encoding utf8
    
    $SERVICE_ARN = (aws apprunner create-service --service-name $BACKEND_SERVICE_NAME --source-configuration "file://$env:TEMP\apprunner-config.json" --region $AWS_REGION | ConvertFrom-Json).Service.ServiceArn
    
    Write-Host "SUCCESS: Created App Runner service: $SERVICE_ARN" -ForegroundColor Green
} else {
    Write-Host "Service exists, updating..."
    
    $UPDATE_CONFIG = @{
        ImageIdentifier = $FULL_IMAGE_URI
    } | ConvertTo-Json -Depth 5
    
    $UPDATE_CONFIG | Out-File -FilePath "$env:TEMP\apprunner-update.json" -Encoding utf8
    
    aws apprunner update-service --service-arn $SERVICE_ARN --source-configuration "file://$env:TEMP\apprunner-update.json" --region $AWS_REGION | Out-Null
    
    Write-Host "SUCCESS: Updated App Runner service" -ForegroundColor Green
}

# Get service URL
Start-Sleep -Seconds 5
$SERVICE_URL = (aws apprunner describe-service --service-arn $SERVICE_ARN --region $AWS_REGION | ConvertFrom-Json).Service.ServiceUrl
Write-Host "SUCCESS: Backend URL: $SERVICE_URL" -ForegroundColor Green

# Step 4: Frontend deployment instructions
Write-Host ""
Write-Host "Step 4: Deploying frontend to AWS Amplify..." -ForegroundColor Yellow
Write-Host "Note: Amplify deployment is best done via AWS Console or Amplify CLI" -ForegroundColor Yellow
Write-Host ""
Write-Host "To deploy frontend:"
Write-Host "1. Go to AWS Amplify Console"
Write-Host "2. Connect your GitHub repository"
Write-Host "3. Set build settings:"
Write-Host "   - Base directory: frontend"
Write-Host "   - Build command: npm run build"
Write-Host "   - Output directory: dist"
Write-Host ""
Write-Host "Or use Amplify CLI:"
Write-Host "  amplify init"
Write-Host "  amplify add hosting"
Write-Host "  amplify publish"

Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Green
Write-Host "  Backend URL: $SERVICE_URL"
Write-Host "  Frontend: Deploy via Amplify Console/CLI"
Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green


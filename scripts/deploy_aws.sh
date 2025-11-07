#!/bin/bash
# AWS Deployment Script for SpendSenseAI
# Deploys backend to App Runner and frontend to Amplify

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
APP_NAME="spendsenseai"
BACKEND_SERVICE_NAME="${APP_NAME}-backend"
FRONTEND_APP_NAME="${APP_NAME}-frontend"

echo -e "${GREEN}🚀 Starting AWS Deployment for SpendSenseAI${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Not logged into AWS. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"

# Step 1: Create ECR repository for Docker image
echo ""
echo -e "${YELLOW}📦 Step 1: Setting up ECR repository...${NC}"
ECR_REPO_NAME="${APP_NAME}-backend"
ECR_REPO_URI=$(aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null | jq -r '.repositories[0].repositoryUri' || echo "")

if [ -z "$ECR_REPO_URI" ]; then
    echo "Creating ECR repository..."
    ECR_REPO_URI=$(aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION | jq -r '.repository.repositoryUri')
    echo -e "${GREEN}✅ Created ECR repository: $ECR_REPO_URI${NC}"
else
    echo -e "${GREEN}✅ ECR repository exists: $ECR_REPO_URI${NC}"
fi

# Step 2: Build and push Docker image
echo ""
echo -e "${YELLOW}🐳 Step 2: Building and pushing Docker image...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

IMAGE_TAG="latest"
FULL_IMAGE_URI="${ECR_REPO_URI}:${IMAGE_TAG}"

echo "Building Docker image..."
docker build -t $APP_NAME-backend .
docker tag $APP_NAME-backend:latest $FULL_IMAGE_URI

echo "Pushing to ECR..."
docker push $FULL_IMAGE_URI
echo -e "${GREEN}✅ Docker image pushed: $FULL_IMAGE_URI${NC}"

# Step 3: Create App Runner service
echo ""
echo -e "${YELLOW}🚀 Step 3: Deploying to AWS App Runner...${NC}"

# Check if service exists
SERVICE_EXISTS=$(aws apprunner list-services --region $AWS_REGION 2>/dev/null | jq -r ".ServiceSummaryList[] | select(.ServiceName == \"$BACKEND_SERVICE_NAME\") | .ServiceArn" || echo "")

if [ -z "$SERVICE_EXISTS" ]; then
    echo "Creating App Runner service..."
    
    # Create service configuration
    cat > /tmp/apprunner-config.json <<EOF
{
  "ServiceName": "$BACKEND_SERVICE_NAME",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "$FULL_IMAGE_URI",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "SPENDSENSE_DB_PATH": "/app/data/spendsense.db",
          "ENABLE_LLM": "true",
          "USE_AWS_SECRETS": "true",
          "AWS_REGION": "$AWS_REGION"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": "arn:aws:iam::971422717446:role/sainathyai-application-role"
  },
  "HealthCheckConfiguration": {
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }
}
EOF

    SERVICE_ARN=$(aws apprunner create-service \
        --service-name $BACKEND_SERVICE_NAME \
        --source-configuration file:///tmp/apprunner-config.json \
        --region $AWS_REGION \
        | jq -r '.Service.ServiceArn')
    
    echo -e "${GREEN}✅ Created App Runner service: $SERVICE_ARN${NC}"
else
    echo "Service exists, updating..."
    SERVICE_ARN=$SERVICE_EXISTS
    
    # Update service
    cat > /tmp/apprunner-update.json <<EOF
{
  "ImageIdentifier": "$FULL_IMAGE_URI"
}
EOF

    aws apprunner update-service \
        --service-arn $SERVICE_ARN \
        --source-configuration file:///tmp/apprunner-update.json \
        --region $AWS_REGION > /dev/null
    
    echo -e "${GREEN}✅ Updated App Runner service${NC}"
fi

# Get service URL
sleep 5
SERVICE_URL=$(aws apprunner describe-service --service-arn $SERVICE_ARN --region $AWS_REGION | jq -r '.Service.ServiceUrl')
echo -e "${GREEN}✅ Backend URL: $SERVICE_URL${NC}"

# Step 4: Deploy frontend to Amplify
echo ""
echo -e "${YELLOW}🌐 Step 4: Deploying frontend to AWS Amplify...${NC}"
echo -e "${YELLOW}Note: Amplify deployment is best done via AWS Console or Amplify CLI${NC}"
echo ""
echo "To deploy frontend:"
echo "1. Go to AWS Amplify Console"
echo "2. Connect your GitHub repository"
echo "3. Set build settings:"
echo "   - Base directory: frontend"
echo "   - Build command: npm run build"
echo "   - Output directory: dist"
echo ""
echo "Or use Amplify CLI:"
echo "  amplify init"
echo "  amplify add hosting"
echo "  amplify publish"

echo ""
echo -e "${GREEN}✅ Deployment Summary:${NC}"
echo "  Backend URL: $SERVICE_URL"
echo "  Frontend: Deploy via Amplify Console/CLI"
echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"


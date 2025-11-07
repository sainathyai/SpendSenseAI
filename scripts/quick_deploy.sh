#!/bin/bash
# Quick deployment script - simplified version

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
APP_NAME="spendsenseai"
ECR_REPO_NAME="${APP_NAME}-backend"

echo "🚀 Quick Deploy to AWS"
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

# Create ECR repo if needed
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

# Build and push
echo "Building Docker image..."
docker build -t $APP_NAME-backend .
docker tag $APP_NAME-backend:latest ${ECR_REPO_URI}:latest
docker push ${ECR_REPO_URI}:latest

echo "✅ Image pushed: ${ECR_REPO_URI}:latest"
echo ""
echo "Next steps:"
echo "1. Update apprunner-config.json with image URI: ${ECR_REPO_URI}:latest"
echo "2. Run: aws apprunner create-service --service-name ${APP_NAME}-backend --source-configuration file://apprunner-config.json --region $AWS_REGION"


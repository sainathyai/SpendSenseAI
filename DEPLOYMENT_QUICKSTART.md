# Quick Deployment Guide - AWS CLI

Deploy SpendSenseAI to AWS in 3 steps using CLI.

## Prerequisites

```bash
# Install AWS CLI
aws --version  # Should be 2.x

# Configure AWS
aws configure
# Enter: Access Key ID, Secret Key, Region (us-east-1), Output (json)

# Install Docker
docker --version

# Install jq (for JSON parsing)
# Mac: brew install jq
# Linux: sudo apt-get install jq
```

## Step 1: Deploy Backend (App Runner)

### Option A: Use Deployment Script (Recommended)

**Linux/Mac:**
```bash
chmod +x scripts/deploy_aws.sh
./scripts/deploy_aws.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy_aws.ps1
```

### Option B: Manual Steps

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name spendsenseai-backend --region us-east-1

# 2. Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# 3. Build and push Docker image
docker build -t spendsenseai-backend .
docker tag spendsenseai-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/spendsenseai-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/spendsenseai-backend:latest

# 4. Create App Runner service
# Update apprunner-config.json with your ECR image URI
aws apprunner create-service \
  --service-name spendsenseai-backend \
  --source-configuration file://apprunner-config.json \
  --region us-east-1

# 5. Get service URL
aws apprunner describe-service \
  --service-name spendsenseai-backend \
  --region us-east-1 \
  --query 'Service.ServiceUrl' \
  --output text
```

**Save the backend URL** - you'll need it for frontend configuration.

## Step 2: Deploy Frontend (Amplify)

### Option A: AWS Console (Easiest)

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)
2. Click "New app" → "Host web app"
3. Select "GitHub" and authorize
4. Choose your repository: `sainathyai/SpendSenseAI`
5. Configure build settings:
   - **App name**: `spendsenseai-frontend`
   - **Branch**: `phase3-advanced-features`
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build`
   - **Output directory**: `dist`
6. Add environment variables:
   - `VITE_API_BASE_URL`: `https://<your-apprunner-url>.awsapprunner.com`
7. Click "Save and deploy"

### Option B: Amplify CLI

```bash
cd frontend

# Install Amplify CLI if needed
npm install -g @aws-amplify/cli

# Initialize
amplify init

# Add hosting
amplify add hosting

# Set environment variable
amplify env add
# Add: VITE_API_BASE_URL=https://<your-apprunner-url>.awsapprunner.com

# Deploy
amplify publish
```

## Step 3: Configure Database

For demo, include database in Docker image:

```bash
# Copy database to data/ directory
cp data/spendsense.db data/

# Rebuild and push Docker image
docker build -t spendsenseai-backend .
docker tag spendsenseai-backend:latest <ecr-uri>:latest
docker push <ecr-uri>:latest

# Update App Runner service
aws apprunner update-service \
  --service-name spendsenseai-backend \
  --source-configuration '{"ImageRepository":{"ImageIdentifier":"<ecr-uri>:latest"}}' \
  --region us-east-1
```

## Step 4: Verify Deployment

```bash
# Check backend health
curl https://<apprunner-url>/health

# Check frontend
# Visit Amplify URL in browser
```

## Troubleshooting

### Backend Issues
```bash
# View App Runner logs
aws apprunner describe-service \
  --service-name spendsenseai-backend \
  --region us-east-1 \
  --query 'Service.Status' \
  --output text

# Check service events
aws apprunner list-operations \
  --service-arn <service-arn> \
  --region us-east-1
```

### Frontend Issues
- Check Amplify build logs in console
- Verify `VITE_API_BASE_URL` is set correctly
- Check browser console for CORS errors

## Cost Estimate

- **App Runner**: ~$10-15/month (1 vCPU, 2GB RAM)
- **Amplify**: Free tier (100 GB/month)
- **ECR**: ~$0.10/month
- **Secrets Manager**: ~$0.40/month
- **Total**: ~$10-15/month

## Cleanup

```bash
# Delete App Runner service
aws apprunner delete-service \
  --service-arn <service-arn> \
  --region us-east-1

# Delete ECR repository
aws ecr delete-repository \
  --repository-name spendsenseai-backend \
  --force \
  --region us-east-1

# Delete Amplify app (via console)
```


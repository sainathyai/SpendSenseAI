# AWS Deployment Guide for SpendSenseAI

This guide walks you through deploying SpendSenseAI on AWS using the recommended tech stack.

## Architecture

- **Frontend**: AWS Amplify (React apps)
- **Backend**: AWS App Runner (FastAPI)
- **Database**: SQLite on EBS volume (for demo)
- **Secrets**: AWS Secrets Manager (OpenAI API key)

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Docker** installed (for building backend image)
4. **Node.js** and npm (for frontend)
5. **Amplify CLI** (optional, for frontend deployment)

## Quick Start

### 1. Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
```

### 2. Deploy Backend (App Runner)

**On Linux/Mac:**
```bash
chmod +x scripts/deploy_aws.sh
./scripts/deploy_aws.sh
```

**On Windows (PowerShell):**
```powershell
.\scripts\deploy_aws.ps1
```

This script will:
- Create ECR repository
- Build and push Docker image
- Create/update App Runner service
- Output the backend URL

### 3. Deploy Frontend (Amplify)

**Option A: Using AWS Console (Recommended)**
1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)
2. Click "New app" → "Host web app"
3. Connect your GitHub repository
4. Configure build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build`
   - **Output directory**: `dist`
5. Add environment variables:
   - `VITE_API_BASE_URL`: Your App Runner service URL
6. Deploy

**Option B: Using Amplify CLI**
```bash
cd frontend
amplify init
amplify add hosting
amplify publish
```

### 4. Configure Environment Variables

**Backend (App Runner):**
- `SPENDSENSE_DB_PATH`: `/app/data/spendsense.db`
- `ENABLE_LLM`: `true`
- `USE_AWS_SECRETS`: `true`
- `AWS_REGION`: `us-east-1`

**Frontend (Amplify):**
- `VITE_API_BASE_URL`: Your App Runner service URL (e.g., `https://xxxxx.us-east-1.awsapprunner.com`)

## Database Setup

For demo purposes, SQLite database can be:
1. **Included in Docker image** (for quick demo)
2. **Mounted from S3** (for persistence)
3. **On EBS volume** (for production-like setup)

To include database in Docker image:
```bash
# Copy database to data/ directory before building
cp data/spendsense.db data/
docker build -t spendsense-backend .
```

## Secrets Management

OpenAI API key should be stored in AWS Secrets Manager:
1. Go to AWS Secrets Manager
2. Create secret: `openai/sainathyai`
3. Store your OpenAI API key
4. App Runner will use IAM role to access it

## Cost Estimation

**Monthly costs (demo):**
- App Runner: ~$10-15/month (1 vCPU, 2GB RAM)
- Amplify: Free tier (100 GB bandwidth/month)
- Secrets Manager: ~$0.40/month
- ECR: ~$0.10/month (storage)
- **Total: ~$10-15/month**

## Troubleshooting

### Backend not starting
- Check App Runner logs: `aws apprunner describe-service --service-arn <arn>`
- Verify environment variables
- Check IAM role permissions

### Frontend can't connect to backend
- Verify `VITE_API_BASE_URL` is set correctly
- Check CORS settings in backend
- Verify App Runner service is running

### Database not found
- Ensure database file is included in Docker image
- Or mount from S3/EBS volume

## Manual Deployment Steps

If scripts don't work, follow these manual steps:

### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name spendsenseai-backend --region us-east-1
```

### 2. Build and Push Docker Image
```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t spendsenseai-backend .

# Tag image
docker tag spendsenseai-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/spendsenseai-backend:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/spendsenseai-backend:latest
```

### 3. Create App Runner Service
```bash
aws apprunner create-service \
  --service-name spendsenseai-backend \
  --source-configuration file://apprunner-config.json \
  --region us-east-1
```

## Next Steps

1. Set up custom domain (optional)
2. Configure auto-scaling
3. Set up monitoring/alerting
4. Migrate to RDS PostgreSQL (for production)


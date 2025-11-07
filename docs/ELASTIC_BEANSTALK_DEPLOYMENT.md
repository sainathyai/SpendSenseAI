# Elastic Beanstalk Deployment Guide

Deploy SpendSenseAI to AWS Elastic Beanstalk without Docker.

## Prerequisites

1. **AWS CLI** installed and configured
2. **EB CLI** (Elastic Beanstalk CLI) - will be installed automatically
3. **Python 3.11** (for local development)

## Quick Start

### 1. Install EB CLI (if needed)

```bash
pip install awsebcli
```

### 2. Deploy

**Linux/Mac:**
```bash
chmod +x scripts/deploy_ebs.sh
./scripts/deploy_ebs.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy_ebs.ps1
```

## Manual Deployment Steps

### 1. Initialize Elastic Beanstalk

```bash
eb init -p "Python 3.11" -r us-east-1 spendsenseai
```

This will:
- Create `.elasticbeanstalk/` directory
- Configure your EB application
- Set up default settings

### 2. Create Environment

```bash
eb create spendsenseai-env \
    --instance-type t3.small \
    --platform "Python 3.11" \
    --envvars SPENDSENSE_DB_PATH=/var/app/data/spendsense.db,ENABLE_LLM=true,USE_AWS_SECRETS=true,AWS_REGION=us-east-1
```

### 3. Deploy Application

```bash
eb deploy spendsenseai-env
```

### 4. Get Application URL

```bash
eb status
# Look for "CNAME" - that's your application URL
```

## Configuration Files

### `.ebextensions/01_python.config`
- Configures Python environment
- Sets environment variables
- Configures health checks

### `.ebextensions/02_setup.config`
- Creates data directory
- Copies database file on deployment

### `.ebextensions/03_nginx.config`
- Configures Nginx proxy settings
- Sets timeouts and body size limits

### `application.py`
- Entry point for Elastic Beanstalk
- Exposes `application` variable (WSGI requirement)

### `Procfile`
- Defines how to run the application
- Uses uvicorn to serve FastAPI

### `.ebignore`
- Similar to `.gitignore`
- Excludes unnecessary files from deployment

## Environment Variables

Set via EB CLI:
```bash
eb setenv SPENDSENSE_DB_PATH=/var/app/data/spendsense.db ENABLE_LLM=true USE_AWS_SECRETS=true AWS_REGION=us-east-1
```

Or in `.ebextensions/01_python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    SPENDSENSE_DB_PATH: /var/app/data/spendsense.db
    ENABLE_LLM: "true"
    USE_AWS_SECRETS: "true"
    AWS_REGION: us-east-1
```

## Database Setup

### Option 1: Include in Deployment

1. Copy database to `data/` directory:
```bash
cp data/spendsense.db data/
```

2. Deploy - the `.ebextensions/02_setup.config` will copy it to `/var/app/data/`

### Option 2: Use S3

1. Upload database to S3:
```bash
aws s3 cp data/spendsense.db s3://your-bucket/spendsense.db
```

2. Download on deployment using `.ebextensions` hook

### Option 3: Use RDS (Production)

1. Create RDS PostgreSQL instance
2. Migrate data from SQLite
3. Update connection string in environment variables

## Useful Commands

```bash
# View logs
eb logs

# SSH into instance
eb ssh

# Check status
eb status

# View health
eb health

# Open in browser
eb open

# Terminate environment
eb terminate spendsenseai-env
```

## Troubleshooting

### Application not starting
```bash
# Check logs
eb logs

# Check environment variables
eb printenv

# SSH and check manually
eb ssh
```

### Database not found
- Ensure database is in `data/` directory
- Check `/var/app/data/` on instance
- Verify `.ebextensions/02_setup.config` is working

### Health check failing
- Verify `/health` endpoint works locally
- Check health check configuration in `.ebextensions/01_python.config`
- Review application logs

## Cost Estimate

- **t3.small** instance: ~$15/month
- **Load balancer**: ~$16/month (if enabled)
- **Total**: ~$15-31/month

## Next Steps

1. Deploy frontend to Amplify
2. Set `VITE_API_BASE_URL` to your EB URL
3. Configure custom domain (optional)
4. Set up monitoring/alerting





# Route53 and Frontend Deployment Guide

This guide walks you through setting up Route53 DNS records and deploying the frontend to AWS Amplify.

## Prerequisites

1. **AWS CLI** installed and configured
2. **AWS Account** with appropriate permissions:
   - Route53 (read/write)
   - Amplify (read/write)
   - IAM permissions for domain associations
3. **Hosted Zone** already created in Route53 for `sainathyai.com`
4. **Amplify Apps** already created (or use `create_amplify_apps.ps1` first)

## Quick Start

### Windows (PowerShell)

```powershell
.\scripts\deploy_frontend_with_route53.ps1
```

### Linux/Mac (Bash)

```bash
chmod +x scripts/deploy_frontend_with_route53.sh
./scripts/deploy_frontend_with_route53.sh
```

## What the Script Does

1. **Verifies Route53 Hosted Zone** - Checks that the hosted zone exists
2. **Verifies Amplify Apps** - Checks that both Operator and User apps exist
3. **Associates Custom Domains** - Links custom domains to Amplify apps:
   - `admin.spendsenseai.sainathyai.com` → Operator Dashboard
   - `user.spendsenseai.sainathyai.com` → User Dashboard
4. **Creates Route53 DNS Records** - Creates CNAME records pointing to Amplify
5. **Configures Environment Variables** - Sets `VITE_API_BASE_URL` for both apps

## Configuration

The script uses these default values (can be overridden with environment variables):

- **Backend URL**: `https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com`
- **Root Domain**: `sainathyai.com`
- **Operator Domain**: `admin.spendsenseai.sainathyai.com`
- **User Domain**: `user.spendsenseai.sainathyai.com`
- **Hosted Zone ID**: `Z0882306KADD7M9CEUFD`
- **Region**: `us-east-1`
- **Operator App ID**: `dvukd3zjye01u`
- **User App ID**: `d2yncedb4tyu2y`

### Override Backend URL

```powershell
$env:BACKEND_URL = "https://your-backend-url.com"
.\scripts\deploy_frontend_with_route53.ps1
```

```bash
export BACKEND_URL="https://your-backend-url.com"
./scripts/deploy_frontend_with_route53.sh
```

## Manual Steps After Running Script

After running the script, you need to complete these steps in the AWS Amplify Console:

### 1. Connect GitHub Repository

For each app (Operator and User):

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)
2. Select the app
3. Go to "App settings" → "General"
4. Click "Edit" under "Repository"
5. Connect your GitHub repository: `sainathyai/SpendSenseAI`
6. Select branch: `main` (or your deployment branch)

### 2. Configure Build Settings

#### Operator Dashboard (`dvukd3zjye01u`)

1. Go to "App settings" → "Build settings"
2. Click "Edit"
3. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build:operator`
   - **Output directory**: `dist`
   - **Build spec file**: `frontend/amplify-operator.yml` (or use the YAML below)

**Build spec (amplify-operator.yml):**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build:operator
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

#### User Dashboard (`d2yncedb4tyu2y`)

1. Go to "App settings" → "Build settings"
2. Click "Edit"
3. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build:user`
   - **Output directory**: `dist-user`
   - **Build spec file**: `frontend/amplify-user.yml` (or use the YAML below)

**Build spec (amplify-user.yml):**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build:user
  artifacts:
    baseDirectory: dist-user
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

### 3. Set Environment Variables

For each app, set:

- **Key**: `VITE_API_BASE_URL`
- **Value**: `https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com`

1. Go to "App settings" → "Environment variables"
2. Click "Manage variables"
3. Add `VITE_API_BASE_URL` with your backend URL
4. Save

### 4. Deploy

Amplify will automatically deploy when you:
- Push to the connected branch
- Or manually trigger deployment in the Amplify Console

To manually trigger:
1. Go to the app in Amplify Console
2. Click "Redeploy this version" or "Deploy" (if first time)

## Verify Deployment

### Check DNS Records

```bash
# Check Operator Dashboard DNS
dig admin.spendsenseai.sainathyai.com

# Check User Dashboard DNS
dig user.spendsenseai.sainathyai.com
```

Or use online tools:
- [DNS Checker](https://dnschecker.org/)
- [What's My DNS](https://www.whatsmydns.net/)

### Test URLs

After DNS propagation (5-15 minutes):

- **Operator Dashboard**: https://admin.spendsenseai.sainathyai.com
- **User Dashboard**: https://user.spendsenseai.sainathyai.com
- **Backend API**: https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com

### Check Amplify Deployment Status

```bash
# Operator Dashboard
aws amplify get-app --app-id dvukd3zjye01u --region us-east-1

# User Dashboard
aws amplify get-app --app-id d2yncedb4tyu2y --region us-east-1
```

## Troubleshooting

### DNS Not Resolving

1. **Wait 5-15 minutes** for DNS propagation
2. **Verify Route53 records**:
   ```bash
   aws route53 list-resource-record-sets \
       --hosted-zone-id Z0882306KADD7M9CEUFD \
       --query "ResourceRecordSets[?Name=='admin.spendsenseai.sainathyai.com.']"
   ```
3. **Check domain association status**:
   ```bash
   aws amplify get-domain-association \
       --app-id dvukd3zjye01u \
       --domain-name admin.spendsenseai.sainathyai.com \
       --region us-east-1
   ```

### Build Failures

1. **Check build logs** in Amplify Console
2. **Verify build settings** match the configuration above
3. **Check environment variables** are set correctly
4. **Verify package.json** has the correct build scripts:
   - `build:operator` for Operator Dashboard
   - `build:user` for User Dashboard

### Domain Association Fails

1. **Verify domain ownership** - Make sure you own `sainathyai.com`
2. **Check Route53 hosted zone** - Ensure it exists and is configured correctly
3. **Verify Amplify app IDs** - Make sure the app IDs are correct
4. **Check IAM permissions** - Ensure you have permissions to create domain associations

### Environment Variables Not Working

1. **Verify variable name** - Must be `VITE_API_BASE_URL` (Vite prefix is required)
2. **Check build logs** - Environment variables are injected at build time
3. **Redeploy** - After changing environment variables, trigger a new deployment

## Next Steps

1. ✅ Route53 DNS records created
2. ✅ Custom domains associated with Amplify apps
3. ✅ Environment variables configured
4. ⏳ Connect GitHub repositories
5. ⏳ Configure build settings
6. ⏳ Deploy frontend apps
7. ⏳ Verify DNS propagation
8. ⏳ Test frontend URLs

## Related Scripts

- `scripts/create_amplify_apps.ps1` - Create Amplify apps if they don't exist
- `scripts/setup_route53_records.ps1` - Just set up Route53 records (if domains already associated)
- `scripts/deploy_frontend_amplify.ps1` - Frontend deployment instructions (manual)

## References

- [AWS Amplify Documentation](https://docs.aws.amazon.com/amplify/)
- [Route53 Documentation](https://docs.aws.amazon.com/route53/)
- [Amplify Custom Domains](https://docs.aws.amazon.com/amplify/latest/userguide/custom-domains.html)




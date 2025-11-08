# Quick Frontend Deployment Guide

## Run the Deployment Script

### Option 1: Simple Script (Recommended)
```powershell
.\scripts\deploy_amplify_simple.ps1
```

### Option 2: Full Script
```powershell
.\scripts\deploy_frontend_with_route53.ps1
```

## Manual Steps (If Script Fails)

### 1. Set up Route53 DNS Records

#### Get Amplify CNAMEs

**Operator Dashboard:**
```powershell
aws amplify get-domain-association --app-id dvukd3zjye01u --domain-name admin.spendsenseai.sainathyai.com --region us-east-1
```

**User Dashboard:**
```powershell
aws amplify get-domain-association --app-id d2yncedb4tyu2y --domain-name user.spendsenseai.sainathyai.com --region us-east-1
```

#### Create Route53 Records

Create a JSON file for each domain:

**operator-route53.json:**
```json
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "admin.spendsenseai.sainathyai.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "YOUR_OPERATOR_CNAME_HERE"
          }
        ]
      }
    }
  ]
}
```

**user-route53.json:**
```json
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "user.spendsenseai.sainathyai.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "YOUR_USER_CNAME_HERE"
          }
        ]
      }
    }
  ]
}
```

**Apply the records:**
```powershell
aws route53 change-resource-record-sets --hosted-zone-id Z0882306KADD7M9CEUFD --change-batch file://operator-route53.json
aws route53 change-resource-record-sets --hosted-zone-id Z0882306KADD7M9CEUFD --change-batch file://user-route53.json
```

### 2. Configure Amplify Apps

#### Update Environment Variables

**Operator App:**
```powershell
aws amplify update-app --app-id dvukd3zjye01u --environment-variables "VITE_API_BASE_URL=https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com" --region us-east-1
```

**User App:**
```powershell
aws amplify update-app --app-id d2yncedb4tyu2y --environment-variables "VITE_API_BASE_URL=https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com" --region us-east-1
```

### 3. Configure Build Settings in Amplify Console

Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)

#### For Operator Dashboard (dvukd3zjye01u):

1. Select the app
2. Go to "App settings" → "Build settings"
3. Click "Edit"
4. Set:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build:operator`
   - **Output directory**: `dist`
   - **Build spec file**: `frontend/amplify-operator.yml`

#### For User Dashboard (d2yncedb4tyu2y):

1. Select the app
2. Go to "App settings" → "Build settings"
3. Click "Edit"
4. Set:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build:user`
   - **Output directory**: `dist-user`
   - **Build spec file**: `frontend/amplify-user.yml`

### 4. Connect GitHub Repository

For each app:
1. Go to "App settings" → "General"
2. Click "Edit" under "Repository"
3. Connect GitHub: `sainathyai/SpendSenseAI`
4. Select branch: `main`

### 5. Deploy

- Push to main branch (auto-deploy)
- Or manually trigger in Amplify Console

## Verify Deployment

```powershell
# Check Operator app
aws amplify get-app --app-id dvukd3zjye01u --region us-east-1

# Check User app
aws amplify get-app --app-id d2yncedb4tyu2y --region us-east-1

# Check domain associations
aws amplify get-domain-association --app-id dvukd3zjye01u --domain-name admin.spendsenseai.sainathyai.com --region us-east-1
aws amplify get-domain-association --app-id d2yncedb4tyu2y --domain-name user.spendsenseai.sainathyai.com --region us-east-1
```

## URLs

- **Operator Dashboard**: https://admin.spendsenseai.sainathyai.com
- **User Dashboard**: https://user.spendsenseai.sainathyai.com
- **Backend API**: https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com



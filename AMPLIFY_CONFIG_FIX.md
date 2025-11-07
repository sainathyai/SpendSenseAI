# Amplify Configuration Issues and Fixes

## Problems Identified

From the Amplify Console, I can see:

1. **Custom domain is on wrong branch**: 
   - Domain `user.spendsenseai.sainathyai.com` is on `phase3-advanced-features` branch
   - Should be on `main` branch

2. **Branches show "No deploys"**:
   - Both `main` and `phase3-advanced-features` branches have no deployments
   - Need to connect GitHub repository and deploy

3. **Main branch not connected**:
   - Main branch is not connected to GitHub repository
   - Needs to be connected to trigger deployments

## Fixes Needed

### 1. Move Domain to Main Branch (Manual in Console)

**For User Dashboard (d2yncedb4tyu2y):**

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)
2. Select app: **spendsenseai-user**
3. Go to **Domain Management**
4. Click on domain: `user.spendsenseai.sainathyai.com`
5. Click **Edit**
6. Change branch from `phase3-advanced-features` to `main`
7. Save

**For Operator Dashboard (dvukd3zjye01u):**

1. Select app: **spendsenseai-operator**
2. Go to **Domain Management**
3. Click on domain: `admin.spendsenseai.sainathyai.com`
4. Click **Edit**
5. Change branch from `phase3-advanced-features` to `main`
6. Save

### 2. Connect GitHub Repository to Main Branch

**For each app:**

1. Go to **App settings** → **General**
2. Under **Repository**, click **Edit**
3. Connect GitHub repository: `sainathyai/SpendSenseAI`
4. Select branch: `main`
5. Save

### 3. Configure Build Settings for Main Branch

**For User Dashboard:**

1. Go to **App settings** → **Build settings**
2. Click **Edit**
3. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build:user`
   - **Output directory**: `dist-user`
   - **Build spec file**: `frontend/amplify-user.yml`
4. Save

**For Operator Dashboard:**

1. Go to **App settings** → **Build settings**
2. Click **Edit**
3. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build:operator`
   - **Output directory**: `dist`
   - **Build spec file**: `frontend/amplify-operator.yml`
4. Save

### 4. Deploy Main Branch

After connecting GitHub and configuring build settings:

1. Go to **Branches** section
2. Click on **main** branch
3. Click **Deploy updates** (or push to main branch in GitHub)
4. Wait for deployment to complete

### 5. Create Route53 Records

After domains are on main branch and deployed:

```powershell
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "scripts\deploy_amplify_simple.ps1"
```

## Current Status

- ✅ Custom domains added
- ✅ Branches exist (main and phase3-advanced-features)
- ❌ Domains on wrong branch (phase3-advanced-features instead of main)
- ❌ GitHub not connected to main branch
- ❌ No deployments on main branch
- ❌ Route53 records not created (waiting for domain CNAMEs)

## After Fixes

Once everything is configured:
- Domains will be on main branch
- Main branch will be connected to GitHub
- Deployments will trigger automatically on push
- Route53 records will point to Amplify
- URLs will work: https://admin.spendsenseai.sainathyai.com and https://user.spendsenseai.sainathyai.com


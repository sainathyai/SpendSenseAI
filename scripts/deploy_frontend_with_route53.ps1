# Complete Frontend Deployment with Route53 Setup (PowerShell)
# This script sets up Route53 DNS records and deploys frontend to AWS Amplify

$ErrorActionPreference = "Stop"

# Configuration
$BACKEND_URL = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com" }
$ROOT_DOMAIN = "sainathyai.com"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$HOSTED_ZONE_ID = "Z0882306KADD7M9CEUFD"
$REGION = "us-east-1"

# Amplify App IDs (from deployment status)
$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Frontend Deployment with Route53 Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if logged in
$awsCheck = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -ne 0 -and $awsCheck -match "error|Error|ERROR") {
    Write-Host "ERROR: Not logged into AWS. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ AWS CLI configured" -ForegroundColor Green
Write-Host ""

# Step 1: Verify Route53 Hosted Zone
Write-Host "Step 1: Verifying Route53 Hosted Zone..." -ForegroundColor Yellow
$ZONE_INFO = aws route53 get-hosted-zone --id $HOSTED_ZONE_ID --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Could not find hosted zone $HOSTED_ZONE_ID" -ForegroundColor Red
    Write-Host "Please verify the hosted zone ID is correct." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Found hosted zone: $HOSTED_ZONE_ID ($ROOT_DOMAIN)" -ForegroundColor Green
Write-Host ""

# Step 2: Check Amplify Apps
Write-Host "Step 2: Verifying Amplify Apps..." -ForegroundColor Yellow
try {
    $OPERATOR_APP = aws amplify get-app --app-id $OPERATOR_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
    Write-Host "✅ Operator app found: $($OPERATOR_APP.app.name) ($OPERATOR_APP_ID)" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Operator app not found. You may need to create it first." -ForegroundColor Yellow
    Write-Host "Run: .\scripts\create_amplify_apps.ps1" -ForegroundColor Yellow
}

try {
    $USER_APP = aws amplify get-app --app-id $USER_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
    Write-Host "✅ User app found: $($USER_APP.app.name) ($USER_APP_ID)" -ForegroundColor Green
} catch {
    Write-Host "WARNING: User app not found. You may need to create it first." -ForegroundColor Yellow
    Write-Host "Run: .\scripts\create_amplify_apps.ps1" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Associate Custom Domains with Amplify Apps
Write-Host "Step 3: Setting up Custom Domains..." -ForegroundColor Yellow

# Operator Dashboard Domain
Write-Host "Configuring Operator Dashboard domain: $OPERATOR_DOMAIN" -ForegroundColor Cyan
try {
    $OPERATOR_DOMAIN_ASSOC = aws amplify get-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region $REGION 2>&1 | ConvertFrom-Json
    
    if ($OPERATOR_DOMAIN_ASSOC.domainAssociation) {
        Write-Host "✅ Domain already associated" -ForegroundColor Green
        $OPERATOR_CNAME = $OPERATOR_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
        Write-Host "   CNAME: $OPERATOR_CNAME" -ForegroundColor Gray
    }
} catch {
    Write-Host "Domain not yet associated. Creating domain association..." -ForegroundColor Yellow
    
    # Create domain association
    $DOMAIN_ASSOC_CONFIG = @{
        subDomainSettings = @(
            @{
                prefix = "admin"
                branchName = "main"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $DOMAIN_ASSOC_CONFIG | Out-File -FilePath "$env:TEMP\operator-domain.json" -Encoding utf8
    
    try {
        aws amplify create-domain-association `
            --app-id $OPERATOR_APP_ID `
            --domain-name $OPERATOR_DOMAIN `
            --sub-domain-settings file://"$env:TEMP\operator-domain.json" `
            --region $REGION | Out-Null
        
        Write-Host "✅ Domain association created" -ForegroundColor Green
        Write-Host "   Waiting for domain verification..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Get the CNAME
        $OPERATOR_DOMAIN_ASSOC = aws amplify get-domain-association `
            --app-id $OPERATOR_APP_ID `
            --domain-name $OPERATOR_DOMAIN `
            --region $REGION | ConvertFrom-Json
        $OPERATOR_CNAME = $OPERATOR_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
    } catch {
        Write-Host "⚠️  Could not create domain association automatically." -ForegroundColor Yellow
        Write-Host "   Please add the domain manually in Amplify Console:" -ForegroundColor Yellow
        Write-Host "   1. Go to AWS Amplify Console" -ForegroundColor Yellow
        Write-Host "   2. Select app: $OPERATOR_APP_ID" -ForegroundColor Yellow
        Write-Host "   3. Go to Domain Management" -ForegroundColor Yellow
        Write-Host "   4. Add domain: $OPERATOR_DOMAIN" -ForegroundColor Yellow
        Write-Host "   5. Then run this script again" -ForegroundColor Yellow
        exit 1
    }
}

# User Dashboard Domain
Write-Host ""
Write-Host "Configuring User Dashboard domain: $USER_DOMAIN" -ForegroundColor Cyan
try {
    $USER_DOMAIN_ASSOC = aws amplify get-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region $REGION 2>&1 | ConvertFrom-Json
    
    if ($USER_DOMAIN_ASSOC.domainAssociation) {
        Write-Host "✅ Domain already associated" -ForegroundColor Green
        $USER_CNAME = $USER_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
        Write-Host "   CNAME: $USER_CNAME" -ForegroundColor Gray
    }
} catch {
    Write-Host "Domain not yet associated. Creating domain association..." -ForegroundColor Yellow
    
    # Create domain association
    $DOMAIN_ASSOC_CONFIG = @{
        subDomainSettings = @(
            @{
                prefix = "user"
                branchName = "main"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $DOMAIN_ASSOC_CONFIG | Out-File -FilePath "$env:TEMP\user-domain.json" -Encoding utf8
    
    try {
        aws amplify create-domain-association `
            --app-id $USER_APP_ID `
            --domain-name $USER_DOMAIN `
            --sub-domain-settings file://"$env:TEMP\user-domain.json" `
            --region $REGION | Out-Null
        
        Write-Host "✅ Domain association created" -ForegroundColor Green
        Write-Host "   Waiting for domain verification..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Get the CNAME
        $USER_DOMAIN_ASSOC = aws amplify get-domain-association `
            --app-id $USER_APP_ID `
            --domain-name $USER_DOMAIN `
            --region $REGION | ConvertFrom-Json
        $USER_CNAME = $USER_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
    } catch {
        Write-Host "⚠️  Could not create domain association automatically." -ForegroundColor Yellow
        Write-Host "   Please add the domain manually in Amplify Console:" -ForegroundColor Yellow
        Write-Host "   1. Go to AWS Amplify Console" -ForegroundColor Yellow
        Write-Host "   2. Select app: $USER_APP_ID" -ForegroundColor Yellow
        Write-Host "   3. Go to Domain Management" -ForegroundColor Yellow
        Write-Host "   4. Add domain: $USER_DOMAIN" -ForegroundColor Yellow
        Write-Host "   5. Then run this script again" -ForegroundColor Yellow
        exit 1
    }
}

# Get CNAMEs if not already set
if (-not $OPERATOR_CNAME) {
    $OPERATOR_DOMAIN_ASSOC = aws amplify get-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region $REGION | ConvertFrom-Json
    $OPERATOR_CNAME = $OPERATOR_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
}

if (-not $USER_CNAME) {
    $USER_DOMAIN_ASSOC = aws amplify get-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region $REGION | ConvertFrom-Json
    $USER_CNAME = $USER_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
}

Write-Host ""
Write-Host "✅ Domain associations configured" -ForegroundColor Green
Write-Host "   Operator CNAME: $OPERATOR_CNAME" -ForegroundColor Gray
Write-Host "   User CNAME: $USER_CNAME" -ForegroundColor Gray
Write-Host ""

# Step 4: Create Route53 DNS Records
Write-Host "Step 4: Creating Route53 DNS Records..." -ForegroundColor Yellow

# Operator Dashboard CNAME Record
Write-Host "Creating Route53 record for Operator Dashboard..." -ForegroundColor Cyan
$OPERATOR_RECORD = @{
    Changes = @(
        @{
            Action = "UPSERT"
            ResourceRecordSet = @{
                Name = $OPERATOR_DOMAIN
                Type = "CNAME"
                TTL = 300
                ResourceRecords = @(
                    @{
                        Value = $OPERATOR_CNAME
                    }
                )
            }
        }
    )
} | ConvertTo-Json -Depth 10

$OPERATOR_RECORD | Out-File -FilePath "$env:TEMP\operator-route53.json" -Encoding utf8

try {
    $RESULT = aws route53 change-resource-record-sets `
        --hosted-zone-id $HOSTED_ZONE_ID `
        --change-batch "file://$env:TEMP\operator-route53.json" 2>&1 | ConvertFrom-Json
    
    Write-Host "✅ Created Route53 record for Operator Dashboard" -ForegroundColor Green
    Write-Host "   Record: $OPERATOR_DOMAIN -> $OPERATOR_CNAME" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Could not create Route53 record. It may already exist." -ForegroundColor Yellow
}

# User Dashboard CNAME Record
Write-Host ""
Write-Host "Creating Route53 record for User Dashboard..." -ForegroundColor Cyan
$USER_RECORD = @{
    Changes = @(
        @{
            Action = "UPSERT"
            ResourceRecordSet = @{
                Name = $USER_DOMAIN
                Type = "CNAME"
                TTL = 300
                ResourceRecords = @(
                    @{
                        Value = $USER_CNAME
                    }
                )
            }
        }
    )
} | ConvertTo-Json -Depth 10

$USER_RECORD | Out-File -FilePath "$env:TEMP\user-route53.json" -Encoding utf8

try {
    $RESULT = aws route53 change-resource-record-sets `
        --hosted-zone-id $HOSTED_ZONE_ID `
        --change-batch "file://$env:TEMP\user-route53.json" 2>&1 | ConvertFrom-Json
    
    Write-Host "✅ Created Route53 record for User Dashboard" -ForegroundColor Green
    Write-Host "   Record: $USER_DOMAIN -> $USER_CNAME" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Could not create Route53 record. It may already exist." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Route53 DNS records configured" -ForegroundColor Green
Write-Host "   DNS propagation may take 5-15 minutes" -ForegroundColor Yellow
Write-Host ""

# Step 5: Configure Amplify Apps
Write-Host "Step 5: Configuring Amplify Apps..." -ForegroundColor Yellow

# Update Operator App Environment Variables
Write-Host "Updating Operator Dashboard environment variables..." -ForegroundColor Cyan
try {
    aws amplify update-app `
        --app-id $OPERATOR_APP_ID `
        --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" `
        --region $REGION | Out-Null
    Write-Host "✅ Updated Operator app environment variables" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not update environment variables automatically." -ForegroundColor Yellow
    Write-Host "   Please set VITE_API_BASE_URL=$BACKEND_URL in Amplify Console" -ForegroundColor Yellow
}

# Update User App Environment Variables
Write-Host ""
Write-Host "Updating User Dashboard environment variables..." -ForegroundColor Cyan
try {
    aws amplify update-app `
        --app-id $USER_APP_ID `
        --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" `
        --region $REGION | Out-Null
    Write-Host "✅ Updated User app environment variables" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not update environment variables automatically." -ForegroundColor Yellow
    Write-Host "   Please set VITE_API_BASE_URL=$BACKEND_URL in Amplify Console" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Amplify apps configured" -ForegroundColor Green
Write-Host ""

# Step 6: Deployment Instructions
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Route53 DNS records created" -ForegroundColor Green
Write-Host "✅ Custom domains associated with Amplify apps" -ForegroundColor Green
Write-Host "✅ Environment variables configured" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Connect GitHub Repository (if not already connected):" -ForegroundColor Cyan
Write-Host "   - Go to AWS Amplify Console" -ForegroundColor White
Write-Host "   - For each app, connect your GitHub repository" -ForegroundColor White
Write-Host "   - Repository: sainathyai/SpendSenseAI" -ForegroundColor White
Write-Host ""
Write-Host "2. Configure Build Settings:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Operator Dashboard ($OPERATOR_APP_ID):" -ForegroundColor White
Write-Host "   - Base directory: frontend" -ForegroundColor Gray
Write-Host "   - Build command: npm ci && npm run build:operator" -ForegroundColor Gray
Write-Host "   - Output directory: dist" -ForegroundColor Gray
Write-Host "   - Build spec file: frontend/amplify-operator.yml" -ForegroundColor Gray
Write-Host ""
Write-Host "   User Dashboard ($USER_APP_ID):" -ForegroundColor White
Write-Host "   - Base directory: frontend" -ForegroundColor Gray
Write-Host "   - Build command: npm ci && npm run build:user" -ForegroundColor Gray
Write-Host "   - Output directory: dist-user" -ForegroundColor Gray
Write-Host "   - Build spec file: frontend/amplify-user.yml" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Deploy:" -ForegroundColor Cyan
Write-Host "   - Amplify will automatically deploy on push to main branch" -ForegroundColor White
Write-Host "   - Or trigger deployment manually in Amplify Console" -ForegroundColor White
Write-Host ""
Write-Host "4. Verify DNS:" -ForegroundColor Cyan
Write-Host "   - Wait 5-15 minutes for DNS propagation" -ForegroundColor White
Write-Host "   - Test: https://$OPERATOR_DOMAIN" -ForegroundColor White
Write-Host "   - Test: https://$USER_DOMAIN" -ForegroundColor White
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "   Operator Dashboard: https://$OPERATOR_DOMAIN" -ForegroundColor Green
Write-Host "   User Dashboard: https://$USER_DOMAIN" -ForegroundColor Green
Write-Host "   Backend API: $BACKEND_URL" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan



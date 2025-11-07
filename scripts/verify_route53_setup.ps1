# Verify Route53 and Amplify Setup (PowerShell)

$ErrorActionPreference = "Stop"

# Configuration
$ROOT_DOMAIN = "sainathyai.com"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$HOSTED_ZONE_ID = "Z0882306KADD7M9CEUFD"
$REGION = "us-east-1"
$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Route53 and Amplify Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Verify Route53 Hosted Zone
Write-Host "1. Verifying Route53 Hosted Zone..." -ForegroundColor Yellow
try {
    $ZONE = aws route53 get-hosted-zone --id $HOSTED_ZONE_ID --region $REGION 2>&1 | ConvertFrom-Json
    Write-Host "   ✅ Hosted zone found: $($ZONE.HostedZone.Name)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Hosted zone not found" -ForegroundColor Red
}

# Check Route53 Records
Write-Host ""
Write-Host "2. Checking Route53 DNS Records..." -ForegroundColor Yellow

# Operator Domain
$OPERATOR_RECORD = aws route53 list-resource-record-sets `
    --hosted-zone-id $HOSTED_ZONE_ID `
    --query "ResourceRecordSets[?Name=='${OPERATOR_DOMAIN}.']" `
    --region $REGION 2>&1 | ConvertFrom-Json

if ($OPERATOR_RECORD.Count -gt 0) {
    $CNAME = $OPERATOR_RECORD[0].ResourceRecords[0].Value
    Write-Host "   ✅ Operator record found: $OPERATOR_DOMAIN -> $CNAME" -ForegroundColor Green
} else {
    Write-Host "   ❌ Operator record not found" -ForegroundColor Red
}

# User Domain
$USER_RECORD = aws route53 list-resource-record-sets `
    --hosted-zone-id $HOSTED_ZONE_ID `
    --query "ResourceRecordSets[?Name=='${USER_DOMAIN}.']" `
    --region $REGION 2>&1 | ConvertFrom-Json

if ($USER_RECORD.Count -gt 0) {
    $CNAME = $USER_RECORD[0].ResourceRecords[0].Value
    Write-Host "   ✅ User record found: $USER_DOMAIN -> $CNAME" -ForegroundColor Green
} else {
    Write-Host "   ❌ User record not found" -ForegroundColor Red
}

# Check Amplify Apps
Write-Host ""
Write-Host "3. Checking Amplify Apps..." -ForegroundColor Yellow

# Operator App
try {
    $OPERATOR_APP = aws amplify get-app --app-id $OPERATOR_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
    Write-Host "   ✅ Operator app found: $($OPERATOR_APP.app.name) ($OPERATOR_APP_ID)" -ForegroundColor Green
    
    # Check environment variables
    $ENV_VARS = $OPERATOR_APP.app.environmentVariables
    if ($ENV_VARS -and $ENV_VARS.PSObject.Properties['VITE_API_BASE_URL']) {
        Write-Host "      ✅ VITE_API_BASE_URL set: $($ENV_VARS.VITE_API_BASE_URL)" -ForegroundColor Green
    } else {
        Write-Host "      ⚠️  VITE_API_BASE_URL not set" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Operator app not found" -ForegroundColor Red
}

# User App
try {
    $USER_APP = aws amplify get-app --app-id $USER_APP_ID --region $REGION 2>&1 | ConvertFrom-Json
    Write-Host "   ✅ User app found: $($USER_APP.app.name) ($USER_APP_ID)" -ForegroundColor Green
    
    # Check environment variables
    $ENV_VARS = $USER_APP.app.environmentVariables
    if ($ENV_VARS -and $ENV_VARS.PSObject.Properties['VITE_API_BASE_URL']) {
        Write-Host "      ✅ VITE_API_BASE_URL set: $($ENV_VARS.VITE_API_BASE_URL)" -ForegroundColor Green
    } else {
        Write-Host "      ⚠️  VITE_API_BASE_URL not set" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ User app not found" -ForegroundColor Red
}

# Check Domain Associations
Write-Host ""
Write-Host "4. Checking Domain Associations..." -ForegroundColor Yellow

# Operator Domain
try {
    $OPERATOR_DOMAIN_ASSOC = aws amplify get-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region $REGION 2>&1 | ConvertFrom-Json
    
    $STATUS = $OPERATOR_DOMAIN_ASSOC.domainAssociation.domainStatus
    $CNAME = $OPERATOR_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
    
    Write-Host "   ✅ Operator domain associated: $OPERATOR_DOMAIN" -ForegroundColor Green
    Write-Host "      Status: $STATUS" -ForegroundColor Gray
    Write-Host "      CNAME: $CNAME" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Operator domain not associated" -ForegroundColor Red
}

# User Domain
try {
    $USER_DOMAIN_ASSOC = aws amplify get-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region $REGION 2>&1 | ConvertFrom-Json
    
    $STATUS = $USER_DOMAIN_ASSOC.domainAssociation.domainStatus
    $CNAME = $USER_DOMAIN_ASSOC.domainAssociation.subDomains[0].dnsRecord.name
    
    Write-Host "   ✅ User domain associated: $USER_DOMAIN" -ForegroundColor Green
    Write-Host "      Status: $STATUS" -ForegroundColor Gray
    Write-Host "      CNAME: $CNAME" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ User domain not associated" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan




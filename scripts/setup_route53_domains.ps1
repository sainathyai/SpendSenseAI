# Setup Route53 DNS records for Amplify custom domains (PowerShell)

$ErrorActionPreference = "Stop"

$ROOT_DOMAIN = "sainathyai.com"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"

Write-Host "Setting up Route53 DNS records" -ForegroundColor Green
Write-Host ""

# Get hosted zone ID
$HOSTED_ZONE_ID = (aws route53 list-hosted-zones --query "HostedZones[?Name=='${ROOT_DOMAIN}.'].[Id]" --output text).Split('/')[2]

if (-not $HOSTED_ZONE_ID) {
    Write-Host "ERROR: Hosted zone for $ROOT_DOMAIN not found" -ForegroundColor Red
    exit 1
}

Write-Host "Found hosted zone: $HOSTED_ZONE_ID" -ForegroundColor Green
Write-Host ""

# Get Amplify app IDs
Write-Host "Getting Amplify app information..." -ForegroundColor Yellow
Write-Host "Please provide the Amplify app IDs:"
$OPERATOR_APP_ID = Read-Host "1. Operator Dashboard app ID"
$USER_APP_ID = Read-Host "2. User Dashboard app ID"

Write-Host ""
Write-Host "Getting domain verification records from Amplify..." -ForegroundColor Yellow

# For Operator Dashboard
try {
    $OPERATOR_DOMAIN_INFO = aws amplify get-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region us-east-1 | ConvertFrom-Json
    
    Write-Host "Operator domain verification records:" -ForegroundColor Green
    Write-Host ($OPERATOR_DOMAIN_INFO.domainAssociation.domainVerificationRecord | ConvertTo-Json)
} catch {
    Write-Host "Operator domain not yet associated. Please add it in Amplify Console first." -ForegroundColor Yellow
}

# For User Dashboard
try {
    $USER_DOMAIN_INFO = aws amplify get-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region us-east-1 | ConvertFrom-Json
    
    Write-Host "User domain verification records:" -ForegroundColor Green
    Write-Host ($USER_DOMAIN_INFO.domainAssociation.domainVerificationRecord | ConvertTo-Json)
} catch {
    Write-Host "User domain not yet associated. Please add it in Amplify Console first." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Add domains in Amplify Console for both apps"
Write-Host "2. Get the CNAME records from Amplify"
Write-Host "3. Create Route53 records pointing to Amplify CNAMEs"





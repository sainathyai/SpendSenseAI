# Configure custom domains for Amplify apps (PowerShell)

$ErrorActionPreference = "Stop"

$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$REGION = "us-east-1"

Write-Host "Configuring Custom Domains for Amplify Apps" -ForegroundColor Green
Write-Host ""

# Add domain to Operator Dashboard
Write-Host "Adding domain to Operator Dashboard..." -ForegroundColor Yellow
try {
    $OPERATOR_DOMAIN_ASSOC = aws amplify create-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region $REGION `
        --sub-domain-settings "prefix=,branchName=phase3-advanced-features" | ConvertFrom-Json
    
    Write-Host "SUCCESS: Domain added to Operator Dashboard" -ForegroundColor Green
    Write-Host "Domain verification record:" -ForegroundColor Yellow
    Write-Host ($OPERATOR_DOMAIN_ASSOC.domainAssociation.domainVerificationRecord | ConvertTo-Json)
} catch {
    Write-Host "Domain may already be associated or error occurred" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

# Add domain to User Dashboard
Write-Host ""
Write-Host "Adding domain to User Dashboard..." -ForegroundColor Yellow
try {
    $USER_DOMAIN_ASSOC = aws amplify create-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region $REGION `
        --sub-domain-settings "prefix=,branchName=phase3-advanced-features" | ConvertFrom-Json
    
    Write-Host "SUCCESS: Domain added to User Dashboard" -ForegroundColor Green
    Write-Host "Domain verification record:" -ForegroundColor Yellow
    Write-Host ($USER_DOMAIN_ASSOC.domainAssociation.domainVerificationRecord | ConvertTo-Json)
} catch {
    Write-Host "Domain may already be associated or error occurred" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Get CNAME records from Amplify Console for both domains"
Write-Host "2. Create Route53 records pointing to Amplify CNAMEs"
Write-Host "3. Run: .\scripts\setup_route53_records.ps1"


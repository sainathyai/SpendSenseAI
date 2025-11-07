# Associate Amplify Domains for Subdomains (PowerShell)
# Since parent domain is already verified, we can create subdomain associations directly

$ErrorActionPreference = "Stop"

# Configuration
$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$PARENT_DOMAIN = "sainathyai.com"
$REGION = "us-east-1"

Write-Host "Associating Amplify Domains (Subdomains)" -ForegroundColor Cyan
Write-Host "Parent domain $PARENT_DOMAIN is already verified" -ForegroundColor Green
Write-Host ""

# Associate Operator Domain
Write-Host "Associating Operator domain: $OPERATOR_DOMAIN" -ForegroundColor Yellow

try {
    # Try to get existing association
    $EXISTING = aws amplify get-domain-association --app-id $OPERATOR_APP_ID --domain-name $OPERATOR_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
    if ($EXISTING.domainAssociation) {
        Write-Host "Domain already associated!" -ForegroundColor Green
        $CNAME = $EXISTING.domainAssociation.subDomains[0].dnsRecord.name
        Write-Host "CNAME: $CNAME" -ForegroundColor Gray
    }
} catch {
    # Create new association
    Write-Host "Creating domain association..." -ForegroundColor Yellow
    
    # For subdomains of verified parent, we can create directly
    $DOMAIN_CONFIG = @{
        subDomainSettings = @(
            @{
                prefix = "admin"
                branchName = "main"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $DOMAIN_CONFIG | Out-File -FilePath "$env:TEMP\operator-domain.json" -Encoding utf8NoBOM
    
    try {
        $RESULT = aws amplify create-domain-association `
            --app-id $OPERATOR_APP_ID `
            --domain-name $OPERATOR_DOMAIN `
            --sub-domain-settings file://"$env:TEMP\operator-domain.json" `
            --region $REGION 2>&1 | ConvertFrom-Json
        
        Write-Host "Domain association created!" -ForegroundColor Green
        Write-Host "Waiting for DNS record generation..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Get the CNAME
        $DOMAIN_INFO = aws amplify get-domain-association --app-id $OPERATOR_APP_ID --domain-name $OPERATOR_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
        if ($DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
            $CNAME = $DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
            Write-Host "CNAME: $CNAME" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error creating domain association: $_" -ForegroundColor Red
        Write-Host "You may need to add it manually in Amplify Console" -ForegroundColor Yellow
    }
}

Write-Host ""

# Associate User Domain
Write-Host "Associating User domain: $USER_DOMAIN" -ForegroundColor Yellow

try {
    # Try to get existing association
    $EXISTING = aws amplify get-domain-association --app-id $USER_APP_ID --domain-name $USER_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
    if ($EXISTING.domainAssociation) {
        Write-Host "Domain already associated!" -ForegroundColor Green
        $CNAME = $EXISTING.domainAssociation.subDomains[0].dnsRecord.name
        Write-Host "CNAME: $CNAME" -ForegroundColor Gray
    }
} catch {
    # Create new association
    Write-Host "Creating domain association..." -ForegroundColor Yellow
    
    $DOMAIN_CONFIG = @{
        subDomainSettings = @(
            @{
                prefix = "user"
                branchName = "main"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $DOMAIN_CONFIG | Out-File -FilePath "$env:TEMP\user-domain.json" -Encoding utf8NoBOM
    
    try {
        $RESULT = aws amplify create-domain-association `
            --app-id $USER_APP_ID `
            --domain-name $USER_DOMAIN `
            --sub-domain-settings file://"$env:TEMP\user-domain.json" `
            --region $REGION 2>&1 | ConvertFrom-Json
        
        Write-Host "Domain association created!" -ForegroundColor Green
        Write-Host "Waiting for DNS record generation..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Get the CNAME
        $DOMAIN_INFO = aws amplify get-domain-association --app-id $USER_APP_ID --domain-name $USER_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
        if ($DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
            $CNAME = $DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
            Write-Host "CNAME: $CNAME" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error creating domain association: $_" -ForegroundColor Red
        Write-Host "You may need to add it manually in Amplify Console" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done! If domains were created, run the deployment script again to create Route53 records." -ForegroundColor Green
Write-Host ""

exit 0


# Fix Amplify Domain Branch Configuration (PowerShell)
# Move custom domains from phase3-advanced-features to main branch

$ErrorActionPreference = "Stop"

# Configuration
$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$REGION = "us-east-1"
$TARGET_BRANCH = "main"

Write-Host "Fixing Amplify Domain Branch Configuration" -ForegroundColor Cyan
Write-Host "Moving domains from phase3-advanced-features to main branch" -ForegroundColor Yellow
Write-Host ""

# Fix User Dashboard Domain
Write-Host "Fixing User Dashboard domain..." -ForegroundColor Yellow

try {
    # Get current domain association
    $DOMAIN_INFO = aws amplify get-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region $REGION 2>&1 | ConvertFrom-Json
    
    if ($DOMAIN_INFO.domainAssociation) {
        Write-Host "Current domain association found" -ForegroundColor Green
        
        # Check which branch it's on
        $CURRENT_BRANCH = $DOMAIN_INFO.domainAssociation.subDomains[0].branchName
        Write-Host "Current branch: $CURRENT_BRANCH" -ForegroundColor Gray
        
        if ($CURRENT_BRANCH -ne $TARGET_BRANCH) {
            Write-Host "Domain is on wrong branch. Updating to $TARGET_BRANCH..." -ForegroundColor Yellow
            
            # Update subdomain to point to main branch
            $UPDATE_CONFIG = @{
                subDomainSettings = @(
                    @{
                        prefix = "user"
                        branchName = $TARGET_BRANCH
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            $UPDATE_CONFIG | Out-File -FilePath "$env:TEMP\user-domain-update.json" -Encoding utf8
            
            try {
                aws amplify update-domain-association `
                    --app-id $USER_APP_ID `
                    --domain-name $USER_DOMAIN `
                    --sub-domain-settings file://"$env:TEMP\user-domain-update.json" `
                    --region $REGION | Out-Null
                
                Write-Host "Domain updated to $TARGET_BRANCH branch!" -ForegroundColor Green
            } catch {
                Write-Host "Could not update domain automatically. Please update in Amplify Console:" -ForegroundColor Yellow
                Write-Host "1. Go to Domain Management" -ForegroundColor Gray
                Write-Host "2. Edit domain: $USER_DOMAIN" -ForegroundColor Gray
                Write-Host "3. Change branch from phase3-advanced-features to main" -ForegroundColor Gray
            }
        } else {
            Write-Host "Domain is already on $TARGET_BRANCH branch" -ForegroundColor Green
        }
        
        # Get CNAME
        Start-Sleep -Seconds 3
        $DOMAIN_INFO = aws amplify get-domain-association `
            --app-id $USER_APP_ID `
            --domain-name $USER_DOMAIN `
            --region $REGION 2>&1 | ConvertFrom-Json
        
        if ($DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
            $CNAME = $DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
            Write-Host "CNAME: $CNAME" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Could not get domain association. Error: $_" -ForegroundColor Red
}

Write-Host ""

# Fix Operator Dashboard Domain
Write-Host "Fixing Operator Dashboard domain..." -ForegroundColor Yellow

try {
    # Get current domain association
    $DOMAIN_INFO = aws amplify get-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region $REGION 2>&1 | ConvertFrom-Json
    
    if ($DOMAIN_INFO.domainAssociation) {
        Write-Host "Current domain association found" -ForegroundColor Green
        
        # Check which branch it's on
        $CURRENT_BRANCH = $DOMAIN_INFO.domainAssociation.subDomains[0].branchName
        Write-Host "Current branch: $CURRENT_BRANCH" -ForegroundColor Gray
        
        if ($CURRENT_BRANCH -ne $TARGET_BRANCH) {
            Write-Host "Domain is on wrong branch. Updating to $TARGET_BRANCH..." -ForegroundColor Yellow
            
            # Update subdomain to point to main branch
            $UPDATE_CONFIG = @{
                subDomainSettings = @(
                    @{
                        prefix = "admin"
                        branchName = $TARGET_BRANCH
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            $UPDATE_CONFIG | Out-File -FilePath "$env:TEMP\operator-domain-update.json" -Encoding utf8
            
            try {
                aws amplify update-domain-association `
                    --app-id $OPERATOR_APP_ID `
                    --domain-name $OPERATOR_DOMAIN `
                    --sub-domain-settings file://"$env:TEMP\operator-domain-update.json" `
                    --region $REGION | Out-Null
                
                Write-Host "Domain updated to $TARGET_BRANCH branch!" -ForegroundColor Green
            } catch {
                Write-Host "Could not update domain automatically. Please update in Amplify Console:" -ForegroundColor Yellow
                Write-Host "1. Go to Domain Management" -ForegroundColor Gray
                Write-Host "2. Edit domain: $OPERATOR_DOMAIN" -ForegroundColor Gray
                Write-Host "3. Change branch from phase3-advanced-features to main" -ForegroundColor Gray
            }
        } else {
            Write-Host "Domain is already on $TARGET_BRANCH branch" -ForegroundColor Green
        }
        
        # Get CNAME
        Start-Sleep -Seconds 3
        $DOMAIN_INFO = aws amplify get-domain-association `
            --app-id $OPERATOR_APP_ID `
            --domain-name $OPERATOR_DOMAIN `
            --region $REGION 2>&1 | ConvertFrom-Json
        
        if ($DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
            $CNAME = $DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
            Write-Host "CNAME: $CNAME" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Could not get domain association. Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Connect GitHub repository to main branch in Amplify Console" -ForegroundColor Yellow
Write-Host "2. Configure build settings for main branch" -ForegroundColor Yellow
Write-Host "3. Deploy the main branch" -ForegroundColor Yellow
Write-Host "4. Run Route53 script to create DNS records" -ForegroundColor Yellow
Write-Host ""

exit 0


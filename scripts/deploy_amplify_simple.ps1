# Simple Amplify Frontend Deployment Script
# Run this script to set up Route53 and deploy frontend

Write-Host "Starting Amplify Frontend Deployment..." -ForegroundColor Green
Write-Host ""

# Configuration
$BACKEND_URL = "https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com"
$HOSTED_ZONE_ID = "Z0882306KADD7M9CEUFD"
$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$REGION = "us-east-1"

# Step 1: Get or create domain associations
Write-Host "Step 1: Setting up Amplify domain associations..." -ForegroundColor Yellow

$OPERATOR_CNAME = $null
try {
    $OPERATOR_DOMAIN_INFO = aws amplify get-domain-association --app-id $OPERATOR_APP_ID --domain-name $OPERATOR_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
    if ($OPERATOR_DOMAIN_INFO -and $OPERATOR_DOMAIN_INFO.domainAssociation -and $OPERATOR_DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
        $OPERATOR_CNAME = $OPERATOR_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
        Write-Host "Operator CNAME: $OPERATOR_CNAME" -ForegroundColor Green
    } else {
        Write-Host "Operator domain not associated. Creating association..." -ForegroundColor Yellow
        # Create domain association for subdomain (parent domain already verified)
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
            
            Write-Host "Domain association created. Waiting for DNS record..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
            
            # Get the CNAME
            $OPERATOR_DOMAIN_INFO = aws amplify get-domain-association --app-id $OPERATOR_APP_ID --domain-name $OPERATOR_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
            if ($OPERATOR_DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
                $OPERATOR_CNAME = $OPERATOR_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
                Write-Host "Operator CNAME: $OPERATOR_CNAME" -ForegroundColor Green
            }
        } catch {
            Write-Host "Could not create domain association automatically. Please add it in Amplify Console." -ForegroundColor Yellow
            Write-Host "App ID: $OPERATOR_APP_ID | Domain: $OPERATOR_DOMAIN" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "Operator domain not associated. Attempting to create..." -ForegroundColor Yellow
    # Try to create domain association
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
        
        Write-Host "Domain association created. Waiting for DNS record..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Get the CNAME
        $OPERATOR_DOMAIN_INFO = aws amplify get-domain-association --app-id $OPERATOR_APP_ID --domain-name $OPERATOR_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
        if ($OPERATOR_DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
            $OPERATOR_CNAME = $OPERATOR_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
            Write-Host "Operator CNAME: $OPERATOR_CNAME" -ForegroundColor Green
        }
    } catch {
        Write-Host "Could not create domain association. Please add it in Amplify Console." -ForegroundColor Yellow
        Write-Host "App ID: $OPERATOR_APP_ID | Domain: $OPERATOR_DOMAIN" -ForegroundColor Gray
    }
}

$USER_CNAME = $null
try {
    $USER_DOMAIN_INFO = aws amplify get-domain-association --app-id $USER_APP_ID --domain-name $USER_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
    if ($USER_DOMAIN_INFO -and $USER_DOMAIN_INFO.domainAssociation -and $USER_DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
        $USER_CNAME = $USER_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
        Write-Host "User CNAME: $USER_CNAME" -ForegroundColor Green
    } else {
        Write-Host "User domain not associated. Creating association..." -ForegroundColor Yellow
        # Create domain association for subdomain (parent domain already verified)
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
            
            Write-Host "Domain association created. Waiting for DNS record..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
            
            # Get the CNAME
            $USER_DOMAIN_INFO = aws amplify get-domain-association --app-id $USER_APP_ID --domain-name $USER_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
            if ($USER_DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
                $USER_CNAME = $USER_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
                Write-Host "User CNAME: $USER_CNAME" -ForegroundColor Green
            }
        } catch {
            Write-Host "Could not create domain association automatically. Please add it in Amplify Console." -ForegroundColor Yellow
            Write-Host "App ID: $USER_APP_ID | Domain: $USER_DOMAIN" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "User domain not associated. Attempting to create..." -ForegroundColor Yellow
    # Try to create domain association
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
        
        Write-Host "Domain association created. Waiting for DNS record..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Get the CNAME
        $USER_DOMAIN_INFO = aws amplify get-domain-association --app-id $USER_APP_ID --domain-name $USER_DOMAIN --region $REGION 2>&1 | ConvertFrom-Json
        if ($USER_DOMAIN_INFO.domainAssociation.subDomains.Count -gt 0) {
            $USER_CNAME = $USER_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord.name
            Write-Host "User CNAME: $USER_CNAME" -ForegroundColor Green
        }
    } catch {
        Write-Host "Could not create domain association. Please add it in Amplify Console." -ForegroundColor Yellow
        Write-Host "App ID: $USER_APP_ID | Domain: $USER_DOMAIN" -ForegroundColor Gray
    }
}

Write-Host ""

# Step 2: Create Route53 records
Write-Host "Step 2: Creating Route53 DNS records..." -ForegroundColor Yellow

# Operator record
if ($OPERATOR_CNAME) {
    $OPERATOR_RECORD = @{
        Changes = @(
            @{
                Action = "UPSERT"
                ResourceRecordSet = @{
                    Name = $OPERATOR_DOMAIN
                    Type = "CNAME"
                    TTL = 300
                    ResourceRecords = @(@{Value = $OPERATOR_CNAME})
                }
            }
        )
    } | ConvertTo-Json -Depth 10

    $OPERATOR_RECORD | Out-File -FilePath "$env:TEMP\operator-r53.json" -Encoding utf8NoBOM

    try {
        aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch "file://$env:TEMP\operator-r53.json" | Out-Null
        Write-Host "Created Route53 record for Operator Dashboard" -ForegroundColor Green
    } catch {
        Write-Host "Could not create Operator Route53 record" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping Operator Route53 record (domain not associated)" -ForegroundColor Gray
}

# User record
if ($USER_CNAME) {
    $USER_RECORD = @{
        Changes = @(
            @{
                Action = "UPSERT"
                ResourceRecordSet = @{
                    Name = $USER_DOMAIN
                    Type = "CNAME"
                    TTL = 300
                    ResourceRecords = @(@{Value = $USER_CNAME})
                }
            }
        )
    } | ConvertTo-Json -Depth 10

    $USER_RECORD | Out-File -FilePath "$env:TEMP\user-r53.json" -Encoding utf8NoBOM

    try {
        aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch "file://$env:TEMP\user-r53.json" | Out-Null
        Write-Host "Created Route53 record for User Dashboard" -ForegroundColor Green
    } catch {
        Write-Host "Could not create User Route53 record" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping User Route53 record (domain not associated)" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Update environment variables
Write-Host "Step 3: Updating Amplify environment variables..." -ForegroundColor Yellow

try {
    aws amplify update-app --app-id $OPERATOR_APP_ID --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" --region $REGION | Out-Null
    Write-Host "Updated Operator app environment variables" -ForegroundColor Green
} catch {
    Write-Host "Could not update Operator environment variables" -ForegroundColor Yellow
}

try {
    aws amplify update-app --app-id $USER_APP_ID --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" --region $REGION | Out-Null
    Write-Host "Updated User app environment variables" -ForegroundColor Green
} catch {
    Write-Host "Could not update User environment variables" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Route53 DNS records created" -ForegroundColor Green
Write-Host "Environment variables updated" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Go to AWS Amplify Console" -ForegroundColor White
Write-Host "2. For each app, connect GitHub repository" -ForegroundColor White
Write-Host "3. Configure build settings:" -ForegroundColor White
Write-Host "   Operator: Base dir: frontend, Build: npm ci && npm run build:operator, Output: dist" -ForegroundColor Gray
Write-Host "   User: Base dir: frontend, Build: npm ci && npm run build:user, Output: dist-user" -ForegroundColor Gray
Write-Host "4. Deploy (automatic on push or manual trigger)" -ForegroundColor White
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  Operator: https://$OPERATOR_DOMAIN" -ForegroundColor Green
Write-Host "  User: https://$USER_DOMAIN" -ForegroundColor Green
Write-Host "  Backend: $BACKEND_URL" -ForegroundColor Green
Write-Host ""



# Setup Route53 DNS records for Amplify custom domains (PowerShell)

$ErrorActionPreference = "Stop"

$HOSTED_ZONE_ID = "Z0882306KADD7M9CEUFD"
$OPERATOR_DOMAIN = "admin.spendsenseai.sainathyai.com"
$USER_DOMAIN = "user.spendsenseai.sainathyai.com"
$REGION = "us-east-1"

Write-Host "Setting up Route53 DNS records" -ForegroundColor Green
Write-Host ""

# Get Amplify CNAME records
Write-Host "Getting Amplify CNAME records..." -ForegroundColor Yellow

$OPERATOR_APP_ID = "dvukd3zjye01u"
$USER_APP_ID = "d2yncedb4tyu2y"

try {
    $OPERATOR_DOMAIN_INFO = aws amplify get-domain-association `
        --app-id $OPERATOR_APP_ID `
        --domain-name $OPERATOR_DOMAIN `
        --region $REGION | ConvertFrom-Json
    
    $OPERATOR_CNAME = $OPERATOR_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord
    
    Write-Host "Operator Dashboard CNAME:" -ForegroundColor Green
    Write-Host "  Name: $OPERATOR_DOMAIN" -ForegroundColor Yellow
    Write-Host "  Value: $($OPERATOR_CNAME.name)" -ForegroundColor Yellow
    Write-Host "  Type: CNAME" -ForegroundColor Yellow
    
    # Create Route53 record
    $CHANGE_BATCH = @{
        Changes = @(
            @{
                Action = "UPSERT"
                ResourceRecordSet = @{
                    Name = $OPERATOR_DOMAIN
                    Type = "CNAME"
                    TTL = 300
                    ResourceRecords = @(
                        @{
                            Value = $OPERATOR_CNAME.name
                        }
                    )
                }
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $CHANGE_BATCH | Out-File -FilePath "$env:TEMP\operator-route53.json" -Encoding utf8
    
    aws route53 change-resource-record-sets `
        --hosted-zone-id $HOSTED_ZONE_ID `
        --change-batch "file://$env:TEMP\operator-route53.json" | Out-Null
    
    Write-Host "SUCCESS: Created Route53 record for Operator Dashboard" -ForegroundColor Green
} catch {
    Write-Host "Could not get Operator domain info. Please add domain in Amplify Console first." -ForegroundColor Yellow
}

try {
    $USER_DOMAIN_INFO = aws amplify get-domain-association `
        --app-id $USER_APP_ID `
        --domain-name $USER_DOMAIN `
        --region $REGION | ConvertFrom-Json
    
    $USER_CNAME = $USER_DOMAIN_INFO.domainAssociation.subDomains[0].dnsRecord
    
    Write-Host ""
    Write-Host "User Dashboard CNAME:" -ForegroundColor Green
    Write-Host "  Name: $USER_DOMAIN" -ForegroundColor Yellow
    Write-Host "  Value: $($USER_CNAME.name)" -ForegroundColor Yellow
    Write-Host "  Type: CNAME" -ForegroundColor Yellow
    
    # Create Route53 record
    $CHANGE_BATCH = @{
        Changes = @(
            @{
                Action = "UPSERT"
                ResourceRecordSet = @{
                    Name = $USER_DOMAIN
                    Type = "CNAME"
                    TTL = 300
                    ResourceRecords = @(
                        @{
                            Value = $USER_CNAME.name
                        }
                    )
                }
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $CHANGE_BATCH | Out-File -FilePath "$env:TEMP\user-route53.json" -Encoding utf8
    
    aws route53 change-resource-record-sets `
        --hosted-zone-id $HOSTED_ZONE_ID `
        --change-batch "file://$env:TEMP\user-route53.json" | Out-Null
    
    Write-Host "SUCCESS: Created Route53 record for User Dashboard" -ForegroundColor Green
} catch {
    Write-Host "Could not get User domain info. Please add domain in Amplify Console first." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "DNS records created!" -ForegroundColor Green
Write-Host "DNS propagation may take a few minutes." -ForegroundColor Yellow





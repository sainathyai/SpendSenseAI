#!/bin/bash
# Setup Route53 DNS records for Amplify custom domains

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DOMAIN="sainathyai.com"
OPERATOR_DOMAIN="admin.spendsenseai.sainathyai.com"
USER_DOMAIN="user.spendsenseai.sainathyai.com"

echo -e "${GREEN}Setting up Route53 DNS records${NC}"
echo ""

# Get hosted zone ID
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones --query "HostedZones[?Name=='${ROOT_DOMAIN}.'].[Id]" --output text | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo -e "${RED}ERROR: Hosted zone for $ROOT_DOMAIN not found${NC}"
    exit 1
fi

echo -e "${GREEN}Found hosted zone: $HOSTED_ZONE_ID${NC}"
echo ""

# Get Amplify app IDs
echo -e "${YELLOW}Getting Amplify app information...${NC}"
echo "Please provide the Amplify app IDs:"
echo "1. Operator Dashboard app ID:"
read OPERATOR_APP_ID
echo "2. User Dashboard app ID:"
read USER_APP_ID

# Get domain verification records from Amplify
echo ""
echo -e "${YELLOW}Getting domain verification records from Amplify...${NC}"

# For Operator Dashboard
OPERATOR_DOMAIN_INFO=$(aws amplify get-domain-association \
    --app-id $OPERATOR_APP_ID \
    --domain-name $OPERATOR_DOMAIN \
    --region us-east-1 2>/dev/null || echo "")

if [ -z "$OPERATOR_DOMAIN_INFO" ]; then
    echo -e "${YELLOW}Operator domain not yet associated. Please add it in Amplify Console first.${NC}"
else
    echo "Operator domain verification records:"
    echo "$OPERATOR_DOMAIN_INFO" | jq -r '.domainAssociation.domainVerificationRecord'
fi

# For User Dashboard
USER_DOMAIN_INFO=$(aws amplify get-domain-association \
    --app-id $USER_APP_ID \
    --domain-name $USER_DOMAIN \
    --region us-east-1 2>/dev/null || echo "")

if [ -z "$USER_DOMAIN_INFO" ]; then
    echo -e "${YELLOW}User domain not yet associated. Please add it in Amplify Console first.${NC}"
else
    echo "User domain verification records:"
    echo "$USER_DOMAIN_INFO" | jq -r '.domainAssociation.domainVerificationRecord'
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Add domains in Amplify Console for both apps"
echo "2. Get the CNAME records from Amplify"
echo "3. Create Route53 records pointing to Amplify CNAMEs"





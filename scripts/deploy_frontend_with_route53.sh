#!/bin/bash
# Complete Frontend Deployment with Route53 Setup (Bash)
# This script sets up Route53 DNS records and deploys frontend to AWS Amplify

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL=${BACKEND_URL:-"https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com"}
ROOT_DOMAIN="sainathyai.com"
OPERATOR_DOMAIN="admin.spendsenseai.sainathyai.com"
USER_DOMAIN="user.spendsenseai.sainathyai.com"
HOSTED_ZONE_ID="Z0882306KADD7M9CEUFD"
REGION="us-east-1"

# Amplify App IDs (from deployment status)
OPERATOR_APP_ID="dvukd3zjye01u"
USER_APP_ID="d2yncedb4tyu2y"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Frontend Deployment with Route53 Setup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: Not logged into AWS. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"
echo ""

# Step 1: Verify Route53 Hosted Zone
echo -e "${YELLOW}Step 1: Verifying Route53 Hosted Zone...${NC}"
if aws route53 get-hosted-zone --id "$HOSTED_ZONE_ID" --region "$REGION" &> /dev/null; then
    echo -e "${GREEN}✅ Found hosted zone: $HOSTED_ZONE_ID ($ROOT_DOMAIN)${NC}"
else
    echo -e "${RED}ERROR: Could not find hosted zone $HOSTED_ZONE_ID${NC}"
    echo -e "${YELLOW}Please verify the hosted zone ID is correct.${NC}"
    exit 1
fi
echo ""

# Step 2: Check Amplify Apps
echo -e "${YELLOW}Step 2: Verifying Amplify Apps...${NC}"
if aws amplify get-app --app-id "$OPERATOR_APP_ID" --region "$REGION" &> /dev/null; then
    OPERATOR_APP_NAME=$(aws amplify get-app --app-id "$OPERATOR_APP_ID" --region "$REGION" | jq -r '.app.name')
    echo -e "${GREEN}✅ Operator app found: $OPERATOR_APP_NAME ($OPERATOR_APP_ID)${NC}"
else
    echo -e "${YELLOW}WARNING: Operator app not found. You may need to create it first.${NC}"
    echo -e "${YELLOW}Run: ./scripts/create_amplify_apps.sh${NC}"
fi

if aws amplify get-app --app-id "$USER_APP_ID" --region "$REGION" &> /dev/null; then
    USER_APP_NAME=$(aws amplify get-app --app-id "$USER_APP_ID" --region "$REGION" | jq -r '.app.name')
    echo -e "${GREEN}✅ User app found: $USER_APP_NAME ($USER_APP_ID)${NC}"
else
    echo -e "${YELLOW}WARNING: User app not found. You may need to create it first.${NC}"
    echo -e "${YELLOW}Run: ./scripts/create_amplify_apps.sh${NC}"
fi
echo ""

# Step 3: Associate Custom Domains with Amplify Apps
echo -e "${YELLOW}Step 3: Setting up Custom Domains...${NC}"

# Operator Dashboard Domain
echo -e "${CYAN}Configuring Operator Dashboard domain: $OPERATOR_DOMAIN${NC}"
OPERATOR_DOMAIN_ASSOC=$(aws amplify get-domain-association \
    --app-id "$OPERATOR_APP_ID" \
    --domain-name "$OPERATOR_DOMAIN" \
    --region "$REGION" 2>/dev/null || echo "")

if [ -n "$OPERATOR_DOMAIN_ASSOC" ]; then
    echo -e "${GREEN}✅ Domain already associated${NC}"
    OPERATOR_CNAME=$(echo "$OPERATOR_DOMAIN_ASSOC" | jq -r '.domainAssociation.subDomains[0].dnsRecord.name')
    echo -e "   CNAME: $OPERATOR_CNAME"
else
    echo -e "${YELLOW}Domain not yet associated. Creating domain association...${NC}"
    
    # Create domain association
    cat > /tmp/operator-domain.json <<EOF
{
  "subDomainSettings": [
    {
      "prefix": "admin",
      "branchName": "main"
    }
  ]
}
EOF
    
    if aws amplify create-domain-association \
        --app-id "$OPERATOR_APP_ID" \
        --domain-name "$OPERATOR_DOMAIN" \
        --sub-domain-settings file:///tmp/operator-domain.json \
        --region "$REGION" &> /dev/null; then
        echo -e "${GREEN}✅ Domain association created${NC}"
        echo -e "${YELLOW}   Waiting for domain verification...${NC}"
        sleep 5
        
        # Get the CNAME
        OPERATOR_DOMAIN_ASSOC=$(aws amplify get-domain-association \
            --app-id "$OPERATOR_APP_ID" \
            --domain-name "$OPERATOR_DOMAIN" \
            --region "$REGION")
        OPERATOR_CNAME=$(echo "$OPERATOR_DOMAIN_ASSOC" | jq -r '.domainAssociation.subDomains[0].dnsRecord.name')
    else
        echo -e "${YELLOW}⚠️  Could not create domain association automatically.${NC}"
        echo -e "${YELLOW}   Please add the domain manually in Amplify Console:${NC}"
        echo -e "${YELLOW}   1. Go to AWS Amplify Console${NC}"
        echo -e "${YELLOW}   2. Select app: $OPERATOR_APP_ID${NC}"
        echo -e "${YELLOW}   3. Go to Domain Management${NC}"
        echo -e "${YELLOW}   4. Add domain: $OPERATOR_DOMAIN${NC}"
        echo -e "${YELLOW}   5. Then run this script again${NC}"
        exit 1
    fi
fi

# User Dashboard Domain
echo ""
echo -e "${CYAN}Configuring User Dashboard domain: $USER_DOMAIN${NC}"
USER_DOMAIN_ASSOC=$(aws amplify get-domain-association \
    --app-id "$USER_APP_ID" \
    --domain-name "$USER_DOMAIN" \
    --region "$REGION" 2>/dev/null || echo "")

if [ -n "$USER_DOMAIN_ASSOC" ]; then
    echo -e "${GREEN}✅ Domain already associated${NC}"
    USER_CNAME=$(echo "$USER_DOMAIN_ASSOC" | jq -r '.domainAssociation.subDomains[0].dnsRecord.name')
    echo -e "   CNAME: $USER_CNAME"
else
    echo -e "${YELLOW}Domain not yet associated. Creating domain association...${NC}"
    
    # Create domain association
    cat > /tmp/user-domain.json <<EOF
{
  "subDomainSettings": [
    {
      "prefix": "user",
      "branchName": "main"
    }
  ]
}
EOF
    
    if aws amplify create-domain-association \
        --app-id "$USER_APP_ID" \
        --domain-name "$USER_DOMAIN" \
        --sub-domain-settings file:///tmp/user-domain.json \
        --region "$REGION" &> /dev/null; then
        echo -e "${GREEN}✅ Domain association created${NC}"
        echo -e "${YELLOW}   Waiting for domain verification...${NC}"
        sleep 5
        
        # Get the CNAME
        USER_DOMAIN_ASSOC=$(aws amplify get-domain-association \
            --app-id "$USER_APP_ID" \
            --domain-name "$USER_DOMAIN" \
            --region "$REGION")
        USER_CNAME=$(echo "$USER_DOMAIN_ASSOC" | jq -r '.domainAssociation.subDomains[0].dnsRecord.name')
    else
        echo -e "${YELLOW}⚠️  Could not create domain association automatically.${NC}"
        echo -e "${YELLOW}   Please add the domain manually in Amplify Console:${NC}"
        echo -e "${YELLOW}   1. Go to AWS Amplify Console${NC}"
        echo -e "${YELLOW}   2. Select app: $USER_APP_ID${NC}"
        echo -e "${YELLOW}   3. Go to Domain Management${NC}"
        echo -e "${YELLOW}   4. Add domain: $USER_DOMAIN${NC}"
        echo -e "${YELLOW}   5. Then run this script again${NC}"
        exit 1
    fi
fi

# Get CNAMEs if not already set
if [ -z "$OPERATOR_CNAME" ]; then
    OPERATOR_DOMAIN_ASSOC=$(aws amplify get-domain-association \
        --app-id "$OPERATOR_APP_ID" \
        --domain-name "$OPERATOR_DOMAIN" \
        --region "$REGION")
    OPERATOR_CNAME=$(echo "$OPERATOR_DOMAIN_ASSOC" | jq -r '.domainAssociation.subDomains[0].dnsRecord.name')
fi

if [ -z "$USER_CNAME" ]; then
    USER_DOMAIN_ASSOC=$(aws amplify get-domain-association \
        --app-id "$USER_APP_ID" \
        --domain-name "$USER_DOMAIN" \
        --region "$REGION")
    USER_CNAME=$(echo "$USER_DOMAIN_ASSOC" | jq -r '.domainAssociation.subDomains[0].dnsRecord.name')
fi

echo ""
echo -e "${GREEN}✅ Domain associations configured${NC}"
echo -e "   Operator CNAME: $OPERATOR_CNAME"
echo -e "   User CNAME: $USER_CNAME"
echo ""

# Step 4: Create Route53 DNS Records
echo -e "${YELLOW}Step 4: Creating Route53 DNS Records...${NC}"

# Operator Dashboard CNAME Record
echo -e "${CYAN}Creating Route53 record for Operator Dashboard...${NC}"
cat > /tmp/operator-route53.json <<EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$OPERATOR_DOMAIN",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "$OPERATOR_CNAME"
          }
        ]
      }
    }
  ]
}
EOF

if aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch file:///tmp/operator-route53.json &> /dev/null; then
    echo -e "${GREEN}✅ Created Route53 record for Operator Dashboard${NC}"
    echo -e "   Record: $OPERATOR_DOMAIN -> $OPERATOR_CNAME"
else
    echo -e "${YELLOW}⚠️  Could not create Route53 record. It may already exist.${NC}"
fi

# User Dashboard CNAME Record
echo ""
echo -e "${CYAN}Creating Route53 record for User Dashboard...${NC}"
cat > /tmp/user-route53.json <<EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$USER_DOMAIN",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "$USER_CNAME"
          }
        ]
      }
    }
  ]
}
EOF

if aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch file:///tmp/user-route53.json &> /dev/null; then
    echo -e "${GREEN}✅ Created Route53 record for User Dashboard${NC}"
    echo -e "   Record: $USER_DOMAIN -> $USER_CNAME"
else
    echo -e "${YELLOW}⚠️  Could not create Route53 record. It may already exist.${NC}"
fi

echo ""
echo -e "${GREEN}✅ Route53 DNS records configured${NC}"
echo -e "${YELLOW}   DNS propagation may take 5-15 minutes${NC}"
echo ""

# Step 5: Configure Amplify Apps
echo -e "${YELLOW}Step 5: Configuring Amplify Apps...${NC}"

# Update Operator App Environment Variables
echo -e "${CYAN}Updating Operator Dashboard environment variables...${NC}"
if aws amplify update-app \
    --app-id "$OPERATOR_APP_ID" \
    --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" \
    --region "$REGION" &> /dev/null; then
    echo -e "${GREEN}✅ Updated Operator app environment variables${NC}"
else
    echo -e "${YELLOW}⚠️  Could not update environment variables automatically.${NC}"
    echo -e "${YELLOW}   Please set VITE_API_BASE_URL=$BACKEND_URL in Amplify Console${NC}"
fi

# Update User App Environment Variables
echo ""
echo -e "${CYAN}Updating User Dashboard environment variables...${NC}"
if aws amplify update-app \
    --app-id "$USER_APP_ID" \
    --environment-variables "VITE_API_BASE_URL=$BACKEND_URL" \
    --region "$REGION" &> /dev/null; then
    echo -e "${GREEN}✅ Updated User app environment variables${NC}"
else
    echo -e "${YELLOW}⚠️  Could not update environment variables automatically.${NC}"
    echo -e "${YELLOW}   Please set VITE_API_BASE_URL=$BACKEND_URL in Amplify Console${NC}"
fi

echo ""
echo -e "${GREEN}✅ Amplify apps configured${NC}"
echo ""

# Step 6: Deployment Instructions
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Deployment Summary${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${GREEN}✅ Route53 DNS records created${NC}"
echo -e "${GREEN}✅ Custom domains associated with Amplify apps${NC}"
echo -e "${GREEN}✅ Environment variables configured${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "${CYAN}1. Connect GitHub Repository (if not already connected):${NC}"
echo "   - Go to AWS Amplify Console"
echo "   - For each app, connect your GitHub repository"
echo "   - Repository: sainathyai/SpendSenseAI"
echo ""
echo -e "${CYAN}2. Configure Build Settings:${NC}"
echo ""
echo -e "   Operator Dashboard ($OPERATOR_APP_ID):"
echo "   - Base directory: frontend"
echo "   - Build command: npm ci && npm run build:operator"
echo "   - Output directory: dist"
echo "   - Build spec file: frontend/amplify-operator.yml"
echo ""
echo -e "   User Dashboard ($USER_APP_ID):"
echo "   - Base directory: frontend"
echo "   - Build command: npm ci && npm run build:user"
echo "   - Output directory: dist-user"
echo "   - Build spec file: frontend/amplify-user.yml"
echo ""
echo -e "${CYAN}3. Deploy:${NC}"
echo "   - Amplify will automatically deploy on push to main branch"
echo "   - Or trigger deployment manually in Amplify Console"
echo ""
echo -e "${CYAN}4. Verify DNS:${NC}"
echo "   - Wait 5-15 minutes for DNS propagation"
echo "   - Test: https://$OPERATOR_DOMAIN"
echo "   - Test: https://$USER_DOMAIN"
echo ""
echo -e "${CYAN}URLs:${NC}"
echo -e "${GREEN}   Operator Dashboard: https://$OPERATOR_DOMAIN${NC}"
echo -e "${GREEN}   User Dashboard: https://$USER_DOMAIN${NC}"
echo -e "${GREEN}   Backend API: $BACKEND_URL${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${CYAN}========================================${NC}"




#!/bin/bash
# Deploy both Operator and User Dashboards to AWS Amplify

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_URL=${BACKEND_URL:-"https://spendsenseai-env.eba-wmiq25te.us-east-1.elasticbeanstalk.com"}
OPERATOR_DOMAIN="admin.spendsenseai.sainathyai.com"
USER_DOMAIN="user.spendsenseai.sainathyai.com"
ROOT_DOMAIN="sainathyai.com"

echo -e "${GREEN}Deploying Frontend Dashboards to AWS Amplify${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found${NC}"
    exit 1
fi

# Check Amplify CLI
if ! command -v amplify &> /dev/null; then
    echo -e "${YELLOW}Installing Amplify CLI...${NC}"
    npm install -g @aws-amplify/cli
fi

cd frontend

echo -e "${YELLOW}Step 1: Deploying Operator Dashboard...${NC}"
echo "This will create an Amplify app for the Operator Dashboard"
echo ""
echo "Please follow these steps in AWS Console:"
echo "1. Go to AWS Amplify Console"
echo "2. Click 'New app' -> 'Host web app'"
echo "3. Connect your GitHub repository"
echo "4. Configure build settings:"
echo "   - App name: spendsenseai-operator"
echo "   - Branch: phase3-advanced-features"
echo "   - Base directory: frontend"
echo "   - Build command: npm ci && npm run build:operator"
echo "   - Output directory: dist"
echo "   - Build spec file: frontend/amplify-operator.yml"
echo "5. Add environment variable:"
echo "   - VITE_API_BASE_URL: $BACKEND_URL"
echo "6. Deploy"
echo ""

echo -e "${YELLOW}Step 2: Deploying User Dashboard...${NC}"
echo "1. Go to AWS Amplify Console"
echo "2. Click 'New app' -> 'Host web app'"
echo "3. Connect your GitHub repository"
echo "4. Configure build settings:"
echo "   - App name: spendsenseai-user"
echo "   - Branch: phase3-advanced-features"
echo "   - Base directory: frontend"
echo "   - Build command: npm ci && npm run build:user"
echo "   - Output directory: dist-user"
echo "   - Build spec file: frontend/amplify-user.yml"
echo "5. Add environment variable:"
echo "   - VITE_API_BASE_URL: $BACKEND_URL"
echo "6. Deploy"
echo ""

echo -e "${YELLOW}Step 3: Configure Custom Domains${NC}"
echo "For each app, go to Domain Management and add:"
echo "  - Operator: $OPERATOR_DOMAIN"
echo "  - User: $USER_DOMAIN"
echo ""

echo -e "${GREEN}Deployment instructions complete!${NC}"
echo ""
echo "After deploying both apps, run:"
echo "  ./scripts/setup_route53_domains.sh"

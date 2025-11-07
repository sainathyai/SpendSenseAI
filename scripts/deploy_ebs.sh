#!/bin/bash
# Deploy SpendSenseAI to AWS Elastic Beanstalk

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
APP_NAME="spendsenseai"
ENV_NAME="${APP_NAME}-env"
PLATFORM="Python 3.11"
INSTANCE_TYPE="t3.small"

echo -e "${GREEN}Starting Elastic Beanstalk Deployment${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found${NC}"
    exit 1
fi

# Check EB CLI
if ! command -v eb &> /dev/null; then
    echo -e "${YELLOW}EB CLI not found. Installing...${NC}"
    pip install awsebcli
fi

# Check if logged in
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: Not logged into AWS${NC}"
    exit 1
fi

echo -e "${GREEN}SUCCESS: AWS CLI configured${NC}"

# Initialize EB if not already done
if [ ! -f ".elasticbeanstalk/config.yml" ]; then
    echo ""
    echo -e "${YELLOW}Initializing Elastic Beanstalk...${NC}"
    eb init -p "$PLATFORM" -r "$AWS_REGION" "$APP_NAME" --region "$AWS_REGION"
else
    echo -e "${GREEN}Elastic Beanstalk already initialized${NC}"
fi

# Create environment if it doesn't exist
echo ""
echo -e "${YELLOW}Checking environment...${NC}"
if ! eb status "$ENV_NAME" &> /dev/null; then
    echo "Creating environment: $ENV_NAME"
    eb create "$ENV_NAME" \
        --instance-type "$INSTANCE_TYPE" \
        --platform "$PLATFORM" \
        --region "$AWS_REGION" \
        --envvars SPENDSENSE_DB_PATH=/var/app/data/spendsense.db,ENABLE_LLM=true,USE_AWS_SECRETS=true,AWS_REGION=$AWS_REGION
else
    echo -e "${GREEN}Environment exists: $ENV_NAME${NC}"
fi

# Deploy
echo ""
echo -e "${YELLOW}Deploying application...${NC}"
eb deploy "$ENV_NAME"

# Get URL
echo ""
echo -e "${GREEN}Getting application URL...${NC}"
APP_URL=$(eb status "$ENV_NAME" | grep "CNAME" | awk '{print $2}')
echo -e "${GREEN}Application URL: https://${APP_URL}${NC}"

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update frontend VITE_API_BASE_URL to: https://${APP_URL}"
echo "2. Deploy frontend to Amplify"





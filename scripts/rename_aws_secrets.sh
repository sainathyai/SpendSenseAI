#!/bin/bash
# Script to create sainathyai-identified secrets from existing OpenAI secrets
# This copies the values from existing secrets to new ones with sainathyai identifier

REGION="us-east-1"

echo "Creating sainathyai-identified secrets..."

# Get value from openai/api-key
PRIMARY_VALUE=$(aws secretsmanager get-secret-value \
    --secret-id openai/api-key \
    --region $REGION \
    --query SecretString \
    --output text)

# Get value from openai/assistant
BACKUP_VALUE=$(aws secretsmanager get-secret-value \
    --secret-id openai/assistant \
    --region $REGION \
    --query SecretString \
    --output text)

# Create primary secret with sainathyai identifier
echo "Creating sainathyai/openai-api-key-primary..."
aws secretsmanager create-secret \
    --name sainathyai/openai-api-key-primary \
    --description "OpenAI API key for SpendSenseAI (sainathyai) - Primary key" \
    --secret-string "$PRIMARY_VALUE" \
    --region $REGION

# Create backup secret with sainathyai identifier
echo "Creating sainathyai/openai-api-key-backup..."
aws secretsmanager create-secret \
    --name sainathyai/openai-api-key-backup \
    --description "OpenAI API key for SpendSenseAI (sainathyai) - Backup key" \
    --secret-string "$BACKUP_VALUE" \
    --region $REGION

echo "Done! Secrets created with sainathyai identifier."


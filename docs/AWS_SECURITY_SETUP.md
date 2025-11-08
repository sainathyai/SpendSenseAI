# AWS Security Setup Guide

## Overview

This guide explains how to securely configure OpenAI API key access using AWS services. There are two recommended approaches:

1. **AWS Secrets Manager** (Recommended for most cases)
   - Store API key in Secrets Manager
   - Application fetches key on-demand
   - Automatic key rotation support
   - Audit trail in CloudTrail

2. **Lambda Proxy** (Recommended for maximum security)
   - API key never exposed to application
   - Centralized control and rate limiting
   - Request/response transformation
   - Additional security layer

## Option 1: AWS Secrets Manager (Recommended)

### Benefits

- ✅ API key never in code or environment variables
- ✅ Automatic key rotation support
- ✅ Fine-grained IAM access control
- ✅ Audit trail in CloudTrail
- ✅ No extra API calls (fetched on-demand with caching)
- ✅ Works with existing application code

### Setup Steps

#### 1. Create Secret in AWS Secrets Manager

**Using AWS Console:**
1. Go to AWS Secrets Manager
2. Click "Store a new secret"
3. Select "Other type of secret"
4. Add key-value pair: `openai_api_key` = `sk-your-key-here`
5. Secret name: `spendsenseai/openai-api-key`
6. Click "Store"

**Using AWS CLI:**
```bash
aws secretsmanager create-secret \
  --name spendsenseai/openai-api-key \
  --secret-string '{"openai_api_key":"sk-your-key-here"}' \
  --region us-east-1
```

#### 2. Install boto3

```bash
pip install boto3
```

#### 3. Configure IAM Permissions

Create IAM policy for your application:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:spendsenseai/openai-api-key-*"
    }
  ]
}
```

Attach this policy to your EC2 instance role, ECS task role, or Lambda execution role.

#### 4. Configure Application

Update `.env` file:

```env
# Enable AWS Secrets Manager
USE_AWS_SECRETS=true
AWS_SECRET_NAME=spendsenseai/openai-api-key
AWS_REGION=us-east-1

# Optional: Keep OPENAI_API_KEY for local development fallback
OPENAI_API_KEY=sk-your-key-here  # Only used if AWS Secrets fails
```

#### 5. Update Code

The code automatically uses AWS Secrets Manager when `USE_AWS_SECRETS=true`:

```python
from recommend.llm_generator import get_llm_generator

# Automatically fetches from AWS Secrets Manager
generator = get_llm_generator()
rationale = generator.generate_rationale(...)
```

### Local Development

For local development, you can:
1. Use AWS credentials via `aws configure`
2. Or fall back to environment variable (`OPENAI_API_KEY`)
3. The code automatically falls back if AWS Secrets is unavailable

### Key Rotation

AWS Secrets Manager supports automatic rotation:

1. Create rotation Lambda function
2. Configure rotation schedule
3. Update secret value automatically
4. Application code doesn't need changes (caching handles it)

## Option 2: Lambda Proxy (Maximum Security)

### Benefits

- ✅ API key **never** exposed to application
- ✅ Centralized control and rate limiting
- ✅ Request/response transformation
- ✅ Cost tracking and monitoring
- ✅ Additional security layer

### Trade-offs

- ⚠️ Extra latency (~100-200ms per request)
- ⚠️ AWS Lambda costs (~$0.20 per million requests)
- ⚠️ More complex architecture

### Setup Steps

#### 1. Create Lambda Function

**Deploy Lambda function:**

1. Package the Lambda function:
```bash
cd aws/lambda
zip -r openai_proxy.zip openai_proxy.py
# Include dependencies: pip install openai -t .
```

2. Create Lambda function via AWS Console or Terraform (see `aws/terraform/lambda_proxy.tf`)

**Using Terraform:**
```bash
cd aws/terraform
terraform init
terraform plan
terraform apply
```

#### 2. Set Secret in Secrets Manager

```bash
aws secretsmanager put-secret-value \
  --secret-id spendsenseai/openai-api-key \
  --secret-string '{"openai_api_key":"sk-your-key-here"}'
```

#### 3. Configure Lambda Environment

Set Lambda environment variable:
- `OPENAI_SECRET_ARN`: ARN of the secret in Secrets Manager

#### 4. Configure IAM Permissions

Lambda needs:
- `secretsmanager:GetSecretValue` on the secret
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

Application needs:
- `lambda:InvokeFunction` on the Lambda function

#### 5. Configure Application

Update `.env` file:

```env
# Enable Lambda proxy
USE_LAMBDA_PROXY=true
LAMBDA_FUNCTION_NAME=spendsenseai-openai-proxy
AWS_REGION=us-east-1

# AWS credentials (via IAM role or environment)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

#### 6. Update Code

The code automatically uses Lambda proxy when `USE_LAMBDA_PROXY=true`:

```python
from recommend.llm_generator import get_llm_generator

# Automatically uses Lambda proxy
generator = get_llm_generator()
rationale = generator.generate_rationale(...)
```

## Security Comparison

| Aspect | Env Variable | AWS Secrets | Lambda Proxy |
|--------|-------------|-------------|--------------|
| **Key Exposure** | ⚠️ In code/env | ✅ Never exposed | ✅ Never exposed |
| **IAM Control** | ❌ No | ✅ Yes | ✅ Yes |
| **Audit Trail** | ❌ No | ✅ CloudTrail | ✅ CloudTrail |
| **Key Rotation** | ❌ Manual | ✅ Automatic | ✅ Automatic |
| **Rate Limiting** | ❌ No | ❌ No | ✅ Yes |
| **Latency** | ✅ None | ✅ Minimal (cached) | ⚠️ +100-200ms |
| **Cost** | ✅ Free | ✅ Free (usage) | ⚠️ Lambda costs |
| **Complexity** | ✅ Simple | ✅ Simple | ⚠️ Moderate |

## Recommendation

### For Production (AWS):
**Use AWS Secrets Manager** (Option 1)
- Best balance of security and simplicity
- No extra latency
- Works with existing code
- Automatic key rotation

### For Maximum Security:
**Use Lambda Proxy** (Option 2)
- API key never touches application
- Centralized control
- Additional security layer
- Worth the extra latency for sensitive environments

### For Local Development:
**Use Environment Variable**
- Simplest setup
- Fast iteration
- No AWS dependencies

## Cost Estimation

### AWS Secrets Manager:
- **$0.40 per secret per month** (first 10,000 secrets)
- **$0.05 per 10,000 API calls** (GetSecretValue)
- **Total: ~$0.50/month** for typical usage

### Lambda Proxy:
- **$0.20 per million requests** (first 1M free)
- **$0.0000166667 per GB-second** (compute)
- **Total: ~$0.20/month** for 1,000 requests/day

### Comparison:
- **Secrets Manager**: Lower cost, simpler
- **Lambda Proxy**: Slightly higher cost, more features

## Best Practices

1. **Never commit API keys** to code or git
2. **Use IAM roles** instead of access keys when possible
3. **Enable CloudTrail** for audit logging
4. **Rotate keys regularly** (every 90 days)
5. **Use least privilege** IAM policies
6. **Monitor usage** in AWS CloudWatch
7. **Test fallback mechanisms** (local development)

## Troubleshooting

### "Access denied to secret"
- Check IAM permissions
- Verify secret ARN is correct
- Ensure IAM role has `secretsmanager:GetSecretValue` permission

### "Lambda function not found"
- Verify function name matches
- Check AWS region
- Ensure IAM role has `lambda:InvokeFunction` permission

### "API key not found"
- Check secret exists in Secrets Manager
- Verify secret format (JSON with `openai_api_key` key)
- Check fallback to environment variable works

## Migration Path

1. **Start with environment variable** (local development)
2. **Move to AWS Secrets Manager** (production)
3. **Add Lambda proxy** (if maximum security needed)

The code supports all three methods with automatic fallback!


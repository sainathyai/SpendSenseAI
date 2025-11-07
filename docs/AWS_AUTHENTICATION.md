# AWS Authentication Methods

## How the Application Accesses AWS

The application uses **boto3's default credential chain**, which automatically tries these methods in order:

### 1. **Environment Variables** (Local Development)
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_SESSION_TOKEN=your-session-token  # If using temporary credentials
```

### 2. **AWS Credentials File** (`~/.aws/credentials`)
```ini
[default]
aws_access_key_id = your-access-key
aws_secret_access_key = your-secret-key
```

### 3. **AWS Config File** (`~/.aws/config`)
```ini
[default]
region = us-east-1
```

### 4. **IAM Roles** (Production - Recommended)
- **EC2 Instance Role**: Automatically assumed if running on EC2
- **ECS Task Role**: Automatically assumed if running in ECS
- **Lambda Execution Role**: Automatically assumed if running in Lambda
- **IAM Role for Service Accounts**: If using Kubernetes

### 5. **AWS SSO** (Single Sign-On)
- Configured via `aws configure sso`

### 6. **Container Credentials** (ECS/Fargate)
- Automatically retrieved from container metadata

## Current Setup

The code uses boto3's default credential chain:
```python
boto3.client('secretsmanager', region_name='us-east-1')
```

This means it will automatically use:
1. Environment variables if set
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role if running on AWS infrastructure

## For Local Development

**Option 1: AWS CLI Configure**
```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Default region: us-east-1
# Default output format: json
```

**Option 2: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1
```

**Option 3: .env File** (for local development only)
```env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

## For Production (AWS Infrastructure)

**Use IAM Roles** - Never use access keys in production:

### EC2 Instance
1. Create IAM role with `secretsmanager:GetSecretValue` permission
2. Attach role to EC2 instance
3. Application automatically uses role credentials

### ECS/Fargate
1. Create IAM task role with `secretsmanager:GetSecretValue` permission
2. Configure task role in ECS task definition
3. Application automatically uses task role credentials

### Lambda
1. Create IAM execution role with `secretsmanager:GetSecretValue` permission
2. Configure role in Lambda function
3. Application automatically uses execution role credentials

## Required IAM Permissions

The application needs this permission to access Secrets Manager:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:971422717446:secret:openai/sainathyai-*"
    }
  ]
}
```

## Verifying Current Authentication

Check which identity is being used:
```bash
aws sts get-caller-identity
```

This shows:
- Account ID
- User/Role ARN
- Current identity type

## Security Best Practices

1. **Local Development**: Use `aws configure` or environment variables
2. **Production**: Always use IAM roles (never access keys)
3. **Never commit credentials**: Keep `.env` in `.gitignore`
4. **Rotate credentials**: Regularly rotate access keys
5. **Use least privilege**: Only grant `GetSecretValue` permission
6. **Monitor access**: Check CloudTrail for access logs


# IAM Role Setup for sainathyai Projects

## Overview

This guide explains how to set up IAM role-based authentication for sainathyai projects to access AWS Secrets Manager. **This is the recommended approach for production environments.**

**Note**: This IAM role is generic and can be used across all sainathyai projects (SpendSenseAI, etc.)

## Why IAM Roles?

✅ **More Secure**: No access keys to manage or rotate  
✅ **Automatic**: Credentials automatically provided by AWS  
✅ **Auditable**: All access logged in CloudTrail  
✅ **Best Practice**: AWS recommended approach for production

## Setup Methods

### Option 1: Terraform (Recommended)

```bash
cd aws/terraform
terraform init
terraform plan
terraform apply
```

This creates:
- IAM role: `sainathyai-application-role` (generic for all projects)
- IAM policy: `sainathyai-secretsmanager-access`
- Attaches policy to role

### Option 2: CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name sainathyai-iam-role \
  --template-body file://aws/cloudformation/iam_role.yaml \
  --region us-east-1
```

### Option 3: AWS CLI / Console (Manual)

#### Step 1: Create IAM Policy

```bash
aws iam create-policy \
  --policy-name sainathyai-secretsmanager-access \
  --policy-document file://aws/iam/secrets_manager_policy.json \
  --description "Policy for sainathyai projects to access OpenAI API keys from Secrets Manager"
```

Note the Policy ARN from the output.

#### Step 2: Create IAM Role

**For EC2:**
```bash
aws iam create-role \
  --role-name sainathyai-application-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

**For ECS:**
```bash
aws iam create-role \
  --role-name sainathyai-application-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

**For Lambda:**
```bash
aws iam create-role \
  --role-name sainathyai-application-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

#### Step 3: Attach Policy to Role

```bash
aws iam attach-role-policy \
  --role-name sainathyai-application-role \
  --policy-arn <POLICY_ARN_FROM_STEP_1>
```

## Deployment Configuration

### For EC2 Instance

1. **Attach Role to Instance:**
```bash
aws ec2 associate-iam-instance-profile \
  --instance-id i-1234567890abcdef0 \
  --iam-instance-profile Name=sainathyai-instance-profile
```

2. **Create Instance Profile:**
```bash
aws iam create-instance-profile \
  --instance-profile-name sainathyai-instance-profile

aws iam add-role-to-instance-profile \
  --instance-profile-name sainathyai-instance-profile \
  --role-name sainathyai-application-role
```

3. **Application automatically uses role** - no code changes needed!

### For ECS Task

1. **Update Task Definition:**
```json
{
  "taskRoleArn": "arn:aws:iam::971422717446:role/sainathyai-application-role",
  "executionRoleArn": "arn:aws:iam::971422717446:role/ecsTaskExecutionRole"
}
```

2. **Application automatically uses task role** - no code changes needed!

### For Lambda Function

1. **Update Lambda Configuration:**
```bash
aws lambda update-function-configuration \
  --function-name SpendSenseAI-Function \
  --role arn:aws:iam::971422717446:role/sainathyai-application-role
```

2. **Application automatically uses execution role** - no code changes needed!

## Application Code

The application code **doesn't need any changes** - boto3 automatically uses IAM roles when running on AWS infrastructure:

```python
# In aws_secrets.py (line 69)
self._client = boto3.client(
    'secretsmanager',
    region_name=self.region_name
    # No credentials needed - uses IAM role automatically!
)
```

## Verification

### Check if Role is Working

```bash
# On EC2/ECS/Lambda, check metadata:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Should return the role name
```

### Test from Application

```python
import boto3

# Test authentication
sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(f"Using role: {identity['Arn']}")

# Test Secrets Manager access
secrets = boto3.client('secretsmanager')
response = secrets.get_secret_value(SecretId='openai/sainathyai')
print("✓ Successfully accessed secret!")
```

## Local Development

For local development, you can still use AWS credentials:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

The application will automatically use credentials when not running on AWS infrastructure.

## Security Best Practices

1. ✅ **Use IAM roles** in production (not access keys)
2. ✅ **Least privilege** - only grant `GetSecretValue` permission
3. ✅ **Resource-specific** - limit to specific secret ARN pattern
4. ✅ **Monitor access** - check CloudTrail logs
5. ✅ **Rotate secrets** - use Secrets Manager rotation

## Troubleshooting

### "Access Denied" Error

1. Check IAM role is attached to instance/task/function
2. Verify policy is attached to role
3. Check CloudTrail logs for specific error

### "Role Not Found" Error

1. Verify role exists: `aws iam get-role --role-name sainathyai-application-role`
2. Check assume role policy allows the service
3. Verify region matches (us-east-1)

### Testing Locally

If testing locally with IAM role:
1. Use AWS CLI: `aws configure`
2. Or use temporary credentials: `aws sts assume-role`
3. Or set environment variables for local development only


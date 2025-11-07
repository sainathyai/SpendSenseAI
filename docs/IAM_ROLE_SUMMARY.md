# IAM Role Configuration Summary

## ✅ Created Resources

### 1. IAM Policy
- **Name**: `sainathyai-secretsmanager-access`
- **ARN**: `arn:aws:iam::971422717446:policy/sainathyai-secretsmanager-access`
- **Purpose**: Grants access to retrieve OpenAI API keys from Secrets Manager
- **Permissions**:
  - `secretsmanager:GetSecretValue`
  - `secretsmanager:DescribeSecret`
- **Resource**: `arn:aws:secretsmanager:us-east-1:971422717446:secret:openai/sainathyai-*`

### 2. IAM Role
- **Name**: `sainathyai-application-role` (generic for all projects)
- **ARN**: `arn:aws:iam::971422717446:role/sainathyai-application-role`
- **Can be assumed by**:
  - EC2 instances
  - ECS tasks
  - Lambda functions
- **Tags**:
  - Owner: `sainathyai`
  - Purpose: `Secrets Manager Access`

### 3. Policy Attachment
✅ Policy `sainathyai-secretsmanager-access` is attached to role `sainathyai-application-role`

## Usage

### For EC2 Instances
1. Create instance profile:
   ```bash
   aws iam create-instance-profile --instance-profile-name sainathyai-instance-profile
   aws iam add-role-to-instance-profile \
     --instance-profile-name sainathyai-instance-profile \
     --role-name sainathyai-application-role
   ```

2. Attach to EC2 instance:
   ```bash
   aws ec2 associate-iam-instance-profile \
     --instance-id <instance-id> \
     --iam-instance-profile Name=sainathyai-instance-profile
   ```

### For ECS Tasks
Update task definition:
```json
{
  "taskRoleArn": "arn:aws:iam::971422717446:role/sainathyai-application-role"
}
```

### For Lambda Functions
```bash
aws lambda update-function-configuration \
  --function-name <function-name> \
  --role arn:aws:iam::971422717446:role/sainathyai-application-role
```

## Application Behavior

The application code (`recommend/aws_secrets.py`) automatically:
1. ✅ Uses IAM role when running on AWS infrastructure (EC2/ECS/Lambda)
2. ✅ Falls back to credentials file or environment variables for local dev
3. ✅ Logs which authentication method is being used

**No code changes needed** - boto3 handles this automatically!

## Verification

To verify the role is working:
```bash
# Check role exists
aws iam get-role --role-name sainathyai-application-role

# Check attached policies
aws iam list-attached-role-policies --role-name sainathyai-application-role

# Test from application (on EC2/ECS/Lambda)
python -c "import boto3; sts = boto3.client('sts'); print(sts.get_caller_identity())"
```

## Notes

- ⚠️ This role is **generic** and can be used across **all sainathyai projects**
- ✅ No access keys needed - AWS automatically provides temporary credentials
- ✅ More secure than using static access keys
- ✅ All access is logged in CloudTrail for audit purposes


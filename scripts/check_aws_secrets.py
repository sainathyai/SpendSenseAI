"""
Check AWS Secrets Manager configuration and verify secrets exist.

This script:
1. Lists all secrets in AWS Secrets Manager
2. Checks if configured secret names exist
3. Tests retrieval of API keys
4. Verifies ARN and permissions
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    print("ERROR: boto3 not installed. Install with: pip install boto3")
    sys.exit(1)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_all_secrets(region_name: str = "us-east-1"):
    """List all secrets in AWS Secrets Manager."""
    try:
        client = boto3.client('secretsmanager', region_name=region_name)
        
        print("\n" + "=" * 60)
        print("Listing All Secrets in AWS Secrets Manager")
        print("=" * 60)
        
        secrets = []
        paginator = client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page['SecretList']:
                secrets.append(secret)
                print(f"\nSecret Name: {secret['Name']}")
                print(f"  ARN: {secret['ARN']}")
                print(f"  Description: {secret.get('Description', 'N/A')}")
                print(f"  Created: {secret.get('CreatedDate', 'N/A')}")
                print(f"  Last Modified: {secret.get('LastChangedDate', 'N/A')}")
        
        return secrets
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"\nERROR: Access denied. Check IAM permissions.")
            print(f"Required permission: secretsmanager:ListSecrets")
        else:
            print(f"\nERROR: {str(e)}")
        return []
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return []


def check_configured_secrets(secret_names: list, region_name: str = "us-east-1"):
    """Check if configured secrets exist and can be retrieved."""
    try:
        client = boto3.client('secretsmanager', region_name=region_name)
        
        print("\n" + "=" * 60)
        print("Checking Configured Secrets")
        print("=" * 60)
        
        results = []
        
        for secret_name in secret_names:
            print(f"\n{'='*60}")
            print(f"Checking Secret: {secret_name}")
            print(f"{'='*60}")
            
            try:
                # Get secret details
                response = client.describe_secret(SecretId=secret_name)
                
                print(f"✓ Secret exists!")
                print(f"  ARN: {response['ARN']}")
                print(f"  Name: {response['Name']}")
                print(f"  Description: {response.get('Description', 'N/A')}")
                
                # Try to retrieve the secret value
                try:
                    value_response = client.get_secret_value(SecretId=secret_name)
                    secret_string = value_response['SecretString']
                    
                    # Try to parse as JSON
                    try:
                        secret_dict = json.loads(secret_string)
                        print(f"  Format: JSON")
                        print(f"  Keys: {list(secret_dict.keys())}")
                        
                        # Check for API key
                        api_key = (
                            secret_dict.get('openai_api_key') or 
                            secret_dict.get('api_key') or
                            secret_dict.get('OPENAI_API_KEY') or
                            secret_dict.get('key')
                        )
                        
                        if api_key:
                            masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
                            print(f"  ✓ API Key found: {masked_key}")
                            print(f"  Key length: {len(api_key)} characters")
                            results.append({
                                'name': secret_name,
                                'arn': response['ARN'],
                                'status': 'success',
                                'api_key_found': True
                            })
                        else:
                            print(f"  ⚠ API Key not found in secret")
                            print(f"  Available keys: {list(secret_dict.keys())}")
                            results.append({
                                'name': secret_name,
                                'arn': response['ARN'],
                                'status': 'warning',
                                'api_key_found': False
                            })
                    except json.JSONDecodeError:
                        # Plain string
                        print(f"  Format: Plain String")
                        if secret_string.strip():
                            masked_key = f"{secret_string[:7]}...{secret_string[-4:]}" if len(secret_string) > 11 else "***"
                            print(f"  ✓ Secret value found: {masked_key}")
                            print(f"  Value length: {len(secret_string)} characters")
                            results.append({
                                'name': secret_name,
                                'arn': response['ARN'],
                                'status': 'success',
                                'api_key_found': True
                            })
                        else:
                            print(f"  ⚠ Secret is empty")
                            results.append({
                                'name': secret_name,
                                'arn': response['ARN'],
                                'status': 'warning',
                                'api_key_found': False
                            })
                
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'AccessDeniedException':
                        print(f"  ✗ Access denied to retrieve secret value")
                        print(f"  Required permission: secretsmanager:GetSecretValue")
                    else:
                        print(f"  ✗ Error retrieving secret value: {str(e)}")
                    results.append({
                        'name': secret_name,
                        'arn': response['ARN'],
                        'status': 'error',
                        'api_key_found': False,
                        'error': str(e)
                    })
            
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    print(f"  ✗ Secret not found!")
                    print(f"  Check if the name is correct: {secret_name}")
                elif error_code == 'AccessDeniedException':
                    print(f"  ✗ Access denied!")
                    print(f"  Required permission: secretsmanager:DescribeSecret")
                else:
                    print(f"  ✗ Error: {str(e)}")
                results.append({
                    'name': secret_name,
                    'status': 'error',
                    'api_key_found': False,
                    'error': str(e)
                })
            
            except Exception as e:
                print(f"  ✗ Unexpected error: {str(e)}")
                results.append({
                    'name': secret_name,
                    'status': 'error',
                    'api_key_found': False,
                    'error': str(e)
                })
        
        return results
    
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return []


def check_current_configuration():
    """Check current configuration from environment."""
    print("\n" + "=" * 60)
    print("Current Configuration")
    print("=" * 60)
    
    region = os.getenv("AWS_REGION", "us-east-1")
    print(f"AWS Region: {region}")
    
    # Check for multiple secrets
    env_secrets = os.getenv("AWS_SECRET_NAMES", "")
    if env_secrets:
        secret_names = [s.strip() for s in env_secrets.split(",")]
        print(f"AWS_SECRET_NAMES: {env_secrets}")
        print(f"Configured secrets ({len(secret_names)}):")
        for i, name in enumerate(secret_names, 1):
            print(f"  {i}. {name}")
    else:
        single_secret = os.getenv("AWS_SECRET_NAME", "spendsenseai/openai-api-key")
        print(f"AWS_SECRET_NAME: {single_secret}")
        secret_names = [single_secret]
    
    use_aws_secrets = os.getenv("USE_AWS_SECRETS", "true").lower() == "true"
    print(f"USE_AWS_SECRETS: {use_aws_secrets}")
    
    # Check AWS credentials
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key:
        print(f"AWS_ACCESS_KEY_ID: {aws_access_key[:4]}...{aws_access_key[-4:]}")
    else:
        print("AWS_ACCESS_KEY_ID: Not set (using IAM role or default credentials)")
    
    if aws_secret_key:
        print("AWS_SECRET_ACCESS_KEY: *** (set)")
    else:
        print("AWS_SECRET_ACCESS_KEY: Not set (using IAM role or default credentials)")
    
    return secret_names, region


def main():
    """Main function."""
    print("=" * 60)
    print("AWS Secrets Manager Configuration Check")
    print("=" * 60)
    
    # Check current configuration
    secret_names, region = check_current_configuration()
    
    # Check AWS credentials
    print("\n" + "=" * 60)
    print("Checking AWS Credentials")
    print("=" * 60)
    
    try:
        # Try to get caller identity
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"✓ AWS credentials valid!")
        print(f"  Account: {identity.get('Account', 'N/A')}")
        print(f"  User/Role ARN: {identity.get('Arn', 'N/A')}")
    except Exception as e:
        print(f"✗ AWS credentials not configured or invalid: {str(e)}")
        print("\nTo fix:")
        print("  1. Run: aws configure")
        print("  2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("  3. Or use IAM role (if running on EC2/ECS/Lambda)")
        return 1
    
    # List all secrets (optional)
    list_all = input("\nList all secrets in Secrets Manager? (y/n): ").lower() == 'y'
    if list_all:
        all_secrets = list_all_secrets(region)
        if not all_secrets:
            print("\nNo secrets found or access denied.")
    
    # Check configured secrets
    print("\n" + "=" * 60)
    print("Checking Configured Secrets")
    print("=" * 60)
    
    results = check_configured_secrets(secret_names, region)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    warning_count = sum(1 for r in results if r['status'] == 'warning')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Total secrets checked: {len(results)}")
    print(f"✓ Success: {success_count}")
    print(f"⚠ Warning: {warning_count}")
    print(f"✗ Error: {error_count}")
    
    # Show which secrets work
    working_secrets = [r for r in results if r.get('api_key_found', False)]
    if working_secrets:
        print(f"\n✓ Working secrets ({len(working_secrets)}):")
        for r in working_secrets:
            print(f"  - {r['name']} (ARN: {r.get('arn', 'N/A')})")
    
    # Show issues
    issues = [r for r in results if not r.get('api_key_found', False)]
    if issues:
        print(f"\n⚠ Issues found ({len(issues)}):")
        for r in issues:
            print(f"  - {r['name']}: {r.get('error', 'API key not found')}")
    
    # Test actual retrieval using our code
    print("\n" + "=" * 60)
    print("Testing Code Integration")
    print("=" * 60)
    
    try:
        from recommend.aws_secrets import get_openai_api_key_from_aws
        
        api_key = get_openai_api_key_from_aws()
        
        if api_key:
            masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
            print(f"✓ Successfully retrieved API key using code!")
            print(f"  Key (masked): {masked_key}")
            print(f"  Length: {len(api_key)} characters")
            return 0
        else:
            print(f"✗ Failed to retrieve API key using code")
            print(f"  Check configuration and permissions")
            return 1
    
    except Exception as e:
        print(f"✗ Error testing code integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


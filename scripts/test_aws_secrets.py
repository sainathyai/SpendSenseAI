"""
Test script to verify AWS Secrets Manager integration.

This script tests:
- Connection to AWS Secrets Manager
- Retrieval of OpenAI API keys from configured secrets
- Fallback behavior
- Caching functionality
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from recommend.aws_secrets import SecretsManager, get_openai_api_key_from_aws
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_secrets_manager():
    """Test AWS Secrets Manager integration."""
    print("=" * 60)
    print("Testing AWS Secrets Manager Integration")
    print("=" * 60)
    
    # Get secret names from environment
    env_secrets = os.getenv("AWS_SECRET_NAMES", "")
    if env_secrets:
        secret_names = [s.strip() for s in env_secrets.split(",")]
        print(f"\nConfigured secrets (will try in order):")
        for i, name in enumerate(secret_names, 1):
            print(f"  {i}. {name}")
    else:
        single_secret = os.getenv("AWS_SECRET_NAME", "spendsenseai/openai-api-key")
        secret_names = [single_secret]
        print(f"\nConfigured secret: {single_secret}")
    
    # Initialize Secrets Manager
    print(f"\nInitializing Secrets Manager...")
    print(f"Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    
    manager = SecretsManager()
    
    # Test retrieval
    print("\n" + "-" * 60)
    print("Testing API Key Retrieval")
    print("-" * 60)
    
    api_key = manager.get_openai_api_key()
    
    if api_key:
        # Mask the key for display (show first 7 and last 4 chars)
        masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
        print(f"\n✓ Successfully retrieved API key!")
        print(f"  Key (masked): {masked_key}")
        print(f"  Length: {len(api_key)} characters")
        print(f"  Source: {manager._last_successful_secret or 'Unknown'}")
        
        # Test caching
        print("\n" + "-" * 60)
        print("Testing Cache")
        print("-" * 60)
        
        import time
        start_time = time.time()
        cached_key = manager.get_openai_api_key()
        elapsed = (time.time() - start_time) * 1000  # milliseconds
        
        print(f"  Cached retrieval time: {elapsed:.2f}ms")
        print(f"  Keys match: {api_key == cached_key}")
        
        # Test cache invalidation
        print("\n  Invalidating cache...")
        manager.invalidate_cache()
        print("  Cache invalidated")
        
        return True
    else:
        print("\n✗ Failed to retrieve API key")
        print("\nPossible issues:")
        print("  1. AWS credentials not configured")
        print("  2. IAM permissions missing (needs secretsmanager:GetSecretValue)")
        print("  3. Secret names incorrect")
        print("  4. Secrets don't exist in AWS Secrets Manager")
        print("\nTo fix:")
        print("  1. Configure AWS credentials: aws configure")
        print("  2. Check IAM permissions")
        print("  3. Verify secret names in AWS Secrets Manager")
        print("  4. Check AWS_REGION matches your secret location")
        
        return False


def test_environment_variables():
    """Test environment variable fallback."""
    print("\n" + "=" * 60)
    print("Testing Environment Variable Fallback")
    print("=" * 60)
    
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        masked_key = f"{env_key[:7]}...{env_key[-4:]}" if len(env_key) > 11 else "***"
        print(f"\n✓ OPENAI_API_KEY found in environment")
        print(f"  Key (masked): {masked_key}")
        print(f"  Length: {len(env_key)} characters")
        return True
    else:
        print("\n✗ OPENAI_API_KEY not found in environment")
        print("  This is OK if using AWS Secrets Manager")
        return False


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("AWS Secrets Manager Test Suite")
    print("=" * 60)
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    # Test 2: AWS Secrets Manager
    secrets_ok = test_secrets_manager()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Environment Variable: {'✓ OK' if env_ok else '✗ Not found (OK if using AWS)'}")
    print(f"AWS Secrets Manager: {'✓ OK' if secrets_ok else '✗ Failed'}")
    
    if secrets_ok:
        print("\n✓ All tests passed! AWS Secrets Manager is configured correctly.")
        return 0
    elif env_ok:
        print("\n⚠ Using environment variable fallback (not recommended for production)")
        return 0
    else:
        print("\n✗ Tests failed. Please check configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


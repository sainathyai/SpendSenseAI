"""
AWS Secrets Manager Integration for OpenAI API Key.

Provides secure API key retrieval from AWS Secrets Manager:
- On-demand key fetching (never stored in code or env)
- Automatic caching to reduce API calls
- Fallback to environment variable for local development
- IAM-based access control
- Audit trail in CloudTrail
- Supports multiple secrets with fallback (sainathyai-specific and generic)
"""

import os
import json
import time
from typing import Optional
from functools import lru_cache
import logging

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logging.warning("boto3 not installed. AWS Secrets Manager not available. Install with: pip install boto3")


class SecretsManager:
    """AWS Secrets Manager client for secure key retrieval."""
    
    def __init__(
        self,
        secret_names: Optional[list] = None,
        region_name: Optional[str] = None,
        cache_ttl: int = 3600  # 1 hour cache
    ):
        """
        Initialize Secrets Manager client.
        
        Args:
            secret_names: List of secret names to try (default: from env, supports multiple)
            region_name: AWS region (default: from env or us-east-1)
            cache_ttl: Cache TTL in seconds (default: 3600)
        """
        # Support multiple secret names (primary and fallback)
        if secret_names:
            self.secret_names = secret_names
        else:
            # Get from environment - support comma-separated list or single value
            env_secrets = os.getenv("AWS_SECRET_NAMES", "")
            if env_secrets:
                self.secret_names = [s.strip() for s in env_secrets.split(",")]
            else:
                # Fallback to single secret name for backward compatibility
                single_secret = os.getenv("AWS_SECRET_NAME", "openai/sainathyai")
                self.secret_names = [single_secret]
        
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.cache_ttl = cache_ttl
        
        self._client = None
        self._cached_key = None
        self._cache_timestamp = 0
        self._last_successful_secret = None  # Track which secret worked
        
        if AWS_AVAILABLE:
            try:
                # boto3 automatically uses IAM role if running on AWS infrastructure
                # Falls back to credentials file or environment variables for local dev
                self._client = boto3.client(
                    'secretsmanager',
                    region_name=self.region_name
                    # No explicit credentials - uses default credential chain:
                    # 1. IAM role (if on EC2/ECS/Lambda)
                    # 2. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
                    # 3. AWS credentials file (~/.aws/credentials)
                    # 4. AWS config file (~/.aws/config)
                )
                logging.info(f"Initialized AWS Secrets Manager client for region: {self.region_name}")
                
                # Log which authentication method is being used
                # boto3 is already imported at module level if AWS_AVAILABLE is True
                try:
                    if AWS_AVAILABLE:
                        sts = boto3.client('sts')
                        identity = sts.get_caller_identity()
                        if 'role' in identity.get('Arn', '').lower():
                            logging.info(f"Using IAM role: {identity['Arn']}")
                        else:
                            logging.info(f"Using IAM user: {identity['Arn']}")
                except Exception:
                    pass  # Don't fail if we can't check identity
                    
            except Exception as e:
                logging.warning(f"Failed to initialize AWS Secrets Manager: {str(e)}")
                self._client = None
    
    def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key from AWS Secrets Manager with caching.
        Tries multiple secrets in order (primary, fallback).
        
        Returns:
            API key string or None if unavailable
        """
        # Check cache first
        if self._cached_key and (time.time() - self._cache_timestamp) < self.cache_ttl:
            logging.debug(f"Using cached API key from secret: {self._last_successful_secret}")
            return self._cached_key
        
        # Try AWS Secrets Manager - iterate through all secret names
        if self._client:
            for secret_name in self.secret_names:
                try:
                    logging.info(f"Attempting to retrieve secret: {secret_name}")
                    response = self._client.get_secret_value(SecretId=secret_name)
                    
                    # Parse secret (could be JSON or plain string)
                    secret_string = response['SecretString']
                    api_key = None
                    
                    try:
                        secret_dict = json.loads(secret_string)
                        # If JSON, look for common key names (try in order of preference)
                        # Support multiple key formats from different secrets
                        api_key = (
                            secret_dict.get('api_key1') or      # Primary key from openai/api-key
                            secret_dict.get('api_key2') or      # Backup key from openai/api-key
                            secret_dict.get('apiKey') or       # Key from openai/assistant
                            secret_dict.get('openai_api_key') or 
                            secret_dict.get('api_key') or
                            secret_dict.get('OPENAI_API_KEY') or
                            secret_dict.get('key')
                        )
                    except json.JSONDecodeError:
                        # Plain string secret
                        api_key = secret_string.strip()
                    
                    if api_key:
                        self._cached_key = api_key
                        self._cache_timestamp = time.time()
                        self._last_successful_secret = secret_name
                        logging.info(f"Successfully retrieved API key from secret: {secret_name}")
                        return api_key
                    else:
                        logging.warning(f"Secret {secret_name} found but no API key value in it")
                
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'ResourceNotFoundException':
                        logging.warning(f"Secret {secret_name} not found in AWS Secrets Manager, trying next...")
                        continue  # Try next secret
                    elif error_code == 'AccessDeniedException':
                        logging.warning(f"Access denied to secret {secret_name}, trying next...")
                        continue  # Try next secret
                    else:
                        logging.warning(f"Error retrieving secret {secret_name}: {str(e)}, trying next...")
                        continue  # Try next secret
                
                except Exception as e:
                    logging.warning(f"Unexpected error retrieving secret {secret_name}: {str(e)}, trying next...")
                    continue  # Try next secret
            
            # If we get here, all secrets failed
            logging.error(f"Failed to retrieve API key from all secrets: {self.secret_names}")
        
        # Fallback to environment variable (for local development)
        fallback_key = os.getenv("OPENAI_API_KEY")
        if fallback_key:
            logging.info("Using OPENAI_API_KEY from environment variable (fallback)")
            return fallback_key
        
        logging.warning("No OpenAI API key found in AWS Secrets Manager or environment")
        return None
    
    def invalidate_cache(self):
        """Invalidate the cached API key."""
        self._cached_key = None
        self._cache_timestamp = 0


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create global Secrets Manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_openai_api_key_from_aws() -> Optional[str]:
    """
    Get OpenAI API key from AWS Secrets Manager (convenience function).
    
    Returns:
        API key string or None
    """
    manager = get_secrets_manager()
    return manager.get_openai_api_key()


"""
AWS Secrets Manager Integration for OpenAI API Key.

Provides secure API key retrieval from AWS Secrets Manager:
- On-demand key fetching (never stored in code or env)
- Automatic caching to reduce API calls
- Fallback to environment variable for local development
- IAM-based access control
- Audit trail in CloudTrail
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
        secret_name: Optional[str] = None,
        region_name: Optional[str] = None,
        cache_ttl: int = 3600  # 1 hour cache
    ):
        """
        Initialize Secrets Manager client.
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager (default: from env)
            region_name: AWS region (default: from env or us-east-1)
            cache_ttl: Cache TTL in seconds (default: 3600)
        """
        self.secret_name = secret_name or os.getenv("AWS_SECRET_NAME", "spendsenseai/openai-api-key")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.cache_ttl = cache_ttl
        
        self._client = None
        self._cached_key = None
        self._cache_timestamp = 0
        
        if AWS_AVAILABLE:
            try:
                self._client = boto3.client(
                    'secretsmanager',
                    region_name=self.region_name
                )
            except Exception as e:
                logging.warning(f"Failed to initialize AWS Secrets Manager: {str(e)}")
                self._client = None
    
    def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key from AWS Secrets Manager with caching.
        
        Returns:
            API key string or None if unavailable
        """
        # Check cache first
        if self._cached_key and (time.time() - self._cache_timestamp) < self.cache_ttl:
            return self._cached_key
        
        # Try AWS Secrets Manager
        if self._client:
            try:
                response = self._client.get_secret_value(SecretId=self.secret_name)
                
                # Parse secret (could be JSON or plain string)
                secret_string = response['SecretString']
                try:
                    secret_dict = json.loads(secret_string)
                    # If JSON, look for 'openai_api_key' or 'api_key' key
                    api_key = secret_dict.get('openai_api_key') or secret_dict.get('api_key')
                    if api_key:
                        self._cached_key = api_key
                        self._cache_timestamp = time.time()
                        return api_key
                except json.JSONDecodeError:
                    # Plain string secret
                    self._cached_key = secret_string
                    self._cache_timestamp = time.time()
                    return secret_string
            
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    logging.error(f"Secret {self.secret_name} not found in AWS Secrets Manager")
                elif error_code == 'AccessDeniedException':
                    logging.error(f"Access denied to secret {self.secret_name}. Check IAM permissions.")
                else:
                    logging.error(f"Error retrieving secret: {str(e)}")
            
            except Exception as e:
                logging.error(f"Unexpected error retrieving secret: {str(e)}")
        
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


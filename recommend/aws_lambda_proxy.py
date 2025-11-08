"""
AWS Lambda Proxy for OpenAI API Calls.

Provides secure OpenAI API calls through AWS Lambda:
- API key never exposed to client
- Centralized control and rate limiting
- Request/response transformation
- Caching layer
- Cost optimization
"""

import os
import json
import time
from typing import Optional, Dict, Any
import logging

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logging.warning("boto3 not installed. AWS Lambda proxy not available. Install with: pip install boto3")


class LambdaProxy:
    """AWS Lambda proxy for OpenAI API calls."""
    
    def __init__(
        self,
        function_name: Optional[str] = None,
        region_name: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize Lambda proxy client.
        
        Args:
            function_name: Name of the Lambda function (default: from env)
            region_name: AWS region (default: from env or us-east-1)
            timeout: Request timeout in seconds (default: 10)
        """
        self.function_name = function_name or os.getenv("LAMBDA_FUNCTION_NAME", "spendsenseai-openai-proxy")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.timeout = timeout
        
        self._client = None
        
        if AWS_AVAILABLE:
            try:
                self._client = boto3.client(
                    'lambda',
                    region_name=self.region_name
                )
            except Exception as e:
                logging.warning(f"Failed to initialize AWS Lambda client: {str(e)}")
                self._client = None
    
    def invoke_openai(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        model: str = "gpt-4o-mini"
    ) -> Optional[str]:
        """
        Invoke OpenAI API through Lambda proxy.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens
            temperature: Temperature setting
            model: Model name
            
        Returns:
            Generated text or None if failed
        """
        if not self._client:
            logging.error("Lambda client not available")
            return None
        
        try:
            # Prepare payload
            payload = {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "model": model
            }
            
            # Invoke Lambda function
            response = self._client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload),
                Timeout=self.timeout
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                if 'errorMessage' in response_payload:
                    logging.error(f"Lambda error: {response_payload['errorMessage']}")
                    return None
                
                return response_payload.get('text', '')
            else:
                logging.error(f"Lambda invocation failed with status: {response['StatusCode']}")
                return None
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logging.error(f"Lambda function {self.function_name} not found")
            elif error_code == 'AccessDeniedException':
                logging.error(f"Access denied to Lambda function. Check IAM permissions.")
            else:
                logging.error(f"Lambda invocation error: {str(e)}")
            return None
        
        except Exception as e:
            logging.error(f"Unexpected error invoking Lambda: {str(e)}")
            return None


# Global instance
_lambda_proxy: Optional[LambdaProxy] = None


def get_lambda_proxy() -> LambdaProxy:
    """Get or create global Lambda proxy instance."""
    global _lambda_proxy
    if _lambda_proxy is None:
        _lambda_proxy = LambdaProxy()
    return _lambda_proxy


def invoke_openai_via_lambda(
    prompt: str,
    system_prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.7,
    model: str = "gpt-4o-mini"
) -> Optional[str]:
    """
    Invoke OpenAI API through Lambda proxy (convenience function).
    
    Args:
        prompt: User prompt
        system_prompt: System prompt
        max_tokens: Maximum tokens
        temperature: Temperature setting
        model: Model name
        
    Returns:
        Generated text or None
    """
    proxy = get_lambda_proxy()
    return proxy.invoke_openai(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        model=model
    )


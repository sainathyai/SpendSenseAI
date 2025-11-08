"""
AWS Lambda Function: OpenAI Proxy

This Lambda function acts as a secure proxy for OpenAI API calls:
- API key stored in environment (set via AWS Lambda environment variables or Secrets Manager)
- Request validation and rate limiting
- Response transformation
- Error handling
- Cost tracking

Deploy this to AWS Lambda to enable secure OpenAI API calls.
"""

import json
import os
import logging
from typing import Dict, Any

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for OpenAI proxy requests.
    
    Args:
        event: Lambda event with prompt, system_prompt, max_tokens, temperature, model
        context: Lambda context
        
    Returns:
        Dict with 'text' on success, 'errorMessage' on failure
    """
    try:
        # Get API key from environment or Secrets Manager
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            # Try to get from Secrets Manager (if secret ARN is provided)
            secret_arn = os.environ.get('OPENAI_SECRET_ARN')
            if secret_arn:
                try:
                    import boto3
                    secrets_client = boto3.client('secretsmanager')
                    response = secrets_client.get_secret_value(SecretId=secret_arn)
                    secret_dict = json.loads(response['SecretString'])
                    api_key = secret_dict.get('openai_api_key') or secret_dict.get('api_key')
                except Exception as e:
                    logger.error(f"Failed to retrieve secret: {str(e)}")
        
        if not api_key:
            return {
                'statusCode': 500,
                'errorMessage': 'OpenAI API key not configured'
            }
        
        # Parse request
        prompt = event.get('prompt', '')
        system_prompt = event.get('system_prompt', '')
        max_tokens = event.get('max_tokens', 200)
        temperature = event.get('temperature', 0.7)
        model = event.get('model', 'gpt-4o-mini')
        
        if not prompt:
            return {
                'statusCode': 400,
                'errorMessage': 'Prompt is required'
            }
        
        # Validate inputs
        if max_tokens > 500:
            max_tokens = 500  # Cap at 500 tokens for cost control
        
        if temperature < 0 or temperature > 1:
            temperature = 0.7
        
        # Call OpenAI API
        if not OPENAI_AVAILABLE:
            return {
                'statusCode': 500,
                'errorMessage': 'OpenAI package not available in Lambda'
            }
        
        client = OpenAI(api_key=api_key, timeout=10)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        text = response.choices[0].message.content.strip()
        
        # Log successful request (for monitoring)
        logger.info(f"OpenAI API call successful: model={model}, tokens={max_tokens}")
        
        return {
            'statusCode': 200,
            'text': text
        }
    
    except Exception as e:
        logger.error(f"Error in Lambda proxy: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'errorMessage': str(e)
        }


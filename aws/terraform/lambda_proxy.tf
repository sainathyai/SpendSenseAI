# Terraform configuration for OpenAI Lambda Proxy
# Deploy this to create the Lambda function with proper IAM permissions

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Lambda function for OpenAI proxy
resource "aws_lambda_function" "openai_proxy" {
  filename      = "openai_proxy.zip"
  function_name = "spendsenseai-openai-proxy"
  role          = aws_iam_role.lambda_role.arn
  handler       = "openai_proxy.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  environment {
    variables = {
      OPENAI_SECRET_ARN = aws_secretsmanager_secret.openai_key.arn
    }
  }

  # Use Secrets Manager for API key (more secure than env vars)
  # The Lambda function will read from Secrets Manager
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "spendsenseai-openai-proxy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Lambda to read from Secrets Manager
resource "aws_iam_role_policy" "lambda_secrets_policy" {
  name = "lambda-secrets-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.openai_key.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Secrets Manager secret for OpenAI API key
resource "aws_secretsmanager_secret" "openai_key" {
  name        = "spendsenseai/openai-api-key"
  description = "OpenAI API key for SpendSenseAI"
}

# Secret version (you'll need to set this manually after creation)
# Use AWS CLI: aws secretsmanager put-secret-value --secret-id spendsenseai/openai-api-key --secret-string '{"openai_api_key":"sk-your-key-here"}'

# IAM policy for application to invoke Lambda
resource "aws_iam_policy" "invoke_lambda_policy" {
  name        = "invoke-openai-proxy-policy"
  description = "Policy to invoke OpenAI proxy Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.openai_proxy.arn
      }
    ]
  })
}

# Outputs
output "lambda_function_arn" {
  value       = aws_lambda_function.openai_proxy.arn
  description = "ARN of the Lambda function"
}

output "lambda_function_name" {
  value       = aws_lambda_function.openai_proxy.function_name
  description = "Name of the Lambda function"
}


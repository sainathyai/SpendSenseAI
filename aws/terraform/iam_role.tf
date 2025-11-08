# IAM Role for sainathyai projects (generic across all projects)
# This role allows applications to access AWS Secrets Manager

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# IAM Policy for Secrets Manager access
resource "aws_iam_policy" "secrets_manager_policy" {
  name        = "sainathyai-secretsmanager-access"
  description = "Policy for sainathyai projects to access OpenAI API keys from Secrets Manager"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowGetSecretValue"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:us-east-1:971422717446:secret:openai/sainathyai-*"
        ]
      }
    ]
  })
}

# IAM Role for EC2/ECS/Lambda (generic for all sainathyai projects)
resource "aws_iam_role" "sainathyai_role" {
  name = "sainathyai-application-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "ecs-tasks.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        }
      }
    ]
  })
  
  tags = {
    Owner  = "sainathyai"
    Purpose = "Secrets Manager Access"
  }
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "secrets_manager_attachment" {
  role       = aws_iam_role.sainathyai_role.name
  policy_arn = aws_iam_policy.secrets_manager_policy.arn
}

# Outputs
output "iam_role_arn" {
  value       = aws_iam_role.sainathyai_role.arn
  description = "ARN of the IAM role for sainathyai projects"
}

output "iam_role_name" {
  value       = aws_iam_role.sainathyai_role.name
  description = "Name of the IAM role"
}


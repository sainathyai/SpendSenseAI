# OpenAI API Key Setup Guide

## ✅ AWS Configuration Complete

Your AWS credentials have been auto-configured:
- **AWS Account:** 971422717446
- **AWS User:** sainatha.yatham@gmail.com
- **AWS Region:** us-east-1
- **Secrets Manager:** openai/sainathyai (available)
- **CLI Credentials:** ✅ Already configured

## 🔑 Add Your OpenAI API Key

### Step 1: Edit the `.env` file

Open `.env` in your editor and find this line:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 2: Replace with your actual key

Replace `your_openai_api_key_here` with your OpenAI API key:

```env
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_OPENAI_KEY_HERE
```

**Important:** Your key should start with `sk-proj-` or `sk-`

### Step 3: Save the file

The `.env` file is already in `.gitignore`, so your key will NOT be committed to Git.

## 🧪 Verify Configuration

After adding your key, run this test:

```bash
source .venv/Scripts/activate
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

# Check OpenAI key
key = os.getenv('OPENAI_API_KEY', '')
if key and key != 'your_openai_api_key_here':
    print('✅ OpenAI API key configured')
    print(f'   Key starts with: {key[:10]}...')
    print(f'   Key length: {len(key)} characters')
else:
    print('❌ OpenAI API key not configured')
    exit(1)

# Check AWS config
region = os.getenv('AWS_REGION', '')
print(f'✅ AWS Region: {region}')

secret_name = os.getenv('AWS_SECRET_NAMES', '')
print(f'✅ AWS Secret: {secret_name}')

print('\n🎉 All configuration validated!')
"
```

## 🚀 Test LLM Integration

Once configured, test the LLM integration:

```bash
source .venv/Scripts/activate
python -c "
from recommend.llm_generator import test_llm_connection

# This will test the connection and generate a sample rationale
test_llm_connection()
"
```

## 📊 Configuration Options

Your `.env` file has three modes for OpenAI access:

### Mode 1: Direct API Key (Default - Recommended for Local Dev)
```env
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
ENABLE_LLM=true
USE_AWS_SECRETS=false
USE_LAMBDA_PROXY=false
```

### Mode 2: AWS Secrets Manager (For Production)
```env
ENABLE_LLM=true
USE_AWS_SECRETS=true
AWS_SECRET_NAMES=openai/sainathyai
AWS_REGION=us-east-1
```

### Mode 3: AWS Lambda Proxy (Maximum Security)
```env
ENABLE_LLM=true
USE_LAMBDA_PROXY=true
LAMBDA_FUNCTION_NAME=SpendSense-Lambda-dev-ApiLambda91D2282D-JOxDG6UbXD1k
AWS_REGION=us-east-1
```

**Current Setup:** Mode 1 (Direct API Key) is configured by default.

## 🔒 Security Best Practices

1. **Never commit `.env` to Git** - It's already in `.gitignore`
2. **Don't share your API key** - Treat it like a password
3. **Use AWS Secrets Manager for production** - Set `USE_AWS_SECRETS=true`
4. **Rotate keys regularly** - Generate new keys every 90 days
5. **Monitor usage** - Check OpenAI dashboard for unexpected usage

## 💰 Cost Management

The default configuration uses `gpt-4o-mini` which is cost-effective:
- **Model:** gpt-4o-mini
- **Max Tokens:** 200 per request
- **Temperature:** 0.7
- **Estimated Cost:** ~$0.0001 per recommendation

For 190 customers generating recommendations:
- **Cost:** ~$0.02 per full run
- **Monthly (daily updates):** ~$0.60/month

## 🐛 Troubleshooting

### Error: "OpenAI API key not configured"
```bash
# Make sure .env file exists
ls -la .env

# Make sure the key is set correctly
grep OPENAI_API_KEY .env
```

### Error: "Invalid API key"
- Check that your key starts with `sk-proj-` or `sk-`
- Verify the key is active in your OpenAI dashboard
- Make sure there are no extra spaces or quotes

### Error: "Rate limit exceeded"
- OpenAI has rate limits for different tiers
- Add retry logic (already implemented in our code)
- Consider upgrading your OpenAI tier

### Error: "AWS credentials not found"
- Your AWS CLI is already configured, so this shouldn't happen
- If it does, run: `aws configure` to re-setup

## ✨ What Happens Next

Once your key is configured, the system will:

1. **Load environment variables** from `.env`
2. **Try direct API key first** (fastest for local dev)
3. **Fall back to AWS Secrets** if enabled
4. **Fall back to Lambda proxy** if enabled
5. **Fall back to template-based rationales** if all else fails

The fallback system ensures recommendations are ALWAYS generated, even if LLM fails.

## 📝 Next Steps

After configuring your key:

1. ✅ Verify configuration (run test above)
2. 🧪 Test LLM connection
3. 🚀 Run smoke test: `python scripts/smoke_test.py`
4. 📊 Generate recommendations: `curl http://localhost:8000/recommendations/CUST000001`
5. 🎨 View in frontend: Open http://localhost:5173

Happy coding! 🎉




# LLM Integration Guide

## Overview

SpendSenseAI now includes LLM (Large Language Model) integration for tone-controlled text generation. This allows for more natural, personalized rationales while maintaining strict control over tone and avoiding shaming language.

## Features

- **Tone-Controlled Generation**: Generate text with specific tones (supportive, neutral, educational, empowering, gentle)
- **Automatic Fallback**: Falls back to template-based generation if LLM is unavailable
- **Tone Validation**: Validates generated text to ensure no shaming language
- **Cost Optimization**: Uses cost-effective models (gpt-4o-mini) with token limits
- **Configurable**: Fully configurable via environment variables

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `openai>=1.12.0`.

### 2. Configure API Key

Copy the template configuration file:

```bash
cp config.template.env .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=200
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=10
ENABLE_LLM=true
LLM_FALLBACK_TO_TEMPLATES=true
```

### 3. Get OpenAI API Key

1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create a new secret key
4. Copy the key to your `.env` file

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use (gpt-4o-mini is cost-effective) |
| `OPENAI_MAX_TOKENS` | `200` | Maximum tokens per generation |
| `OPENAI_TEMPERATURE` | `0.7` | Creativity level (0.0-1.0) |
| `OPENAI_TIMEOUT` | `10` | API timeout in seconds |
| `ENABLE_LLM` | `true` | Enable/disable LLM generation |
| `LLM_FALLBACK_TO_TEMPLATES` | `true` | Fallback to templates if LLM fails |

## Usage

### Basic Usage

The LLM integration is automatically used when generating recommendations:

```python
from recommend.recommendation_builder import build_recommendations

# LLM will be used automatically if enabled
recommendations = build_recommendations(
    customer_id="CUST000001",
    db_path="data/spendsense.db",
    persona_assignment=persona_assignment
)
```

### Manual Tone Control

You can specify the tone when generating rationales:

```python
from recommend.llm_generator import Tone, generate_rationale_with_llm

rationale = generate_rationale_with_llm(
    recommendation_type="education",
    data_citations={"utilization_percentage": 85.0},
    tone=Tone.GENTLE,  # Use gentle tone for sensitive situations
    persona_type="high_utilization"
)
```

### Tone Options

- **`Tone.SUPPORTIVE`**: Encouraging, helpful, positive
- **`Tone.NEUTRAL`**: Factual, objective, non-judgmental
- **`Tone.EDUCATIONAL`**: Informative, teaching, clear
- **`Tone.EMPOWERING`**: Confidence-building, empowering
- **`Tone.GENTLE`**: Soft, understanding, non-judgmental

### Automatic Tone Selection

The system automatically selects appropriate tones based on persona:

- **Financial Fragility**: Uses `Tone.GENTLE` (softer approach)
- **Savings Builder**: Uses `Tone.EMPOWERING` (celebrates progress)
- **Other Personas**: Uses `Tone.SUPPORTIVE` (default)

## Fallback Behavior

If LLM is unavailable or fails:

1. Falls back to template-based generation
2. Logs the error for debugging
3. Continues operation without interruption

## Cost Considerations

### Model Selection

- **gpt-4o-mini**: Recommended for cost-effectiveness (~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
- **gpt-4**: More expensive but higher quality (use only if needed)

### Token Limits

- Default: 200 tokens per rationale (~150-200 words)
- Adjust via `OPENAI_MAX_TOKENS` in `.env`

### Cost Estimation

For 1,000 recommendations per day:
- **gpt-4o-mini**: ~$0.10-0.20 per day
- **gpt-4**: ~$1.00-2.00 per day

## Tone Validation

All generated text is validated to ensure:

- No shaming language
- No judgmental statements
- No critical personal attacks
- Appropriate tone for financial education

If validation fails, the system automatically falls back to template-based generation.

## Testing

### Test LLM Integration

```python
from recommend.llm_generator import get_llm_generator, Tone

generator = get_llm_generator()
rationale = generator.generate_rationale(
    recommendation_type="education",
    data_citations={"utilization_percentage": 75.0},
    tone=Tone.SUPPORTIVE,
    persona_type="high_utilization"
)
print(rationale)
```

### Test Fallback

Disable LLM to test fallback:

```env
ENABLE_LLM=false
```

The system will automatically use template-based generation.

## Troubleshooting

### API Key Not Found

**Error**: `OpenAI API key not found`

**Solution**: 
1. Check `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. Ensure no extra spaces or quotes around the key

### API Timeout

**Error**: `OpenAI API timeout`

**Solution**:
1. Increase `OPENAI_TIMEOUT` in `.env`
2. Check internet connection
3. Verify API key is valid

### Rate Limits

**Error**: `Rate limit exceeded`

**Solution**:
1. Add retry logic (coming soon)
2. Use caching for repeated requests
3. Upgrade OpenAI plan if needed

### Cost Concerns

**Solution**:
1. Use `gpt-4o-mini` (default)
2. Reduce `OPENAI_MAX_TOKENS`
3. Enable caching for repeated content
4. Monitor usage in OpenAI dashboard

## Security

- **Never commit API keys**: `.env` is gitignored
- **Use environment variables**: Never hardcode keys
- **Rotate keys regularly**: Update keys periodically
- **Monitor usage**: Check OpenAI dashboard for unusual activity

## Best Practices

1. **Always enable fallback**: Set `LLM_FALLBACK_TO_TEMPLATES=true`
2. **Monitor costs**: Check OpenAI dashboard regularly
3. **Test tone validation**: Ensure generated text passes validation
4. **Use appropriate tones**: Match tone to persona and situation
5. **Keep templates updated**: Fallback templates should be accurate

## Future Enhancements

- [ ] Caching for repeated requests
- [ ] Retry logic for API failures
- [ ] Support for other LLM providers (Anthropic, etc.)
- [ ] Fine-tuned models for financial education
- [ ] A/B testing framework for tone effectiveness


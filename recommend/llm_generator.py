"""
LLM Text Generation for SpendSenseAI.

Provides tone-controlled text generation using OpenAI API with:
- Customizable tone prompts
- Fallback to template-based generation
- Cost optimization (caching, token limits)
- Error handling and retries
"""

import os
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import logging

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. LLM generation will fall back to templates.")

# AWS integrations (optional)
try:
    from .aws_secrets import get_openai_api_key_from_aws
    AWS_SECRETS_AVAILABLE = True
except ImportError:
    AWS_SECRETS_AVAILABLE = False

try:
    from .aws_lambda_proxy import invoke_openai_via_lambda
    AWS_LAMBDA_AVAILABLE = True
except ImportError:
    AWS_LAMBDA_AVAILABLE = False


class Tone(str, Enum):
    """Tone options for text generation."""
    SUPPORTIVE = "supportive"  # Encouraging, helpful
    NEUTRAL = "neutral"  # Factual, balanced
    EDUCATIONAL = "educational"  # Informative, teaching
    EMPOWERING = "empowering"  # Confidence-building
    GENTLE = "gentle"  # Soft, non-judgmental


@dataclass
class LLMConfig:
    """Configuration for LLM generation."""
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"  # Cost-effective model
    max_tokens: int = 200
    temperature: float = 0.7  # Balanced creativity
    timeout: int = 10  # seconds
    enable_llm: bool = True
    fallback_to_templates: bool = True
    # Security options
    use_aws_secrets: bool = False  # Use AWS Secrets Manager for API key
    use_lambda_proxy: bool = False  # Use Lambda proxy for API calls


class LLMTextGenerator:
    """LLM text generator with tone control."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM text generator.
        
        Args:
            config: Optional LLMConfig object
        """
        self.config = config or self._load_config()
        self.client = None
        
        # Determine API key source (most secure to least secure)
        api_key = None
        
        if self.config.enable_llm and OPENAI_AVAILABLE:
            # Option 1: AWS Secrets Manager (most secure)
            if self.config.use_aws_secrets and AWS_SECRETS_AVAILABLE:
                api_key = get_openai_api_key_from_aws()
                if api_key:
                    logging.info("Using OpenAI API key from AWS Secrets Manager")
            
            # Option 2: Direct API key (config or env)
            if not api_key:
                if self.config.api_key:
                    api_key = self.config.api_key
                else:
                    api_key = os.getenv("OPENAI_API_KEY")
                    if api_key:
                        logging.info("Using OpenAI API key from environment variable")
            
            # Initialize OpenAI client if we have a key
            if api_key:
                self.client = OpenAI(api_key=api_key, timeout=self.config.timeout)
            else:
                logging.warning("OpenAI API key not found. LLM generation disabled.")
                self.config.enable_llm = False
    
    @staticmethod
    def _load_config() -> LLMConfig:
        """Load configuration from environment variables."""
        return LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY"),  # Only used if AWS Secrets not enabled
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "200")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "10")),
            enable_llm=os.getenv("ENABLE_LLM", "true").lower() == "true",
            fallback_to_templates=os.getenv("LLM_FALLBACK_TO_TEMPLATES", "true").lower() == "true",
            use_aws_secrets=os.getenv("USE_AWS_SECRETS", "false").lower() == "true",
            use_lambda_proxy=os.getenv("USE_LAMBDA_PROXY", "false").lower() == "true"
        )
    
    def _get_tone_prompt(self, tone: Tone) -> str:
        """
        Get tone-specific prompt instructions.
        
        Args:
            tone: Tone enum value
            
        Returns:
            Tone prompt string
        """
        tone_instructions = {
            Tone.SUPPORTIVE: "Use a supportive, encouraging tone. Be helpful and positive without being condescending.",
            Tone.NEUTRAL: "Use a neutral, factual tone. Present information objectively without judgment.",
            Tone.EDUCATIONAL: "Use an educational, informative tone. Explain concepts clearly and helpfully.",
            Tone.EMPOWERING: "Use an empowering, confidence-building tone. Help the user feel capable and in control.",
            Tone.GENTLE: "Use a gentle, non-judgmental tone. Be soft and understanding, avoiding any language that might feel critical or shaming."
        }
        return tone_instructions.get(tone, tone_instructions[Tone.NEUTRAL])
    
    def _build_system_prompt(self, tone: Tone, persona_context: str) -> str:
        """
        Build system prompt for LLM.
        
        Args:
            tone: Tone enum value
            persona_context: Context about the persona
            
        Returns:
            System prompt string
        """
        tone_instruction = self._get_tone_prompt(tone)
        
        return f"""You are a financial education assistant for SpendSenseAI. Your role is to generate clear, helpful rationales for financial recommendations.

Guidelines:
- {tone_instruction}
- Never use shaming, judgmental, or critical language
- Focus on facts and helpful suggestions, not personal judgments
- Be concise (2-3 sentences maximum)
- Use specific numbers and data when provided
- Avoid financial advice - this is educational content only
- Always be respectful and supportive

Persona Context: {persona_context}

Remember: This is educational content, not financial advice. Be helpful, clear, and non-judgmental."""
    
    def _build_user_prompt(
        self,
        recommendation_type: str,
        data_citations: Dict[str, Any],
        content_title: Optional[str] = None,
        content_description: Optional[str] = None,
        offer_title: Optional[str] = None,
        offer_description: Optional[str] = None
    ) -> str:
        """
        Build user prompt with context.
        
        Args:
            recommendation_type: 'education' or 'offer'
            data_citations: Dictionary with supporting data
            content_title: Optional content title
            content_description: Optional content description
            offer_title: Optional offer title
            offer_description: Optional offer description
            
        Returns:
            User prompt string
        """
        prompt = f"Generate a rationale for a {recommendation_type} recommendation.\n\n"
        
        prompt += "Financial Data:\n"
        for key, value in data_citations.items():
            if isinstance(value, (int, float)):
                if 'balance' in key or 'spend' in key or 'amount' in key or 'interest' in key or 'savings' in key:
                    prompt += f"- {key.replace('_', ' ').title()}: ${value:,.2f}\n"
                elif 'percentage' in key or 'rate' in key or 'utilization' in key:
                    prompt += f"- {key.replace('_', ' ').title()}: {value:.1f}%\n"
                else:
                    prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
            else:
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        if recommendation_type == 'education' and content_title:
            prompt += f"\nRecommended Content:\n"
            prompt += f"- Title: {content_title}\n"
            if content_description:
                prompt += f"- Description: {content_description}\n"
        
        elif recommendation_type == 'offer' and offer_title:
            prompt += f"\nRecommended Offer:\n"
            prompt += f"- Title: {offer_title}\n"
            if offer_description:
                prompt += f"- Description: {offer_description}\n"
        
        prompt += "\nGenerate a brief rationale (2-3 sentences) explaining why this recommendation is relevant based on the financial data. Use a supportive, non-judgmental tone."
        
        return prompt
    
    def generate_rationale(
        self,
        recommendation_type: str,
        data_citations: Dict[str, Any],
        tone: Tone = Tone.SUPPORTIVE,
        persona_type: Optional[str] = None,
        content_title: Optional[str] = None,
        content_description: Optional[str] = None,
        offer_title: Optional[str] = None,
        offer_description: Optional[str] = None,
        fallback_generator: Optional[callable] = None
    ) -> str:
        """
        Generate rationale using LLM with tone control.
        
        Args:
            recommendation_type: 'education' or 'offer'
            data_citations: Dictionary with supporting data
            tone: Tone enum value
            persona_type: Optional persona type string
            content_title: Optional content title
            content_description: Optional content description
            offer_title: Optional offer title
            offer_description: Optional offer description
            fallback_generator: Optional fallback function for template-based generation
            
        Returns:
            Generated rationale string
        """
        # Check if LLM is enabled and available
        if not self.config.enable_llm or not self.client:
            if self.config.fallback_to_templates and fallback_generator:
                logging.info("LLM not available, using template-based generation")
                return fallback_generator()
            return "This recommendation is based on your financial behavior."
        
        try:
            # Build prompts
            persona_context = f"User persona: {persona_type}" if persona_type else "User persona: General"
            system_prompt = self._build_system_prompt(tone, persona_context)
            user_prompt = self._build_user_prompt(
                recommendation_type=recommendation_type,
                data_citations=data_citations,
                content_title=content_title,
                content_description=content_description,
                offer_title=offer_title,
                offer_description=offer_description
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            rationale = response.choices[0].message.content.strip()
            
            # Validate tone (basic check)
            if not self._validate_tone(rationale):
                logging.warning("Generated rationale failed tone validation, using fallback")
                if self.config.fallback_to_templates and fallback_generator:
                    return fallback_generator()
            
            return rationale
        
        except Exception as e:
            logging.error(f"LLM generation failed: {str(e)}")
            # Fallback to templates
            if self.config.fallback_to_templates and fallback_generator:
                logging.info("Falling back to template-based generation")
                return fallback_generator()
            return "This recommendation is based on your financial behavior."
    
    def _validate_tone(self, text: str) -> bool:
        """
        Validate that generated text doesn't contain shaming language.
        
        Args:
            text: Text to validate
            
        Returns:
            True if tone is acceptable
        """
        shaming_keywords = [
            "you're overspending",
            "you're wasting money",
            "you should stop",
            "you're irresponsible",
            "you're bad with money",
            "you need to stop",
            "you're overspending",
            "you're terrible",
            "you're failing"
        ]
        
        text_lower = text.lower()
        for keyword in shaming_keywords:
            if keyword in text_lower:
                return False
        
        return True


# Global instance
_llm_generator: Optional[LLMTextGenerator] = None


def get_llm_generator() -> LLMTextGenerator:
    """Get or create global LLM generator instance."""
    global _llm_generator
    if _llm_generator is None:
        _llm_generator = LLMTextGenerator()
    return _llm_generator


def generate_rationale_with_llm(
    recommendation_type: str,
    data_citations: Dict[str, Any],
    tone: Tone = Tone.SUPPORTIVE,
    persona_type: Optional[str] = None,
    content_title: Optional[str] = None,
    content_description: Optional[str] = None,
    offer_title: Optional[str] = None,
    offer_description: Optional[str] = None,
    fallback_generator: Optional[callable] = None
) -> str:
    """
    Generate rationale using LLM with tone control (convenience function).
    
    Args:
        recommendation_type: 'education' or 'offer'
        data_citations: Dictionary with supporting data
        tone: Tone enum value
        persona_type: Optional persona type string
        content_title: Optional content title
        content_description: Optional content description
        offer_title: Optional offer title
        offer_description: Optional offer description
        fallback_generator: Optional fallback function
        
    Returns:
        Generated rationale string
    """
    generator = get_llm_generator()
    return generator.generate_rationale(
        recommendation_type=recommendation_type,
        data_citations=data_citations,
        tone=tone,
        persona_type=persona_type,
        content_title=content_title,
        content_description=content_description,
        offer_title=offer_title,
        offer_description=offer_description,
        fallback_generator=fallback_generator
    )


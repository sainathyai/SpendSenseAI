"""
Education Content Catalog for SpendSenseAI.

Manages educational content library with per-persona content items.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from personas.persona_definition import PersonaType


class ContentType(str, Enum):
    """Content types."""
    ARTICLE = "article"
    GUIDE = "guide"
    CALCULATOR = "calculator"
    CHECKLIST = "checklist"
    TEMPLATE = "template"
    VIDEO = "video"
    TOOL = "tool"


class ContentDifficulty(str, Enum):
    """Content difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class EducationContent:
    """Education content item."""
    content_id: str
    title: str
    description: str
    content_type: ContentType
    target_personas: List[PersonaType]
    difficulty: ContentDifficulty
    estimated_time_minutes: int
    format: str  # e.g., "text", "interactive", "video"
    url: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


# Default content catalog
DEFAULT_CONTENT_CATALOG = {
    # High Utilization Persona Content
    "CONTENT-HU-001": EducationContent(
        content_id="CONTENT-HU-001",
        title="Debt Paydown Strategies: Snowball vs Avalanche Method",
        description="Learn two proven strategies for paying down debt: the snowball method (smallest balance first) and avalanche method (highest interest first). Compare which approach works best for your situation.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.HIGH_UTILIZATION],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="text",
        tags=["debt", "paydown", "strategy"]
    ),
    "CONTENT-HU-002": EducationContent(
        content_id="CONTENT-HU-002",
        title="Balance Transfer Guide: When and How to Use It",
        description="Understand when a balance transfer makes sense, how to evaluate offers, and what to watch out for. Includes calculator to estimate potential savings.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.HIGH_UTILIZATION],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=15,
        format="interactive",
        tags=["balance transfer", "credit cards", "interest"]
    ),
    "CONTENT-HU-003": EducationContent(
        content_id="CONTENT-HU-003",
        title="Setting Up Autopay to Avoid Late Fees",
        description="Step-by-step guide to setting up autopay for credit cards. Learn how to configure minimum payments vs full payments and when to use each.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.HIGH_UTILIZATION],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="text",
        tags=["autopay", "late fees", "payment"]
    ),
    "CONTENT-HU-004": EducationContent(
        content_id="CONTENT-HU-004",
        title="Credit Utilization Calculator",
        description="Interactive calculator to see how reducing your credit utilization impacts your credit score and interest costs. Explore different scenarios.",
        content_type=ContentType.CALCULATOR,
        target_personas=[PersonaType.HIGH_UTILIZATION],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="interactive",
        tags=["calculator", "utilization", "credit score"]
    ),
    "CONTENT-HU-005": EducationContent(
        content_id="CONTENT-HU-005",
        title="Understanding Credit Card Interest: How It Works",
        description="Learn how credit card interest is calculated, what APR means, and how to minimize interest charges. Includes examples with real numbers.",
        content_type=ContentType.ARTICLE,
        target_personas=[PersonaType.HIGH_UTILIZATION],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=12,
        format="text",
        tags=["interest", "apr", "credit cards"]
    ),
    
    # Variable Income Budgeter Persona Content
    "CONTENT-VI-001": EducationContent(
        content_id="CONTENT-VI-001",
        title="Variable Income Budget Template",
        description="Downloadable budget template designed for irregular income. Includes percent-based budgeting and priority-based expense categories.",
        content_type=ContentType.TEMPLATE,
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="downloadable",
        tags=["budget", "template", "variable income"]
    ),
    "CONTENT-VI-002": EducationContent(
        content_id="CONTENT-VI-002",
        title="Emergency Fund Calculator: How Much Do You Need?",
        description="Calculate your emergency fund goal based on your monthly expenses and income variability. Includes personalized recommendations.",
        content_type=ContentType.CALCULATOR,
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="interactive",
        tags=["emergency fund", "calculator", "savings"]
    ),
    "CONTENT-VI-003": EducationContent(
        content_id="CONTENT-VI-003",
        title="Income Smoothing Strategies for Irregular Earners",
        description="Learn techniques to smooth out irregular income, including buffer accounts, percentage-based savings, and expense prioritization.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=15,
        format="text",
        tags=["income smoothing", "irregular income", "strategy"]
    ),
    "CONTENT-VI-004": EducationContent(
        content_id="CONTENT-VI-004",
        title="Percent-Based Budgeting Guide",
        description="How to budget using percentages instead of fixed amounts. Learn the 50/30/20 rule and how to adapt it for variable income.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="text",
        tags=["budgeting", "percent-based", "50/30/20"]
    ),
    "CONTENT-VI-005": EducationContent(
        content_id="CONTENT-VI-005",
        title="Building Your Income Buffer: A Step-by-Step Plan",
        description="Practical steps to build a one-month income buffer when you have irregular pay. Includes realistic timelines and milestones.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=12,
        format="text",
        tags=["buffer", "savings", "plan"]
    ),
    
    # Subscription-Heavy Persona Content
    "CONTENT-SH-001": EducationContent(
        content_id="CONTENT-SH-001",
        title="Subscription Audit Checklist",
        description="Comprehensive checklist to review all your subscriptions. Identify what you're paying for, what you actually use, and what to cancel.",
        content_type=ContentType.CHECKLIST,
        target_personas=[PersonaType.SUBSCRIPTION_HEAVY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=15,
        format="downloadable",
        tags=["subscription", "audit", "checklist"]
    ),
    "CONTENT-SH-002": EducationContent(
        content_id="CONTENT-SH-002",
        title="How to Negotiate Lower Subscription Prices",
        description="Proven strategies for negotiating with subscription services. Includes templates for cancellation calls and retention offers.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.SUBSCRIPTION_HEAVY],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=10,
        format="text",
        tags=["negotiation", "subscription", "savings"]
    ),
    "CONTENT-SH-003": EducationContent(
        content_id="CONTENT-SH-003",
        title="Setting Up Bill Alerts and Reminders",
        description="Learn how to set up alerts for subscription renewals and billing dates. Avoid surprise charges and make informed decisions.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.SUBSCRIPTION_HEAVY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="text",
        tags=["alerts", "billing", "reminders"]
    ),
    "CONTENT-SH-004": EducationContent(
        content_id="CONTENT-SH-004",
        title="Annual Subscription Cost Calculator",
        description="Calculate the true annual cost of all your subscriptions. See how much you're spending per year and identify opportunities to save.",
        content_type=ContentType.CALCULATOR,
        target_personas=[PersonaType.SUBSCRIPTION_HEAVY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="interactive",
        tags=["calculator", "subscription", "cost"]
    ),
    "CONTENT-SH-005": EducationContent(
        content_id="CONTENT-SH-005",
        title="Subscription Alternatives: Free and Low-Cost Options",
        description="Discover free and low-cost alternatives to popular paid subscriptions. Learn how to access similar services without the monthly fees.",
        content_type=ContentType.ARTICLE,
        target_personas=[PersonaType.SUBSCRIPTION_HEAVY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="text",
        tags=["alternatives", "free", "savings"]
    ),
    
    # Savings Builder Persona Content
    "CONTENT-SB-001": EducationContent(
        content_id="CONTENT-SB-001",
        title="Savings Goal Setting Tool",
        description="Interactive tool to set and track savings goals. Calculate how long it will take to reach your goals and adjust your plan.",
        content_type=ContentType.TOOL,
        target_personas=[PersonaType.SAVINGS_BUILDER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="interactive",
        tags=["goal setting", "savings", "planning"]
    ),
    "CONTENT-SB-002": EducationContent(
        content_id="CONTENT-SB-002",
        title="High-Yield Savings Account Comparison Guide",
        description="Compare high-yield savings accounts (HYSAs) from top providers. Learn about APY, minimum balances, and account features.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.SAVINGS_BUILDER],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=15,
        format="text",
        tags=["hysa", "savings", "comparison"]
    ),
    "CONTENT-SB-003": EducationContent(
        content_id="CONTENT-SB-003",
        title="CD Basics: Certificates of Deposit Explained",
        description="Learn about certificates of deposit (CDs) as a savings option. Understand terms, rates, and when CDs make sense for your goals.",
        content_type=ContentType.ARTICLE,
        target_personas=[PersonaType.SAVINGS_BUILDER],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=12,
        format="text",
        tags=["cd", "certificate of deposit", "savings"]
    ),
    "CONTENT-SB-004": EducationContent(
        content_id="CONTENT-SB-004",
        title="Automated Savings Strategies",
        description="Learn how to automate your savings with recurring transfers, round-up apps, and percentage-based savings. Set it and forget it.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.SAVINGS_BUILDER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="text",
        tags=["automation", "savings", "strategy"]
    ),
    "CONTENT-SB-005": EducationContent(
        content_id="CONTENT-SB-005",
        title="Savings Rate Calculator",
        description="Calculate your current savings rate and see how increasing it impacts your goals. Compare different scenarios and timelines.",
        content_type=ContentType.CALCULATOR,
        target_personas=[PersonaType.SAVINGS_BUILDER],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="interactive",
        tags=["calculator", "savings rate", "planning"]
    ),
    
    # Financial Fragility Persona Content
    "CONTENT-FF-001": EducationContent(
        content_id="CONTENT-FF-001",
        title="Fee Avoidance Guide: How to Stop Paying Unnecessary Fees",
        description="Common fees that drain your account and how to avoid them. Learn about overdraft protection, minimum balance fees, and more.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=10,
        format="text",
        tags=["fees", "avoidance", "banking"]
    ),
    "CONTENT-FF-002": EducationContent(
        content_id="CONTENT-FF-002",
        title="Overdraft Protection Options Explained",
        description="Understand different overdraft protection options and how they work. Learn which option is best for your situation.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=8,
        format="text",
        tags=["overdraft", "protection", "banking"]
    ),
    "CONTENT-FF-003": EducationContent(
        content_id="CONTENT-FF-003",
        title="Building a $500 Buffer: Step-by-Step Plan",
        description="Practical steps to build a $500 emergency buffer. Learn how to save small amounts consistently and protect against fees.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=12,
        format="text",
        tags=["buffer", "emergency fund", "plan"]
    ),
    "CONTENT-FF-004": EducationContent(
        content_id="CONTENT-FF-004",
        title="Cash Flow Management for Tight Budgets",
        description="Strategies for managing cash flow when money is tight. Learn about expense timing, bill scheduling, and priority-based spending.",
        content_type=ContentType.GUIDE,
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        difficulty=ContentDifficulty.INTERMEDIATE,
        estimated_time_minutes=15,
        format="text",
        tags=["cash flow", "budget", "management"]
    ),
    "CONTENT-FF-005": EducationContent(
        content_id="CONTENT-FF-005",
        title="Emergency Expense Fund Calculator",
        description="Calculate how much you need in your emergency fund based on your monthly expenses. Set realistic goals and track progress.",
        content_type=ContentType.CALCULATOR,
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        difficulty=ContentDifficulty.BEGINNER,
        estimated_time_minutes=5,
        format="interactive",
        tags=["calculator", "emergency fund", "planning"]
    ),
}


def load_content_catalog(catalog_path: Optional[str] = None) -> Dict[str, EducationContent]:
    """
    Load content catalog from file or return default.
    
    Args:
        catalog_path: Optional path to JSON file with custom content
        
    Returns:
        Dictionary mapping content_id to EducationContent objects
    """
    if catalog_path and Path(catalog_path).exists():
        with open(catalog_path, 'r') as f:
            data = json.load(f)
        
        catalog = {}
        for content_id, content_data in data.items():
            # Convert persona strings to PersonaType enums
            persona_types = [
                PersonaType(p) for p in content_data['target_personas']
            ]
            
            catalog[content_id] = EducationContent(
                content_id=content_data['content_id'],
                title=content_data['title'],
                description=content_data['description'],
                content_type=ContentType(content_data['content_type']),
                target_personas=persona_types,
                difficulty=ContentDifficulty(content_data['difficulty']),
                estimated_time_minutes=content_data['estimated_time_minutes'],
                format=content_data['format'],
                url=content_data.get('url'),
                tags=content_data.get('tags', [])
            )
        
        return catalog
    
    return DEFAULT_CONTENT_CATALOG


def save_content_catalog(catalog: Dict[str, EducationContent], catalog_path: str) -> None:
    """
    Save content catalog to JSON file.
    
    Args:
        catalog: Dictionary mapping content_id to EducationContent objects
        catalog_path: Path to save JSON file
    """
    data = {}
    for content_id, content in catalog.items():
        data[content_id] = {
            'content_id': content.content_id,
            'title': content.title,
            'description': content.description,
            'content_type': content.content_type.value,
            'target_personas': [p.value for p in content.target_personas],
            'difficulty': content.difficulty.value,
            'estimated_time_minutes': content.estimated_time_minutes,
            'format': content.format,
            'url': content.url,
            'tags': content.tags
        }
    
    with open(catalog_path, 'w') as f:
        json.dump(data, f, indent=2)


def get_content_for_persona(
    persona_type: PersonaType,
    catalog: Optional[Dict[str, EducationContent]] = None,
    limit: Optional[int] = None
) -> List[EducationContent]:
    """
    Get educational content for a specific persona.
    
    Args:
        persona_type: PersonaType enum value
        catalog: Optional custom catalog (defaults to DEFAULT_CONTENT_CATALOG)
        limit: Optional limit on number of items to return
        
    Returns:
        List of EducationContent objects for the persona
    """
    if catalog is None:
        catalog = DEFAULT_CONTENT_CATALOG
    
    content_list = [
        content for content in catalog.values()
        if persona_type in content.target_personas
    ]
    
    # If no content found for this persona, get general beginner content
    if not content_list:
        content_list = [
            content for content in catalog.values()
            if content.difficulty.value == 'beginner'
        ]
    
    # Sort by estimated_time_minutes (ascending) for easier content first
    content_list.sort(key=lambda c: c.estimated_time_minutes)
    
    if limit:
        content_list = content_list[:limit]
    
    return content_list


def get_content_by_id(
    content_id: str,
    catalog: Optional[Dict[str, EducationContent]] = None
) -> Optional[EducationContent]:
    """
    Get content by ID.
    
    Args:
        content_id: Content ID
        catalog: Optional custom catalog (defaults to DEFAULT_CONTENT_CATALOG)
        
    Returns:
        EducationContent object or None if not found
    """
    if catalog is None:
        catalog = DEFAULT_CONTENT_CATALOG
    
    return catalog.get(content_id)


def search_content(
    query: str,
    catalog: Optional[Dict[str, EducationContent]] = None,
    persona_type: Optional[PersonaType] = None
) -> List[EducationContent]:
    """
    Search content by title, description, or tags.
    
    Args:
        query: Search query string
        catalog: Optional custom catalog
        persona_type: Optional filter by persona
        
    Returns:
        List of matching EducationContent objects
    """
    if catalog is None:
        catalog = DEFAULT_CONTENT_CATALOG
    
    query_lower = query.lower()
    matches = []
    
    for content in catalog.values():
        # Filter by persona if specified
        if persona_type and persona_type not in content.target_personas:
            continue
        
        # Search in title, description, and tags
        if (query_lower in content.title.lower() or
            query_lower in content.description.lower() or
            any(query_lower in tag.lower() for tag in content.tags)):
            matches.append(content)
    
    return matches


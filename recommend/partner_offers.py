"""
Partner Offer System with Eligibility for SpendSenseAI.

Manages partner product catalog with eligibility rules:
- Product structure (type, provider, requirements, benefits)
- Eligibility rule engine
- Harmful product blacklist
- Offer-persona mapping
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json

from personas.persona_definition import PersonaType
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer


class ProductType(str, Enum):
    """Product types."""
    HYSA = "high_yield_savings_account"
    BALANCE_TRANSFER_CARD = "balance_transfer_card"
    DEBT_CONSOLIDATION_LOAN = "debt_consolidation_loan"
    CREDIT_BUILDER_CARD = "credit_builder_card"
    PERSONAL_LOAN = "personal_loan"
    CD = "certificate_of_deposit"
    MONEY_MARKET = "money_market_account"


@dataclass
class EligibilityRule:
    """Eligibility rule for a product."""
    min_income: Optional[float] = None
    min_credit_score: Optional[int] = None
    max_utilization: Optional[float] = None  # Maximum utilization to be eligible
    min_utilization: Optional[float] = None  # Minimum utilization to be eligible
    requires_existing_account: bool = False
    excludes_existing_account_type: Optional[str] = None  # Don't offer if user has this account type
    persona_requirements: List[PersonaType] = None  # Only eligible for certain personas
    
    def __post_init__(self):
        if self.persona_requirements is None:
            self.persona_requirements = []


@dataclass
class PartnerOffer:
    """Partner product offer."""
    offer_id: str
    product_type: ProductType
    provider: str
    title: str
    description: str
    benefits: List[str]
    requirements: List[str]
    eligibility_rules: EligibilityRule
    target_personas: List[PersonaType]
    is_harmful: bool = False  # True if product is predatory/harmful
    apr: Optional[float] = None  # For loans/credit products
    apy: Optional[float] = None  # For savings products
    minimum_deposit: Optional[float] = None
    url: Optional[str] = None


# Harmful product blacklist
HARMFUL_PRODUCTS = [
    "payday_loan",
    "title_loan",
    "pawn_loan",
    "refund_anticipation_loan"
]


# Default partner offers catalog
DEFAULT_PARTNER_OFFERS = {
    # High Utilization Persona Offers
    "OFFER-HU-001": PartnerOffer(
        offer_id="OFFER-HU-001",
        product_type=ProductType.BALANCE_TRANSFER_CARD,
        provider="Balance Transfer Bank",
        title="Balance Transfer Card with 0% APR",
        description="Transfer your high-interest credit card balances to a card with 0% introductory APR for 18 months. Save on interest while you pay down debt.",
        benefits=[
            "0% APR for 18 months on balance transfers",
            "No annual fee",
            "3% balance transfer fee",
            "Free credit score monitoring"
        ],
        requirements=[
            "Credit score of 650+",
            "Minimum income of $30,000/year",
            "No existing balance transfer card"
        ],
        eligibility_rules=EligibilityRule(
            min_income=30000.0,
            min_credit_score=650,
            min_utilization=30.0,  # Must have some utilization to benefit
            max_utilization=90.0,  # Not too high risk
            excludes_existing_account_type="balance_transfer_card",
            persona_requirements=[PersonaType.HIGH_UTILIZATION]
        ),
        target_personas=[PersonaType.HIGH_UTILIZATION],
        is_harmful=False,
        apr=0.0,  # 0% introductory
        url="https://example.com/balance-transfer"
    ),
    
    "OFFER-HU-002": PartnerOffer(
        offer_id="OFFER-HU-002",
        product_type=ProductType.DEBT_CONSOLIDATION_LOAN,
        provider="Consolidation Lenders",
        title="Debt Consolidation Loan",
        description="Consolidate multiple credit card debts into a single loan with a lower interest rate. Simplify your payments and save on interest.",
        benefits=[
            "Lower interest rate than credit cards",
            "Single monthly payment",
            "Fixed repayment term",
            "No prepayment penalty"
        ],
        requirements=[
            "Credit score of 680+",
            "Minimum income of $40,000/year",
            "Debt-to-income ratio < 50%"
        ],
        eligibility_rules=EligibilityRule(
            min_income=40000.0,
            min_credit_score=680,
            min_utilization=40.0,
            persona_requirements=[PersonaType.HIGH_UTILIZATION]
        ),
        target_personas=[PersonaType.HIGH_UTILIZATION],
        is_harmful=False,
        apr=12.99,
        url="https://example.com/debt-consolidation"
    ),
    
    # Variable Income Budgeter Offers
    "OFFER-VI-001": PartnerOffer(
        offer_id="OFFER-VI-001",
        product_type=ProductType.HYSA,
        provider="High-Yield Savings Bank",
        title="High-Yield Savings Account (4.5% APY)",
        description="Build your emergency fund with a high-yield savings account. Earn competitive interest while keeping your money accessible.",
        benefits=[
            "4.5% APY (much higher than traditional savings)",
            "No monthly fees",
            "No minimum balance after initial deposit",
            "FDIC insured"
        ],
        requirements=[
            "Minimum initial deposit of $100",
            "No existing HYSA account"
        ],
        eligibility_rules=EligibilityRule(
            excludes_existing_account_type="high_yield_savings_account",
            persona_requirements=[PersonaType.VARIABLE_INCOME_BUDGETER]
        ),
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        is_harmful=False,
        apy=4.5,
        minimum_deposit=100.0,
        url="https://example.com/hysa"
    ),
    
    # Savings Builder Offers
    "OFFER-SB-001": PartnerOffer(
        offer_id="OFFER-SB-001",
        product_type=ProductType.HYSA,
        provider="Premium Savings Bank",
        title="Premium High-Yield Savings Account (5.0% APY)",
        description="Maximize your savings with our premium high-yield savings account. Perfect for building long-term savings goals.",
        benefits=[
            "5.0% APY (competitive rate)",
            "No monthly fees",
            "No minimum balance",
            "Easy transfers and mobile app"
        ],
        requirements=[
            "No existing premium HYSA"
        ],
        eligibility_rules=EligibilityRule(
            excludes_existing_account_type="high_yield_savings_account",
            persona_requirements=[PersonaType.SAVINGS_BUILDER]
        ),
        target_personas=[PersonaType.SAVINGS_BUILDER],
        is_harmful=False,
        apy=5.0,
        url="https://example.com/premium-hysa"
    ),
    
    "OFFER-SB-002": PartnerOffer(
        offer_id="OFFER-SB-002",
        product_type=ProductType.CD,
        provider="CD Providers",
        title="12-Month Certificate of Deposit (4.8% APY)",
        description="Lock in a competitive rate with a 12-month CD. Earn guaranteed returns on your savings.",
        benefits=[
            "4.8% APY guaranteed for 12 months",
            "FDIC insured",
            "Fixed rate",
            "No monthly fees"
        ],
        requirements=[
            "Minimum deposit of $1,000",
            "Hold funds for 12 months"
        ],
        eligibility_rules=EligibilityRule(
            min_income=25000.0,
            persona_requirements=[PersonaType.SAVINGS_BUILDER]
        ),
        target_personas=[PersonaType.SAVINGS_BUILDER],
        is_harmful=False,
        apy=4.8,
        minimum_deposit=1000.0,
        url="https://example.com/cd"
    ),
    
    # Financial Fragility Offers
    "OFFER-FF-001": PartnerOffer(
        offer_id="OFFER-FF-001",
        product_type=ProductType.CREDIT_BUILDER_CARD,
        provider="Credit Builder Bank",
        title="Secured Credit Builder Card",
        description="Build credit with a secured credit card. Perfect for building credit history and improving your credit score.",
        benefits=[
            "Reports to all three credit bureaus",
            "No credit check required",
            "Low deposit required",
            "Credit limit increase after 6 months of on-time payments"
        ],
        requirements=[
            "Security deposit of $200-$500",
            "No recent bankruptcies"
        ],
        eligibility_rules=EligibilityRule(
            persona_requirements=[PersonaType.FINANCIAL_FRAGILITY]
        ),
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        is_harmful=False,
        url="https://example.com/credit-builder"
    ),
}


def check_eligibility(
    offer: PartnerOffer,
    customer_id: str,
    db_path: str,
    persona_type: Optional[PersonaType] = None,
    estimated_income: float = 0.0,
    estimated_credit_score: int = 700
) -> tuple[bool, List[str]]:
    """
    Check if customer is eligible for an offer.
    
    Args:
        offer: PartnerOffer object
        customer_id: Customer ID
        db_path: Path to SQLite database
        persona_type: Assigned persona type
        estimated_income: Estimated annual income
        estimated_credit_score: Estimated credit score (simulated for synthetic data)
        
    Returns:
        Tuple of (is_eligible, reasons)
    """
    reasons = []
    is_eligible = True
    
    rules = offer.eligibility_rules
    
    # Check if product is harmful
    if offer.is_harmful:
        return False, ["Product is on harmful product blacklist"]
    
    # Check persona requirements
    if rules.persona_requirements:
        if persona_type and persona_type not in rules.persona_requirements:
            return False, [f"Persona {persona_type.value} not eligible for this offer"]
    
    # Check minimum income
    if rules.min_income and estimated_income < rules.min_income:
        is_eligible = False
        reasons.append(f"Income ${estimated_income:.0f} below minimum ${rules.min_income:.0f}")
    
    # Check credit score
    if rules.min_credit_score and estimated_credit_score < rules.min_credit_score:
        is_eligible = False
        reasons.append(f"Credit score {estimated_credit_score} below minimum {rules.min_credit_score}")
    
    # Check credit utilization
    card_metrics, agg_metrics = analyze_credit_utilization_for_customer(customer_id, db_path, 30)
    
    if card_metrics:
        aggregate_utilization = agg_metrics.aggregate_utilization
        
        if rules.max_utilization and aggregate_utilization > rules.max_utilization:
            is_eligible = False
            reasons.append(f"Utilization {aggregate_utilization:.1f}% exceeds maximum {rules.max_utilization:.1f}%")
        
        if rules.min_utilization and aggregate_utilization < rules.min_utilization:
            is_eligible = False
            reasons.append(f"Utilization {aggregate_utilization:.1f}% below minimum {rules.min_utilization:.1f}%")
    
    # Check existing accounts
    if rules.excludes_existing_account_type:
        accounts = get_accounts_by_customer(customer_id, db_path)
        
        # Check if user already has this account type
        account_type_mapping = {
            "high_yield_savings_account": ["savings", "money market"],
            "balance_transfer_card": ["credit"]
        }
        
        excluded_types = account_type_mapping.get(rules.excludes_existing_account_type, [])
        
        for account in accounts:
            if account.subtype.value in excluded_types:
                # For savings accounts, check if it's already a HYSA
                if account.subtype.value == "savings" and account.balances.current > 0:
                    is_eligible = False
                    reasons.append(f"User already has {rules.excludes_existing_account_type}")
                    break
    
    return is_eligible, reasons


def get_eligible_offers_for_persona(
    persona_type: PersonaType,
    customer_id: str,
    db_path: str,
    offers_catalog: Optional[Dict[str, PartnerOffer]] = None,
    estimated_income: float = 0.0,
    estimated_credit_score: int = 700
) -> List[PartnerOffer]:
    """
    Get eligible offers for a persona.
    
    Args:
        persona_type: PersonaType enum value
        customer_id: Customer ID
        db_path: Path to SQLite database
        offers_catalog: Optional custom catalog
        estimated_income: Estimated annual income
        estimated_credit_score: Estimated credit score
        
    Returns:
        List of eligible PartnerOffer objects
    """
    if offers_catalog is None:
        offers_catalog = DEFAULT_PARTNER_OFFERS
    
    # Filter offers by persona
    persona_offers = [
        offer for offer in offers_catalog.values()
        if persona_type in offer.target_personas
    ]
    
    # Check eligibility for each offer
    eligible_offers = []
    for offer in persona_offers:
        is_eligible, reasons = check_eligibility(
            offer, customer_id, db_path, persona_type,
            estimated_income, estimated_credit_score
        )
        
        if is_eligible:
            eligible_offers.append(offer)
    
    # Sort by relevance (prefer lower APR for loans, higher APY for savings)
    def sort_key(offer):
        if offer.apr is not None:
            return offer.apr  # Lower APR is better
        elif offer.apy is not None:
            return -offer.apy  # Higher APY is better (negative for descending)
        else:
            return 0
    
    eligible_offers.sort(key=sort_key)
    
    return eligible_offers


def load_partner_offers(offers_path: Optional[str] = None) -> Dict[str, PartnerOffer]:
    """
    Load partner offers from file or return default.
    
    Args:
        offers_path: Optional path to JSON file with custom offers
        
    Returns:
        Dictionary mapping offer_id to PartnerOffer objects
    """
    if offers_path and Path(offers_path).exists():
        with open(offers_path, 'r') as f:
            data = json.load(f)
        
        offers = {}
        for offer_id, offer_data in data.items():
            # Convert eligibility rules
            rule_data = offer_data['eligibility_rules']
            eligibility_rule = EligibilityRule(
                min_income=rule_data.get('min_income'),
                min_credit_score=rule_data.get('min_credit_score'),
                max_utilization=rule_data.get('max_utilization'),
                min_utilization=rule_data.get('min_utilization'),
                requires_existing_account=rule_data.get('requires_existing_account', False),
                excludes_existing_account_type=rule_data.get('excludes_existing_account_type'),
                persona_requirements=[PersonaType(p) for p in rule_data.get('persona_requirements', [])]
            )
            
            offer = PartnerOffer(
                offer_id=offer_data['offer_id'],
                product_type=ProductType(offer_data['product_type']),
                provider=offer_data['provider'],
                title=offer_data['title'],
                description=offer_data['description'],
                benefits=offer_data['benefits'],
                requirements=offer_data['requirements'],
                eligibility_rules=eligibility_rule,
                target_personas=[PersonaType(p) for p in offer_data['target_personas']],
                is_harmful=offer_data.get('is_harmful', False),
                apr=offer_data.get('apr'),
                apy=offer_data.get('apy'),
                minimum_deposit=offer_data.get('minimum_deposit'),
                url=offer_data.get('url')
            )
            
            offers[offer_id] = offer
        
        return offers
    
    return DEFAULT_PARTNER_OFFERS


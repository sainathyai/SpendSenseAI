# Partner Offers: Current State & Expansion Plan

## Current State ✅

**Total Offers:** 6 active offers
**Distribution by Persona:**
- Financial Fragility: 1 offer
- High Utilization: 2 offers  
- Savings Builder: 2 offers
- Variable Income: 1 offer
- Subscription Heavy: 0 offers (❌ needs offers)

## Offers Currently Available

### High Utilization (2 offers)
1. **OFFER-HU-001**: Balance Transfer Card (0% APR, 18 months)
2. **OFFER-HU-002**: Debt Consolidation Loan (12.99% APR)

### Variable Income (1 offer)
1. **OFFER-VI-001**: High-Yield Savings Account (4.5% APY)

### Savings Builder (2 offers)
1. **OFFER-SB-001**: High-Yield Savings Account (4.5% APY)
2. **OFFER-SB-002**: Certificate of Deposit (4.8% APY, 12-month)

### Financial Fragility (1 offer)
1. **OFFER-FF-001**: Secured Credit Builder Card

### Subscription Heavy (0 offers)
❌ **Missing** - Needs to be added

## Recommended Additional Offers

### High Utilization (Add 3-4 more)
- **OFFER-HU-003**: Low APR Credit Card (10.99% APR, for consolidation)
- **OFFER-HU-004**: Credit Counseling Service (non-profit, free consultation)
- **OFFER-HU-005**: Balance Transfer Card #2 (alternative provider, 0% for 15 months)
- **OFFER-HU-006**: Secured Credit Card (for rebuilding credit)

### Variable Income Budgeter (Add 4-5 more)
- **OFFER-VI-002**: YNAB Budgeting App (percent-based budgeting)
- **OFFER-VI-003**: Empower Personal Dashboard (income tracking)
- **OFFER-VI-004**: High-Yield Checking Account (no minimum balance)
- **OFFER-VI-005**: Income Smoothing Service (Even app-style)
- **OFFER-VI-006**: Financial Buffer Loan (short-term, low-interest)

### Subscription Heavy (Add 5-6 NEW)
- **OFFER-SH-001**: Rocket Money (subscription management & cancellation)
- **OFFER-SH-002**: Truebill (subscription tracker & negotiation)
- **OFFER-SH-003**: Trim (automatic subscription cancellation)
- **OFFER-SH-004**: Bundle Deals (streaming services bundled discount)
- **OFFER-SH-005**: Negotiation Service (bill negotiation for existing subscriptions)
- **OFFER-SH-006**: Virtual Assistant Service (for managing subscriptions)

### Savings Builder (Add 3-4 more)
- **OFFER-SB-003**: Robo-Advisor (Betterment/Wealthfront for investing)
- **OFFER-SB-004**: High-Yield CD (18-month, 5.0% APY)
- **OFFER-SB-005**: Money Market Account (4.3% APY, check writing)
- **OFFER-SB-006**: I-Bonds (inflation-protected savings bonds)

### Financial Fragility (Add 4-5 more)
- **OFFER-FF-002**: Fee-Free Checking Account (no overdraft fees)
- **OFFER-FF-003**: Chime/Dave Advance (short-term cash advance, $0 interest)
- **OFFER-FF-004**: Overdraft Protection Line (low-cost protection)
- **OFFER-FF-005**: Credit Counseling (free consultation for debt management)
- **OFFER-FF-006**: Emergency Savings Account (low minimum, high APY)

## Implementation Status

### Phase 1: Core Offers (Complete ✅)
- 6 functional offers across 4 personas
- Eligibility system working
- Integration with recommendation engine working

### Phase 2: Subscription Heavy Offers (Priority)
- 0 offers currently
- High priority to add 3-5 offers
- Recommended: Rocket Money, Truebill, Trim

### Phase 3: Full Expansion (Future)
- Target: 5-7 offers per persona
- Total target: 25-35 offers
- Time estimate: 4-6 hours

## Testing Current Offers

```bash
source .venv/Scripts/activate

# Test offers for a customer
python -c "
from recommend.partner_offers import get_eligible_offers_for_persona, PersonaType

# Test for High Utilization persona
offers = get_eligible_offers_for_persona(
    PersonaType.HIGH_UTILIZATION,
    'CUST000001',
    'data/spendsense.db',
    estimated_income=50000,
    estimated_credit_score=700
)

print(f'Eligible offers: {len(offers)}')
for offer in offers:
    print(f'  - {offer.title} ({offer.provider})')
"
```

## Quick Wins

If adding more offers, prioritize:
1. **Subscription Heavy**: Add 3-5 offers (currently 0)
2. **Variable Income**: Add 2-3 budgeting apps
3. **Financial Fragility**: Add fee-free checking and cash advance options

## Notes

- Current system is functional with 6 offers
- Eligibility checking works correctly
- Integration with recommendations works
- Main gap: Subscription Heavy persona has no offers
- Expansion is incremental - system works with current offers

## Future Enhancements

1. **Dynamic Offer Loading**: Load offers from external API or database
2. **A/B Testing**: Test different offers for same persona
3. **Offer Personalization**: Rank offers based on user behavior
4. **Partner Integration**: Real partner APIs for real-time offers
5. **Offer Expiration**: Time-limited promotional offers
6. **Conversion Tracking**: Track which offers users accept




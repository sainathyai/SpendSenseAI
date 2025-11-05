# SpendSenseAI

**From Plaid to Personalized Learning: An Explainable Financial Recommendation Engine**

## Overview

SpendSenseAI is a consent-aware, explainable AI system that analyzes Plaid-style transaction data to detect behavioral patterns, assign financial personas, and deliver personalized financial education with strict guardrails around consent, eligibility, and tone.

### Core Principles
- 🔍 **Transparency over sophistication**
- 🎯 **User control over automation**
- 📚 **Education over sales**
- ⚖️ **Fairness built in from day one**

## Features

- **Behavioral Signal Detection**: Identifies subscriptions, savings patterns, credit utilization, and income stability
- **Persona Assignment**: Classifies users into 5 financial personas with clear, documented criteria
- **Personalized Recommendations**: Delivers 3-5 educational items and 1-3 partner offers with plain-language rationales
- **Consent Management**: Explicit opt-in/opt-out with enforcement before any recommendations
- **Operator Dashboard**: Human oversight interface for reviewing and overriding AI decisions
- **Decision Tracing**: Complete audit trail for every recommendation with data citations
- **Eligibility Guardrails**: Filters out ineligible or harmful products

## Architecture

### Modular Structure
- **ingest/** - Data loading and validation
- **features/** - Signal detection and feature engineering
- **personas/** - Persona assignment logic
- **recommend/** - Recommendation engine
- **guardrails/** - Consent, eligibility, and tone checks
- **ui/** - Operator view and user experience
- **eval/** - Evaluation harness
- **docs/** - Decision log and schema documentation

### Technology Stack
- **Backend**: Python 3.9+
- **Database**: SQLite (local storage)
- **Analytics**: Pandas, NumPy
- **API**: FastAPI or Flask
- **Testing**: pytest
- **UI**: Streamlit or React (TBD)

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Run the application

Detailed setup instructions coming in future PRs.

## Project Status

**Current Phase**: Foundation & Setup (PR #1)

### Completed
- ✅ Repository initialization
- ✅ Directory structure
- ✅ Basic documentation

### In Progress
- 🔄 Data schema definition
- 🔄 Synthetic data generation

### Upcoming
- ⏳ Feature engineering
- ⏳ Persona system
- ⏳ Recommendation engine
- ⏳ Operator dashboard

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Persona Coverage | 100% | Pending |
| Behaviors Detected | ≥3 per user | Pending |
| Rationale Coverage | 100% | Pending |
| Decision Traces | 100% | Pending |
| Latency | <5s per user | Pending |
| Unit Tests | ≥10 passing | Pending |
| Consent Enforcement | 100% | Pending |

## 5 Financial Personas

1. **High Utilization**: Users with credit utilization ≥50% or debt concerns
2. **Variable Income Budgeter**: Users with irregular income and low cash-flow buffer
3. **Subscription-Heavy**: Users with ≥3 recurring subscriptions totaling significant spend
4. **Savings Builder**: Users with consistent savings growth and healthy credit
5. **Financial Fragility** (Custom): Users at risk of overdrafts or with persistently low balances

## Compliance & Ethics

### Guardrails
- **Not Financial Advice**: All recommendations include mandatory disclaimer
- **Consent-First**: No data processing without explicit user opt-in
- **Tone Validation**: No shaming or judgmental language
- **Eligibility Filters**: Prevents recommendations for ineligible products
- **Harm Prevention**: Actively excludes predatory financial products

### Privacy
- Synthetic data only (no real PII)
- Operator access logged and audited
- User data never shared externally
- Consent can be revoked at any time

## Documentation

- **Platinum Project_ Peak6_SpendSense.md** - Original PRD from Peak6
- **SpendSenseAI_Project_Analysis.md** - Detailed analysis of challenges and nuances
- **PR_by_PR_Implementation_Plan.md** - Complete 30-PR roadmap
- **QUICK_REFERENCE.md** - Quick reference guide
- **PR_DEPENDENCY_ROADMAP.md** - Visual workflow and dependencies
- **docs/decision_log.md** - Design decisions and rationale (coming soon)

## Contributing

This is an individual/small team project for Peak6's Platinum Challenge.

### Development Workflow
- Create feature branches: `pr-###-feature-name`
- Small related PRs can be combined in one branch
- All code must pass tests before merging
- Maintain 100% decision trace coverage

## Testing

Run tests with pytest (setup coming in future PRs).

## License

This project is for educational and demonstration purposes.

## Contact

**Project Sponsor**: Bryce Harris - bharris@peak6.com

## Disclaimer

**This is educational content, not financial advice. Consult a licensed financial advisor for personalized guidance.**

---

**Build systems people can trust with their financial data.**


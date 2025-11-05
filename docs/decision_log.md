# SpendSenseAI Decision Log

This document records all major design decisions, rationale, and trade-offs made during development.

## Purpose

Maintaining a decision log ensures:
- Transparency in design choices
- Context for future maintainers
- Auditability for regulators
- Learning from past decisions

---

## PR #1: Project Setup (2025-11-05)

### Decision 1: Python as Primary Language
**Chosen:** Python 3.9+

**Rationale:**
- Excellent data processing libraries (pandas, numpy)
- Strong ML/AI ecosystem for future extensions
- Rapid prototyping capabilities
- Good for building APIs (FastAPI)
- Team familiarity

**Alternatives Considered:**
- Node.js/TypeScript: Good for APIs, less mature for data processing
- Go: Fast but longer development time
- Java: Verbose, slower iteration

**Trade-offs:**
- Performance: Python slower than compiled languages
- Acceptable: <5s latency target is achievable
- Deployment: Requires Python runtime

### Decision 2: SQLite for Database
**Chosen:** SQLite

**Rationale:**
- PRD requirement for local storage
- No external dependencies
- Easy setup (one-command)
- Sufficient for 50-100 users
- Good SQL support
- File-based, portable

**Alternatives Considered:**
- PostgreSQL: More powerful but requires server setup
- MongoDB: NoSQL flexibility but adds complexity
- In-memory only: Fast but no persistence

**Trade-offs:**
- Scalability: Limited to single-node
- Acceptable: Project scope is local/demo
- Concurrency: Limited write concurrency
- Acceptable: Single-threaded recommendation generation

### Decision 3: Modular Architecture
**Chosen:** Separate directories for each concern

**Structure:**
- `ingest/` - Data loading
- `features/` - Signal detection
- `personas/` - Persona assignment
- `recommend/` - Recommendations
- `guardrails/` - Safety/compliance
- `ui/` - Interfaces
- `eval/` - Metrics

**Rationale:**
- Clear separation of concerns
- Easier testing (mock dependencies)
- Team can work on modules independently
- Easier to understand codebase
- PRD explicitly recommends this

**Alternatives Considered:**
- Monolithic: All code in one file/module
- Microservices: Separate services per module

**Trade-offs:**
- Complexity: More files to manage
- Benefit: Much clearer organization
- Import overhead: Minimal for Python

### Decision 4: FastAPI for REST API
**Chosen:** FastAPI (tentative, can switch to Flask)

**Rationale:**
- Modern, async support
- Automatic API documentation (OpenAPI)
- Type hints integration (Pydantic)
- Fast development
- Good for demos

**Alternatives Considered:**
- Flask: Simpler, more mature, synchronous
- Django: Too heavy for this project
- Plain HTTP server: Too low-level

**Trade-offs:**
- Learning curve: FastAPI newer than Flask
- Documentation: Excellent auto-generated docs
- Performance: Async is overkill but future-proof

**Note:** May switch to Flask if FastAPI adds unnecessary complexity

### Decision 5: Pytest for Testing
**Chosen:** pytest

**Rationale:**
- Most popular Python testing framework
- Simple syntax
- Excellent fixture support
- Good coverage tools
- Parametrized testing
- Community support

**Alternatives Considered:**
- unittest: Standard library but verbose
- nose2: Less actively maintained

**Trade-offs:**
- External dependency vs standard library
- Benefits outweigh minimal dependency cost

### Decision 6: Synthetic Data Only
**Chosen:** No real PII, generated synthetic data

**Rationale:**
- Privacy compliance (no risk)
- Controlled diversity (can ensure edge cases)
- Reproducible (seeded generation)
- No data acquisition needed
- PRD requirement

**Alternatives Considered:**
- Anonymized real data: Privacy risks, acquisition challenges
- Public datasets: May not match Plaid schema

**Trade-offs:**
- Realism: Synthetic data may miss real-world patterns
- Mitigation: Generate based on realistic distributions
- Privacy: Zero risk with synthetic data

### Decision 7: Git Branch Strategy
**Chosen:** Feature branches named `pr-###-feature-name`

**Rationale:**
- Clear connection to PR numbers
- Easy to track work
- Can combine small related PRs in one branch
- Standard practice

**Alternatives Considered:**
- Git Flow: Too complex for solo/small team
- Trunk-based: Prefer isolated feature development

**Trade-offs:**
- Branch management overhead
- Acceptable: Clear organization is worth it

---

## Template for Future Decisions

### Decision X: [Title]
**Chosen:** [What was chosen]

**Rationale:**
- [Why this choice]
- [Benefits]
- [Context]

**Alternatives Considered:**
- Option A: [Pros/cons]
- Option B: [Pros/cons]

**Trade-offs:**
- [What we gain]
- [What we lose]
- [Why trade-off is acceptable]

**Limitations:**
- [Known issues]
- [Future work needed]

---

## Pending Decisions (To be made in future PRs)

### PR #2-3: Data Generation Strategy
- How to ensure diversity in synthetic users?
- What distributions for income, credit, savings?
- How to generate realistic transaction patterns?

### PR #5-8: Signal Detection Algorithms
- Rules-based vs. ML-based detection?
- Threshold values for each signal?
- How to handle edge cases?

### PR #10: Custom 5th Persona Design
- What gap in coverage exists?
- Financial Fragility vs other options?
- Criteria and prioritization?

### PR #17-18: UI Framework Choice
- Streamlit vs React for operator dashboard?
- How much polish is needed?
- Time vs quality trade-off?

### Extensions: Which to prioritize?
- Customer dashboard vs counterfactuals vs bias detection?
- Which adds most value to submission?

---

## Revision History

- 2025-11-05: Initial decision log created (PR #1)
- [Future dates]: [Updates]


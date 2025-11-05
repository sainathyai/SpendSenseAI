# Contributing to SpendSenseAI

Thank you for contributing to SpendSenseAI!

## Development Workflow

### Branch Naming Convention
- Feature branches: `pr-###-feature-name`
- Example: `pr-005-subscription-detection`
- Small related PRs can be combined in a single branch

### Before Starting
1. Ensure you're on the latest main branch
2. Create a new feature branch
3. Make your changes
4. Write tests for new functionality
5. Update documentation

### Pull Request Process

1. **Create Branch**
   - Branch from `main`
   - Use naming convention: `pr-###-feature-name`

2. **Development**
   - Write clean, documented code
   - Follow Python style guidelines (PEP 8)
   - Add docstrings to all functions/classes
   - Include type hints where appropriate

3. **Testing**
   - Write unit tests for new functionality
   - Ensure all existing tests pass
   - Aim for >80% code coverage
   - Test edge cases

4. **Documentation**
   - Update README if adding new features
   - Document design decisions in `docs/decision_log.md`
   - Update API documentation if applicable
   - Include inline comments for complex logic

5. **Commit**
   - Write clear, descriptive commit messages
   - Reference PR number in commits
   - Keep commits focused and atomic

6. **Review**
   - Self-review your changes
   - Check for hardcoded values
   - Verify deterministic behavior
   - Ensure privacy compliance

## Code Style

### Python
- Follow PEP 8 style guide
- Use Black for automatic formatting: `black .`
- Use isort for import sorting: `isort .`
- Run flake8 for linting: `flake8`
- Use type hints where applicable

### Commit Messages
Format: `[PR-###] Brief description`

Example:
```
[PR-005] Add subscription detection engine

- Implement recurring pattern detection
- Add cadence analysis (monthly/weekly)
- Include unit tests with known patterns
```

## Testing Requirements

### Unit Tests
- Test individual functions/classes
- Mock external dependencies
- Cover edge cases
- Located in `tests/unit/`

### Integration Tests
- Test end-to-end workflows
- Verify module interactions
- Located in `tests/integration/`

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_subscriptions.py
```

## Documentation Requirements

### Decision Log
Document all major decisions in `docs/decision_log.md`:
- Why this approach was chosen
- Alternatives considered
- Trade-offs made
- Limitations introduced

### Code Documentation
- All public functions need docstrings
- Include parameter descriptions
- Specify return types
- Note any side effects

Example:
```python
def detect_subscriptions(transactions: list, window_days: int = 30) -> dict:
    """
    Detect recurring subscription patterns in transaction data.
    
    Args:
        transactions: List of transaction dictionaries
        window_days: Time window for analysis in days (default: 30)
        
    Returns:
        Dictionary containing:
            - recurring_merchants: List of merchant names
            - monthly_spend: Total recurring spend per month
            - subscription_count: Number of detected subscriptions
            
    Raises:
        ValueError: If transactions list is empty
    """
    pass
```

## Success Criteria Checklist

Before submitting a PR, verify:

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Decision log updated for major choices
- [ ] No hardcoded values (use configs)
- [ ] Deterministic behavior (seeded randomness)
- [ ] Privacy considerations addressed
- [ ] Performance acceptable (<5s for recommendations)
- [ ] Error handling implemented
- [ ] Edge cases considered

## Privacy & Compliance

### Always Remember
- Use synthetic data only (no real PII)
- Include "not financial advice" disclaimers
- Enforce consent before recommendations
- Validate tone (no shaming language)
- Filter harmful/predatory products
- Log all operator actions

### Red Flags
- Real names, SSNs, or account numbers
- Judgmental language in recommendations
- Recommendations without consent
- Products user is ineligible for

## Getting Help

- Review project documentation in `docs/`
- Check the PRD: `Platinum Project_ Peak6_SpendSense.md`
- Refer to implementation plan: `PR_by_PR_Implementation_Plan.md`
- Contact: Bryce Harris - bharris@peak6.com

## Core Principles

Remember the guiding principles:
- **Transparency over sophistication**
- **User control over automation**
- **Education over sales**
- **Fairness built in from day one**

Build systems people can trust with their financial data.


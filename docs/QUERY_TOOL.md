# Natural Language Query Tool

## Overview

The Query Tool is a natural language interface for the SpendSenseAI operator dashboard that interprets text queries and returns database results without requiring SQL knowledge.

## Features

- **Pattern-based interpretation**: Uses regex patterns to understand queries
- **No LLM required**: Works entirely with pattern matching (can be upgraded to LLM later)
- **Context-aware**: Remembers customer context within a session
- **Multiple query types**: Supports balances, debt, transactions, subscriptions, and more
- **Chat-like interface**: Query history and formatted results
- **API endpoint**: `/operator/query` for programmatic access

## Architecture

### Components

1. **QueryInterpreter** (`recommend/query_interpreter.py`)
   - Pattern matching engine
   - Query type detection
   - Database query execution
   - Result formatting

2. **API Endpoint** (`ui/api.py`)
   - POST `/operator/query`
   - Accepts natural language queries
   - Returns structured JSON results

3. **UI Component** (`ui/query_tool.py`)
   - Streamlit chat interface
   - Query history management
   - Result visualization

## Supported Query Types

### Customer Information
- `list customers` - List all customers with summaries
- `customer CUST000001` - Get detailed customer info
- `show balances for CUST000001` - Get all account balances
- `net worth for CUST000001` - Calculate net worth

### Debt & Credit
- `debt info for CUST000001` - Get credit card liabilities
- `credit utilization for CUST000001` - Get credit utilization metrics
- `overdue for CUST000001` - Show overdue accounts

### Transactions
- `transactions for CUST000001` - Get recent transactions
- `last 10 transactions for CUST000001` - Get N most recent transactions
- `spending by category for CUST000001` - Category breakdown

### Feature Analysis
- `subscriptions for CUST000001` - Detect recurring subscriptions
- `savings for CUST000001` - Analyze savings patterns
- `income for CUST000001` - Assess income stability

### Accounts
- `accounts for CUST000001` - List all accounts
- `how many accounts for CUST000001` - Count accounts by type

## Usage

### API Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/operator/query",
    json={
        "query": "show balances for CUST000001",
        "customer_id": "CUST000001"  # Optional context
    }
)

result = response.json()
```

### Dashboard Usage

1. Navigate to the Query Tool section in the operator dashboard
2. Type a natural language query
3. Click "Execute"
4. View formatted results
5. Query history is maintained in the session

## Example Queries

```
# List all customers
"list customers"

# Get balances
"show balances for CUST000001"
"what is the balance for CUST000001"

# Debt information
"debt for CUST000001"
"show overdue accounts for CUST000001"
"credit card balance for CUST000001"

# Transactions
"transactions for CUST000001"
"last 30 days transactions for CUST000001"
"spending by category for CUST000001"

# Feature analysis
"subscriptions for CUST000001"
"credit utilization for CUST000001"
"savings for CUST000001"
"income for CUST000001"
```

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "query": "show balances for CUST000001",
  "result": {
    "type": "balances",
    "customer_id": "CUST000001",
    "accounts": [...],
    "total_assets": 7439.78,
    "total_debt": 1848.92,
    "net_worth": 5590.86
  },
  "timestamp": "2025-11-05T22:00:00.000000"
}
```

## Extensibility

### Adding New Query Types

1. Add a new pattern to `QueryInterpreter.patterns`
2. Implement a handler method (e.g., `_get_new_feature`)
3. Add result display logic to `ui/query_tool.py`

Example:

```python
# In QueryInterpreter
self.patterns.append(
    (r'payment\s+history\s+(?:for\s+)?(?:customer|user)?\s*(CUST\d+)', 
     self._get_payment_history)
)

def _get_payment_history(self, query: str, match, context: Optional[Dict] = None):
    customer_id = self._extract_customer_id(query, match, context)
    # Query database
    return {
        'type': 'payment_history',
        'customer_id': customer_id,
        # ... data
    }
```

### Upgrading to LLM

To upgrade from pattern matching to LLM-based interpretation:

1. Add LLM integration to `QueryInterpreter`
2. Use LLM to extract intent and entities
3. Map intent to existing handler functions
4. Keep patterns as fallback

## Performance

- **Pattern matching**: < 10ms per query
- **Database queries**: 10-100ms depending on complexity
- **API response**: < 500ms total
- **No external dependencies**: Works offline

## Security

- **Operator-only**: Query tool is restricted to operator dashboard
- **No SQL injection**: Uses parameterized queries
- **Rate limiting**: Can be added to API endpoint
- **Audit logging**: All queries are logged with timestamps

## Future Enhancements

1. **LLM Integration**: Use OpenAI/Anthropic for better NLU
2. **Query suggestions**: Auto-complete based on history
3. **Saved queries**: Bookmark frequent queries
4. **Export results**: CSV/PDF export of query results
5. **Multi-customer queries**: Aggregate queries across customers
6. **Time-based queries**: "show spending last month"
7. **Comparison queries**: "compare CUST000001 vs CUST000002"

## Testing

Run the query tool tests:

```bash
python -m pytest tests/test_query_tool.py -v
```

Test individual queries via API:

```bash
curl -X POST http://localhost:8000/operator/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show balances for CUST000001"}'
```

## Troubleshooting

### Query not recognized
- Check that customer ID format is correct (CUST######)
- Try rephrasing with supported keywords
- Check example queries for correct syntax

### No results returned
- Verify customer ID exists in database
- Check date ranges for transaction queries
- Ensure database connection is working

### Slow queries
- Check database indexes
- Limit transaction date ranges
- Use specific queries instead of "list all"

## Integration with Dashboard

To integrate the query tool into the operator dashboard:

```python
# In ui/dashboard.py
from ui.query_tool import render_query_tool

# Add to sidebar or main page
if selected_view == "Query Tool":
    render_query_tool(API_BASE_URL)
```


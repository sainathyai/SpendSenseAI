"""
AI-Powered SQL Query Generator for SpendSenseAI.

Uses LLM to generate SQL queries from natural language questions.
Includes safety checks and schema awareness.
"""

import sqlite3
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from recommend.llm_generator import LLMTextGenerator, LLMConfig

# Database schema information for LLM context
DATABASE_SCHEMA = """
Database Schema for SpendSenseAI:

Tables:
1. accounts
   - account_id (TEXT, PRIMARY KEY)
   - customer_id (TEXT, NOT NULL)
   - type (TEXT, NOT NULL) - 'depository', 'credit', 'loan', 'investment', 'other'
   - subtype (TEXT, NOT NULL) - 'checking', 'savings', 'credit card', etc.
   - balances_available (REAL)
   - balances_current (REAL, NOT NULL)
   - balances_limit (REAL)
   - iso_currency_code (TEXT, DEFAULT 'USD')
   - holder_category (TEXT, DEFAULT 'consumer')
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)

2. transactions
   - transaction_id (TEXT, PRIMARY KEY)
   - account_id (TEXT, NOT NULL, FOREIGN KEY -> accounts.account_id)
   - date (DATE, NOT NULL)
   - amount (REAL, NOT NULL) - positive for debits, negative for credits
   - merchant_name (TEXT)
   - merchant_entity_id (TEXT)
   - payment_channel (TEXT, DEFAULT 'online')
   - personal_finance_category_primary (TEXT)
   - personal_finance_category_detailed (TEXT)
   - pending (INTEGER, DEFAULT 0)
   - iso_currency_code (TEXT, DEFAULT 'USD')
   - created_at (TIMESTAMP)

3. credit_card_liabilities
   - account_id (TEXT, PRIMARY KEY, FOREIGN KEY -> accounts.account_id)
   - apr_type (TEXT, NOT NULL)
   - apr_percentage (REAL, NOT NULL)
   - minimum_payment_amount (REAL, NOT NULL)
   - last_payment_amount (REAL)
   - is_overdue (INTEGER, DEFAULT 0) - 1 if overdue, 0 otherwise
   - next_payment_due_date (DATE)
   - last_statement_balance (REAL)
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)

4. loan_liabilities
   - account_id (TEXT, PRIMARY KEY, FOREIGN KEY -> accounts.account_id)
   - interest_rate (REAL, NOT NULL)
   - next_payment_due_date (DATE)
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)

5. consent
   - consent_id (TEXT, PRIMARY KEY)
   - customer_id (TEXT, NOT NULL)
   - scope (TEXT, NOT NULL)
   - status (TEXT, NOT NULL) - 'active', 'revoked', 'expired'
   - granted_at (TIMESTAMP)
   - expires_at (TIMESTAMP)

Important Notes:
- Use JOINs to connect accounts with transactions: accounts.account_id = transactions.account_id
- Use JOINs to connect accounts with liabilities: accounts.account_id = credit_card_liabilities.account_id
- Customer IDs are in format: CUST000001, CUST000002, etc.
- Amounts: positive for debits (charges), negative for credits (payments/refunds)
- Dates are stored as DATE strings in format: YYYY-MM-DD
- Always use parameterized queries with ? placeholders for user input
- Never use string concatenation for SQL queries
- Credit cards: accounts with type = 'credit' and subtype = 'credit card'
- To count customers with multiple credit cards: SELECT customer_id, COUNT(*) as count FROM accounts WHERE type = 'credit' GROUP BY customer_id HAVING COUNT(*) > 1
"""


class SQLQueryGenerator:
    """Generates SQL queries from natural language using LLM."""
    
    def __init__(self, db_path: str, llm_config: Optional[LLMConfig] = None):
        """
        Initialize SQL query generator.
        
        Args:
            db_path: Path to SQLite database
            llm_config: Optional LLM configuration
        """
        self.db_path = db_path
        self.llm_generator = LLMTextGenerator(llm_config) if llm_config else LLMTextGenerator()
        self.schema = DATABASE_SCHEMA
    
    def generate_sql(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language.
        
        Args:
            natural_language_query: Natural language question
            
        Returns:
            Dictionary with SQL query and metadata
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt()
            
            # Build user prompt
            user_prompt = self._build_user_prompt(natural_language_query)
            
            # Generate SQL using LLM
            if not self.llm_generator.config.enable_llm:
                return {
                    'success': False,
                    'error': 'LLM is not enabled. Please enable OpenAI API key.',
                    'sql': None
                }
            
            # Use LLM to generate SQL
            if not self.llm_generator.client:
                return {
                    'success': False,
                    'error': 'OpenAI client not initialized. Please check your API key.',
                    'sql': None
                }
            
            sql_response = self.llm_generator.client.chat.completions.create(
                model=self.llm_generator.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,  # SQL queries can be longer
                temperature=0.1,  # Low temperature for precise SQL
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            # Parse response
            response_text = sql_response.choices[0].message.content.strip()
            response_data = json.loads(response_text)
            
            sql_query = response_data.get('sql', '').strip()
            explanation = response_data.get('explanation', '')
            
            if not sql_query:
                return {
                    'success': False,
                    'error': 'LLM did not generate a SQL query',
                    'sql': None
                }
            
            # Validate and sanitize SQL
            validation_result = self._validate_sql(sql_query)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'sql': sql_query,
                    'explanation': explanation
                }
            
            return {
                'success': True,
                'sql': sql_query,
                'explanation': explanation,
                'validated': True
            }
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            return {
                'success': False,
                'error': f'Failed to parse LLM response: {str(e)}',
                'sql': None
            }
        except Exception as e:
            logging.error(f"Error generating SQL query: {e}")
            return {
                'success': False,
                'error': f'Error generating SQL: {str(e)}',
                'sql': None
            }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for SQL generation."""
        return f"""You are a SQL query generator for a financial data database. Your task is to convert natural language questions into safe, valid SQLite SQL queries.

{DATABASE_SCHEMA}

Rules:
1. Generate ONLY valid SQLite SQL queries
2. Use parameterized queries with ? placeholders for any user-provided values
3. Never use string concatenation or direct value insertion
4. Always use proper JOINs when accessing related tables
5. Return results in JSON format: {{"sql": "SELECT ...", "explanation": "brief explanation"}}
6. Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
7. Use proper column names from the schema
8. Handle NULL values appropriately
9. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
10. Format dates properly (they are stored as DATE strings)

Example:
User: "How many customers have overdue credit card balances?"
Response: {{"sql": "SELECT COUNT(DISTINCT a.customer_id) as count FROM accounts a JOIN credit_card_liabilities l ON a.account_id = l.account_id WHERE a.type = 'credit' AND l.is_overdue = 1", "explanation": "Counts distinct customers with overdue credit cards"}}

Important: Always return valid JSON with 'sql' and 'explanation' fields."""
    
    def _build_user_prompt(self, query: str) -> str:
        """Build user prompt for SQL generation."""
        return f"""Convert this natural language question into a SQLite SQL query:

"{query}"

Return the response as JSON with:
- "sql": The SQL query (use ? for parameters)
- "explanation": A brief explanation of what the query does

Remember:
- Only SELECT queries
- Use parameterized queries (? placeholders)
- Use proper JOINs
- Follow the database schema exactly"""
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query for safety and correctness.
        
        Args:
            sql: SQL query string
            
        Returns:
            Dictionary with validation result
        """
        sql_upper = sql.upper().strip()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'EXEC', 'EXECUTE', '--', ';', '/*', '*/'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    'valid': False,
                    'error': f'Dangerous SQL keyword detected: {keyword}'
                }
        
        # Check that it's a SELECT query
        if not sql_upper.startswith('SELECT'):
            return {
                'valid': False,
                'error': 'Only SELECT queries are allowed'
            }
        
        # Try to parse the SQL (basic validation)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Use EXPLAIN to validate without executing
            cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
            cursor.fetchall()
            conn.close()
        except sqlite3.Error as e:
            return {
                'valid': False,
                'error': f'Invalid SQL syntax: {str(e)}'
            }
        
        return {'valid': True}
    
    def execute_generated_query(
        self,
        natural_language_query: str,
        parameters: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate and execute SQL query from natural language.
        
        Args:
            natural_language_query: Natural language question
            parameters: Optional parameters for the query
            
        Returns:
            Dictionary with query results
        """
        # Generate SQL
        generation_result = self.generate_sql(natural_language_query)
        
        if not generation_result['success']:
            return {
                'success': False,
                'error': generation_result.get('error', 'Failed to generate SQL'),
                'query': natural_language_query,
                'sql': generation_result.get('sql'),
                'timestamp': datetime.now().isoformat()
            }
        
        sql_query = generation_result['sql']
        
        # Execute query
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if parameters:
                cursor.execute(sql_query, parameters)
            else:
                cursor.execute(sql_query)
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(row))
            
            conn.close()
            
            return {
                'success': True,
                'query': natural_language_query,
                'sql': sql_query,
                'explanation': generation_result.get('explanation', ''),
                'result': {
                    'type': 'sql_result',
                    'count': len(results),
                    'data': results,
                    'sql_query': sql_query  # Include SQL in result for debugging
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except sqlite3.Error as e:
            logging.error(f"SQL execution error: {e}")
            return {
                'success': False,
                'error': f'SQL execution error: {str(e)}',
                'query': natural_language_query,
                'sql': sql_query,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Unexpected error executing query: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'query': natural_language_query,
                'sql': sql_query,
                'timestamp': datetime.now().isoformat()
            }


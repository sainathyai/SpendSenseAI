"""
Natural Language Query Interpreter for SpendSenseAI
Interprets natural language queries and executes database operations
"""

import sqlite3
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from features.subscription_detection import detect_subscriptions_for_customer

# Try to import SQL query generator (optional, requires LLM)
try:
    from recommend.sql_query_generator import SQLQueryGenerator
    SQL_GENERATOR_AVAILABLE = True
except ImportError:
    SQL_GENERATOR_AVAILABLE = False


class QueryInterpreter:
    """Interprets natural language queries into database operations"""
    
    def __init__(self, db_path: str, enable_ai_queries: bool = True):
        """
        Initialize query interpreter.
        
        Args:
            db_path: Path to SQLite database
            enable_ai_queries: Enable AI-powered SQL generation (requires LLM)
        """
        self.db_path = db_path
        self.enable_ai_queries = enable_ai_queries and SQL_GENERATOR_AVAILABLE
        self.sql_generator = None
        
        if self.enable_ai_queries:
            try:
                self.sql_generator = SQLQueryGenerator(db_path)
                logging.info("AI-powered SQL query generation enabled")
            except Exception as e:
                logging.warning(f"Failed to initialize SQL generator: {e}. Falling back to pattern matching.")
                self.enable_ai_queries = False
    
    def interpret(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Interpret a natural language query and execute it
        
        Args:
            query: Natural language query string
            context: Optional context (e.g., customer_id)
            
        Returns:
            Dictionary with query results
        """
        query_lower = query.lower().strip()
        
        try:
            # Extract customer ID if present
            customer_id = self._extract_customer_id(query) or (context.get('customer_id') if context else None)
            
            # List customers
            if 'list customers' in query_lower or 'show customers' in query_lower or 'all customers' in query_lower:
                return self._list_customers()
            
            # Customer info
            if ('customer' in query_lower or 'user' in query_lower) and customer_id:
                if 'outstanding' in query_lower or ('balance' in query_lower and 'outstanding' in query_lower):
                    return self._get_debt_info(customer_id)
                elif 'balance' in query_lower:
                    return self._get_balances(customer_id)
                elif 'debt' in query_lower:
                    return self._get_debt_info(customer_id)
                elif 'subscription' in query_lower:
                    return self._get_subscriptions(customer_id)
                elif 'transaction' in query_lower:
                    return self._get_transactions(customer_id)
                else:
                    return self._get_customer_info(customer_id)
            
            # Balance queries (including "outstanding balance")
            if ('balance' in query_lower or 'outstanding' in query_lower) and customer_id:
                # If "outstanding" is mentioned, return debt info (credit card balances)
                if 'outstanding' in query_lower:
                    return self._get_debt_info(customer_id)
                return self._get_balances(customer_id)
            
            # Debt queries
            if 'debt' in query_lower and customer_id:
                return self._get_debt_info(customer_id)
            
            # Subscription queries
            if 'subscription' in query_lower and customer_id:
                return self._get_subscriptions(customer_id)
            
            # Transaction queries
            if 'transaction' in query_lower and customer_id:
                return self._get_transactions(customer_id)
            
            # Net worth
            if 'net worth' in query_lower and customer_id:
                return self._get_balances(customer_id)
            
            # Overdue queries
            if ('overdue' in query_lower or 'cc balance overdue' in query_lower or 'credit card overdue' in query_lower):
                if customer_id:
                    return self._get_overdue_info(customer_id)
                else:
                    # Count or list customers with overdue balances
                    if 'how many' in query_lower or 'count' in query_lower or 'number' in query_lower:
                        return self._count_overdue_customers()
                    else:
                        return self._list_overdue_customers()
            
            # If pattern matching fails and AI queries are enabled, try AI generation
            if self.enable_ai_queries and self.sql_generator:
                try:
                    ai_result = self.sql_generator.execute_generated_query(query)
                    if ai_result.get('success'):
                        return ai_result
                    # If AI fails, include the error in the response
                    ai_error = ai_result.get('error', 'Unknown error')
                    logging.warning(f"AI query generation failed: {ai_error}")
                    return {
                        'success': False,
                        'query': query,
                        'error': f'Could not understand query. LLM attempt failed: {ai_error}. Try: "list customers", "show balances for CUST000001", "debt info for CUST000001", "how many customers have cc balances overdue", or ask any question about the database.',
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    logging.warning(f"AI query generation exception: {e}. Falling back to error message.")
                    return {
                        'success': False,
                        'query': query,
                        'error': f'Could not understand query. LLM attempt raised exception: {str(e)}. Try: "list customers", "show balances for CUST000001", "debt info for CUST000001", "how many customers have cc balances overdue", or ask any question about the database.',
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'success': False,
                'query': query,
                'error': 'Could not understand query. Try: "list customers", "show balances for CUST000001", "debt info for CUST000001", "how many customers have cc balances overdue", or ask any question about the database.',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_customer_id(self, query: str) -> Optional[str]:
        """Extract customer ID from query"""
        # Match CUST followed by digits (e.g., CUST000001)
        match = re.search(r'CUST\d+', query, re.IGNORECASE)
        if match:
            return match.group(0).upper()
        
        # Match variations like "customer1", "customer 1", "cust1", "user1", etc.
        # Extract the number and format as CUST000001
        patterns = [
            r'customer\s*(\d+)',
            r'cust\s*(\d+)',
            r'user\s*(\d+)',
            r'c\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                num = match.group(1)
                # Format as CUST000001 (pad with zeros)
                return f"CUST{num.zfill(6)}"
        
        return None
    
    def _list_customers(self) -> Dict[str, Any]:
        """List all customers"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT customer_id
            FROM accounts
            ORDER BY customer_id
            LIMIT 50
        """)
        
        customers = [row['customer_id'] for row in cursor.fetchall()]
        conn.close()
        
        return {
            'success': True,
            'query': 'list customers',
            'result': {
                'type': 'customer_list',
                'count': len(customers),
                'customers': customers
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_customer_info(self, customer_id: str) -> Dict[str, Any]:
        """Get customer information"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get account count
        cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE customer_id = ?", (customer_id,))
        account_count = cursor.fetchone()['count']
        
        # Get transaction count
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE customer_id = ?", (customer_id,))
        transaction_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'success': True,
            'query': f'customer info for {customer_id}',
            'result': {
                'type': 'customer_info',
                'customer_id': customer_id,
                'account_count': account_count,
                'transaction_count': transaction_count
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_balances(self, customer_id: str) -> Dict[str, Any]:
        """Get balance information for a customer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get assets (depository accounts)
        cursor.execute("""
            SELECT COALESCE(SUM(balances_current), 0) as total
            FROM accounts
            WHERE customer_id = ? AND type = 'depository'
        """, (customer_id,))
        total_assets = cursor.fetchone()['total']
        
        # Get debts (credit accounts)
        cursor.execute("""
            SELECT COALESCE(SUM(balances_current), 0) as total
            FROM accounts
            WHERE customer_id = ? AND type = 'credit'
        """, (customer_id,))
        total_debts = cursor.fetchone()['total']
        
        net_worth = total_assets - total_debts
        
        conn.close()
        
        return {
            'success': True,
            'query': f'balances for {customer_id}',
            'result': {
                'type': 'balances',
                'customer_id': customer_id,
                'total_assets': round(total_assets, 2),
                'total_debts': round(total_debts, 2),
                'net_worth': round(net_worth, 2)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_debt_info(self, customer_id: str) -> Dict[str, Any]:
        """Get debt information for a customer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                account_id,
                type,
                subtype,
                balances_current,
                balances_limit
            FROM accounts
            WHERE customer_id = ? AND type = 'credit'
        """, (customer_id,))
        
        debts = []
        total_debt = 0
        total_limit = 0
        
        for row in cursor.fetchall():
            debt_amount = row['balances_current'] or 0
            limit = row['balances_limit'] or 0
            # Construct name from type and subtype
            account_name = f"{row['type'].title()} - {row['subtype'].title()}"
            debts.append({
                'account_id': row['account_id'],
                'name': account_name,
                'type': row['type'],
                'subtype': row['subtype'],
                'balance': round(debt_amount, 2),
                'limit': round(limit, 2),
                'utilization': round((debt_amount / limit * 100) if limit > 0 else 0, 2)
            })
            total_debt += debt_amount
            total_limit += limit
        
        conn.close()
        
        return {
            'success': True,
            'query': f'debt info for {customer_id}',
            'result': {
                'type': 'debt_info',
                'customer_id': customer_id,
                'total_debt': round(total_debt, 2),
                'total_limit': round(total_limit, 2),
                'overall_utilization': round((total_debt / total_limit * 100) if total_limit > 0 else 0, 2),
                'accounts': debts
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_subscriptions(self, customer_id: str) -> Dict[str, Any]:
        """Get subscription information"""
        try:
            # Detect subscriptions
            subscriptions, metrics = detect_subscriptions_for_customer(
                customer_id,
                self.db_path,
                window_days=90
            )
            
            # Format subscriptions for response
            subscription_list = []
            for sub in subscriptions:
                subscription_list.append({
                    'merchant_name': sub.merchant_name,
                    'cadence': sub.cadence,
                    'monthly_recurring_spend': round(sub.monthly_recurring_spend, 2),
                    'average_amount': round(sub.average_amount, 2),
                    'transaction_count': sub.transaction_count,
                    'first_transaction_date': sub.first_transaction_date.isoformat() if hasattr(sub.first_transaction_date, 'isoformat') else str(sub.first_transaction_date),
                    'last_transaction_date': sub.last_transaction_date.isoformat() if hasattr(sub.last_transaction_date, 'isoformat') else str(sub.last_transaction_date),
                    'is_active': sub.is_active,
                    'confidence_score': round(sub.confidence_score, 2)
                })
            
            return {
                'success': True,
                'query': f'subscriptions for {customer_id}',
                'result': {
                    'type': 'subscriptions',
                    'customer_id': customer_id,
                    'subscription_count': len(subscriptions),
                    'active_subscription_count': metrics.get('active_subscription_count', 0),
                    'total_monthly_recurring_spend': round(metrics.get('total_monthly_recurring_spend', 0.0), 2),
                    'active_monthly_recurring_spend': round(metrics.get('active_monthly_recurring_spend', 0.0), 2),
                    'subscription_share_of_total': round(metrics.get('subscription_share_of_total', 0.0), 2),
                    'subscriptions': subscription_list
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'query': f'subscriptions for {customer_id}',
                'error': f'Error detecting subscriptions: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_transactions(self, customer_id: str) -> Dict[str, Any]:
        """Get recent transactions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                t.transaction_id,
                t.date,
                t.merchant_name,
                t.amount,
                t.personal_finance_category_primary,
                t.personal_finance_category_detailed
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = ?
            ORDER BY t.date DESC
            LIMIT 10
        """, (customer_id,))
        
        transactions = []
        for row in cursor.fetchall():
            # Use merchant_name as name, fallback to transaction_id if not available
            name = row['merchant_name'] or row['transaction_id']
            # Use primary category as category, fallback to detailed if not available
            category = row['personal_finance_category_primary'] or row['personal_finance_category_detailed'] or 'OTHER'
            transactions.append({
                'transaction_id': row['transaction_id'],
                'date': row['date'],
                'name': name,
                'amount': round(row['amount'], 2),
                'category': category
            })
        
        conn.close()
        
        return {
            'success': True,
            'query': f'transactions for {customer_id}',
            'result': {
                'type': 'transactions',
                'customer_id': customer_id,
                'count': len(transactions),
                'transactions': transactions
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_overdue_info(self, customer_id: str) -> Dict[str, Any]:
        """Get overdue credit card information for a customer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                a.account_id,
                a.type,
                a.subtype,
                a.balances_current,
                a.balances_limit,
                l.is_overdue,
                l.minimum_payment_amount,
                l.next_payment_due_date
            FROM accounts a
            JOIN credit_card_liabilities l ON a.account_id = l.account_id
            WHERE a.customer_id = ? AND a.type = 'credit' AND l.is_overdue = 1
        """, (customer_id,))
        
        overdue_accounts = []
        for row in cursor.fetchall():
            overdue_accounts.append({
                'account_id': row['account_id'],
                'name': f"{row['type'].title()} - {row['subtype'].title()}",
                'balance': round(row['balances_current'] or 0, 2),
                'limit': round(row['balances_limit'] or 0, 2),
                'minimum_payment': round(row['minimum_payment_amount'] or 0, 2),
                'next_payment_due_date': row['next_payment_due_date']
            })
        
        conn.close()
        
        return {
            'success': True,
            'query': f'overdue info for {customer_id}',
            'result': {
                'type': 'overdue_info',
                'customer_id': customer_id,
                'overdue_count': len(overdue_accounts),
                'accounts': overdue_accounts
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _count_overdue_customers(self) -> Dict[str, Any]:
        """Count customers with overdue credit card balances"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT a.customer_id) as count
            FROM accounts a
            JOIN credit_card_liabilities l ON a.account_id = l.account_id
            WHERE a.type = 'credit' AND l.is_overdue = 1
        """)
        
        result = cursor.fetchone()
        count = result['count'] if result else 0
        
        conn.close()
        
        return {
            'success': True,
            'query': 'how many customers have cc balances overdue',
            'result': {
                'type': 'overdue_count',
                'count': count,
                'message': f'{count} customer(s) have overdue credit card balances'
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _list_overdue_customers(self) -> Dict[str, Any]:
        """List customers with overdue credit card balances"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                a.customer_id,
                COUNT(DISTINCT a.account_id) as overdue_account_count,
                SUM(a.balances_current) as total_overdue_balance
            FROM accounts a
            JOIN credit_card_liabilities l ON a.account_id = l.account_id
            WHERE a.type = 'credit' AND l.is_overdue = 1
            GROUP BY a.customer_id
            ORDER BY total_overdue_balance DESC
        """)
        
        customers = []
        for row in cursor.fetchall():
            customers.append({
                'customer_id': row['customer_id'],
                'overdue_account_count': row['overdue_account_count'],
                'total_overdue_balance': round(row['total_overdue_balance'] or 0, 2)
            })
        
        conn.close()
        
        return {
            'success': True,
            'query': 'list customers with overdue credit card balances',
            'result': {
                'type': 'overdue_customers',
                'count': len(customers),
                'customers': customers
            },
            'timestamp': datetime.now().isoformat()
        }

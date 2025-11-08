"""
Unit tests for database module.
"""

import pytest
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path

from ingest.database import (
    create_database, load_accounts, load_transactions,
    load_credit_card_liabilities, check_data_integrity
)
from ingest.queries import (
    get_accounts_by_customer, get_transactions_by_account,
    get_transactions_by_customer, get_credit_card_liabilities_by_customer,
    check_data_integrity as check_integrity
)
from ingest.schemas import (
    Account, Transaction, CreditCardLiability,
    AccountType, AccountSubtype, HolderCategory,
    PaymentChannel, PersonalFinanceCategory,
    PersonalFinanceCategoryPrimary, PersonalFinanceCategoryDetailed,
    AccountBalances, CreditCardAPR
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    create_database(db_path)
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_accounts():
    """Create sample accounts for testing."""
    return [
        Account(
            account_id="ACC-001",
            customer_id="CUST-001",
            type=AccountType.DEPOSITORY,
            subtype=AccountSubtype.CHECKING,
            balances=AccountBalances(available=1000.0, current=1000.0, limit=None),
            iso_currency_code="USD",
            holder_category=HolderCategory.CONSUMER
        ),
        Account(
            account_id="ACC-002",
            customer_id="CUST-001",
            type=AccountType.CREDIT,
            subtype=AccountSubtype.CREDIT_CARD,
            balances=AccountBalances(available=None, current=500.0, limit=5000.0),
            iso_currency_code="USD",
            holder_category=HolderCategory.CONSUMER
        ),
        Account(
            account_id="ACC-003",
            customer_id="CUST-002",
            type=AccountType.DEPOSITORY,
            subtype=AccountSubtype.CHECKING,
            balances=AccountBalances(available=2000.0, current=2000.0, limit=None),
            iso_currency_code="USD",
            holder_category=HolderCategory.CONSUMER
        ),
    ]


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing."""
    category = PersonalFinanceCategory(
        primary=PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        detailed=PersonalFinanceCategoryDetailed.GENERAL_MERCHANDISE
    )
    
    return [
        Transaction(
            transaction_id="TXN-001",
            account_id="ACC-001",
            date=date.today() - timedelta(days=10),
            amount=-50.0,
            merchant_name="Test Merchant",
            merchant_entity_id="MERCH-001",
            payment_channel=PaymentChannel.ONLINE,
            personal_finance_category=category,
            pending=False,
            iso_currency_code="USD"
        ),
        Transaction(
            transaction_id="TXN-002",
            account_id="ACC-002",
            date=date.today() - timedelta(days=5),
            amount=-100.0,
            merchant_name="Test Merchant 2",
            merchant_entity_id="MERCH-002",
            payment_channel=PaymentChannel.ONLINE,
            personal_finance_category=category,
            pending=False,
            iso_currency_code="USD"
        ),
        Transaction(
            transaction_id="TXN-003",
            account_id="ACC-001",
            date=date.today() - timedelta(days=1),
            amount=-25.0,
            merchant_name="Test Merchant 3",
            merchant_entity_id="MERCH-003",
            payment_channel=PaymentChannel.ONLINE,
            personal_finance_category=category,
            pending=True,
            iso_currency_code="USD"
        ),
    ]


@pytest.fixture
def sample_liabilities():
    """Create sample liabilities for testing."""
    return [
        CreditCardLiability(
            account_id="ACC-002",
            aprs=[CreditCardAPR(type="purchase", percentage=18.99)],
            minimum_payment_amount=25.0,
            last_payment_amount=50.0,
            is_overdue=False,
            next_payment_due_date=date.today() + timedelta(days=15),
            last_statement_balance=500.0
        ),
    ]


class TestDatabaseSetup:
    """Test database setup functionality."""
    
    def test_create_database(self, temp_db):
        """Test database creation."""
        assert os.path.exists(temp_db)
        
        # Verify tables exist
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('accounts', 'transactions', 'credit_card_liabilities')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'accounts' in tables
        assert 'transactions' in tables
        assert 'credit_card_liabilities' in tables
        
        conn.close()


class TestDataLoading:
    """Test data loading functionality."""
    
    def test_load_accounts(self, temp_db, sample_accounts):
        """Test loading accounts."""
        count = load_accounts(sample_accounts, temp_db)
        assert count == 3
        
        # Verify accounts were loaded
        accounts = get_accounts_by_customer("CUST-001", temp_db)
        assert len(accounts) == 2
        assert accounts[0].account_id == "ACC-001"
        assert accounts[1].account_id == "ACC-002"
    
    def test_load_transactions(self, temp_db, sample_accounts, sample_transactions):
        """Test loading transactions."""
        # Load accounts first (required for foreign key)
        load_accounts(sample_accounts, temp_db)
        
        count = load_transactions(sample_transactions, temp_db)
        assert count == 3
        
        # Verify transactions were loaded
        transactions = get_transactions_by_account("ACC-001", temp_db)
        assert len(transactions) == 2  # TXN-001 and TXN-003
        assert transactions[0].transaction_id == "TXN-003"  # Most recent first
    
    def test_load_liabilities(self, temp_db, sample_accounts, sample_liabilities):
        """Test loading liabilities."""
        # Load accounts first (required for foreign key)
        load_accounts(sample_accounts, temp_db)
        
        count = load_credit_card_liabilities(sample_liabilities, temp_db)
        assert count == 1
        
        # Verify liabilities were loaded
        liabilities = get_credit_card_liabilities_by_customer("CUST-001", temp_db)
        assert len(liabilities) == 1
        assert liabilities[0].account_id == "ACC-002"
        assert liabilities[0].aprs[0].percentage == 18.99


class TestQueries:
    """Test query functionality."""
    
    def test_get_accounts_by_customer(self, temp_db, sample_accounts):
        """Test getting accounts by customer."""
        load_accounts(sample_accounts, temp_db)
        
        accounts = get_accounts_by_customer("CUST-001", temp_db)
        assert len(accounts) == 2
        
        accounts = get_accounts_by_customer("CUST-002", temp_db)
        assert len(accounts) == 1
    
    def test_get_transactions_by_account(self, temp_db, sample_accounts, sample_transactions):
        """Test getting transactions by account."""
        load_accounts(sample_accounts, temp_db)
        load_transactions(sample_transactions, temp_db)
        
        transactions = get_transactions_by_account("ACC-001", temp_db)
        assert len(transactions) == 2
        
        # Test date filtering
        start_date = date.today() - timedelta(days=7)
        transactions = get_transactions_by_account("ACC-001", temp_db, start_date=start_date)
        assert len(transactions) == 1  # Only TXN-003
    
    def test_get_transactions_exclude_pending(self, temp_db, sample_accounts, sample_transactions):
        """Test excluding pending transactions."""
        load_accounts(sample_accounts, temp_db)
        load_transactions(sample_transactions, temp_db)
        
        transactions = get_transactions_by_account("ACC-001", temp_db, exclude_pending=True)
        assert len(transactions) == 1  # Only TXN-001 (TXN-003 is pending)
    
    def test_get_transactions_by_customer(self, temp_db, sample_accounts, sample_transactions):
        """Test getting transactions by customer."""
        load_accounts(sample_accounts, temp_db)
        load_transactions(sample_transactions, temp_db)
        
        transactions = get_transactions_by_customer("CUST-001", temp_db)
        assert len(transactions) == 3  # All transactions for both accounts


class TestDataIntegrity:
    """Test data integrity checks."""
    
    def test_data_integrity_pass(self, temp_db, sample_accounts, sample_transactions, sample_liabilities):
        """Test data integrity with valid data."""
        load_accounts(sample_accounts, temp_db)
        load_transactions(sample_transactions, temp_db)
        load_credit_card_liabilities(sample_liabilities, temp_db)
        
        integrity = check_integrity(temp_db)
        
        assert integrity['total_accounts'] == 3
        assert integrity['total_transactions'] == 3
        assert integrity['total_liabilities'] == 1
        assert integrity['orphaned_transactions'] == 0
        assert integrity['orphaned_liabilities'] == 0
        assert integrity['integrity_passed'] == True


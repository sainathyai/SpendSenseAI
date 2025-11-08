"""
Unit tests for subscription detection engine.
"""

import pytest
from datetime import date, timedelta
from ingest.schemas import (
    Transaction, PaymentChannel, PersonalFinanceCategory,
    PersonalFinanceCategoryPrimary, PersonalFinanceCategoryDetailed
)
from features.subscription_detection import (
    detect_subscriptions,
    group_transactions_by_merchant,
    calculate_date_intervals,
    detect_cadence,
    calculate_monthly_recurring_spend,
    is_active_subscription,
    calculate_subscription_metrics
)


@pytest.fixture
def monthly_subscription_transactions():
    """Create monthly subscription transactions (Netflix-like)."""
    category = PersonalFinanceCategory(
        primary=PersonalFinanceCategoryPrimary.ENTERTAINMENT,
        detailed=PersonalFinanceCategoryDetailed.ENTERTAINMENT
    )
    
    base_date = date(2024, 1, 1)
    transactions = []
    
    # Create 6 monthly transactions (every 30 days)
    for i in range(6):
        transaction = Transaction(
            transaction_id=f"TXN-MONTHLY-{i}",
            account_id="ACC-001",
            date=base_date + timedelta(days=i * 30),
            amount=-15.99,  # Negative for charge
            merchant_name="Netflix",
            merchant_entity_id="MERCH-NETFLIX",
            payment_channel=PaymentChannel.ONLINE,
            personal_finance_category=category,
            pending=False,
            iso_currency_code="USD"
        )
        transactions.append(transaction)
    
    return transactions


@pytest.fixture
def weekly_subscription_transactions():
    """Create weekly subscription transactions."""
    category = PersonalFinanceCategory(
        primary=PersonalFinanceCategoryPrimary.ENTERTAINMENT,
        detailed=PersonalFinanceCategoryDetailed.ENTERTAINMENT
    )
    
    base_date = date(2024, 1, 1)
    transactions = []
    
    # Create 8 weekly transactions (every 7 days)
    for i in range(8):
        transaction = Transaction(
            transaction_id=f"TXN-WEEKLY-{i}",
            account_id="ACC-001",
            date=base_date + timedelta(days=i * 7),
            amount=-9.99,
            merchant_name="Weekly Service",
            merchant_entity_id="MERCH-WEEKLY",
            payment_channel=PaymentChannel.ONLINE,
            personal_finance_category=category,
            pending=False,
            iso_currency_code="USD"
        )
        transactions.append(transaction)
    
    return transactions


@pytest.fixture
def mixed_transactions():
    """Create mixed transactions (some subscriptions, some one-time)."""
    category = PersonalFinanceCategory(
        primary=PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        detailed=PersonalFinanceCategoryDetailed.GENERAL_MERCHANDISE
    )
    
    base_date = date(2024, 1, 1)
    transactions = []
    
    # Add 3 monthly subscription transactions
    for i in range(3):
        transactions.append(Transaction(
            transaction_id=f"TXN-SUB-{i}",
            account_id="ACC-001",
            date=base_date + timedelta(days=i * 30),
            amount=-20.00,
            merchant_name="Subscription Service",
            merchant_entity_id="MERCH-SUB",
            payment_channel=PaymentChannel.ONLINE,
            personal_finance_category=category,
            pending=False,
            iso_currency_code="USD"
        ))
    
    # Add one-time purchases
    transactions.append(Transaction(
        transaction_id="TXN-ONETIME-1",
        account_id="ACC-001",
        date=base_date + timedelta(days=10),
        amount=-50.00,
        merchant_name="One Time Purchase",
        merchant_entity_id="MERCH-ONETIME",
        payment_channel=PaymentChannel.ONLINE,
        personal_finance_category=category,
        pending=False,
        iso_currency_code="USD"
    ))
    
    return transactions


class TestGrouping:
    """Test transaction grouping."""
    
    def test_group_by_merchant(self, monthly_subscription_transactions):
        """Test grouping transactions by merchant."""
        groups = group_transactions_by_merchant(monthly_subscription_transactions)
        
        assert "Netflix" in groups
        assert len(groups["Netflix"]) == 6


class TestDateIntervals:
    """Test date interval calculation."""
    
    def test_calculate_intervals(self, monthly_subscription_transactions):
        """Test calculating date intervals."""
        intervals = calculate_date_intervals(monthly_subscription_transactions)
        
        assert len(intervals) == 5  # 6 transactions = 5 intervals
        assert all(28 <= interval <= 32 for interval in intervals)  # Monthly cadence
    
    def test_intervals_single_transaction(self):
        """Test intervals with single transaction."""
        transaction = Transaction(
            transaction_id="TXN-1",
            account_id="ACC-1",
            date=date(2024, 1, 1),
            amount=-10.0,
            merchant_name="Test",
            payment_channel=PaymentChannel.ONLINE,
            pending=False,
            iso_currency_code="USD"
        )
        
        intervals = calculate_date_intervals([transaction])
        assert intervals == []


class TestCadenceDetection:
    """Test cadence detection."""
    
    def test_detect_monthly_cadence(self, monthly_subscription_transactions):
        """Test detecting monthly cadence."""
        intervals = calculate_date_intervals(monthly_subscription_transactions)
        cadence, confidence = detect_cadence(intervals, len(monthly_subscription_transactions))
        
        assert cadence == 'monthly'
        assert confidence > 0.5
    
    def test_detect_weekly_cadence(self, weekly_subscription_transactions):
        """Test detecting weekly cadence."""
        intervals = calculate_date_intervals(weekly_subscription_transactions)
        cadence, confidence = detect_cadence(intervals, len(weekly_subscription_transactions))
        
        assert cadence == 'weekly'
        assert confidence > 0.5
    
    def test_detect_irregular_cadence(self):
        """Test detecting irregular cadence."""
        # Create irregular transactions
        transactions = [
            Transaction(
                transaction_id=f"TXN-{i}",
                account_id="ACC-1",
                date=date(2024, 1, 1) + timedelta(days=i * 10 + i * 5),  # Irregular spacing
                amount=-10.0,
                merchant_name="Irregular",
                payment_channel=PaymentChannel.ONLINE,
                pending=False,
                iso_currency_code="USD"
            ) for i in range(4)
        ]
        
        intervals = calculate_date_intervals(transactions)
        cadence, confidence = detect_cadence(intervals, len(transactions))
        
        assert cadence == 'irregular'
        assert confidence < 0.5


class TestMonthlyRecurringSpend:
    """Test monthly recurring spend calculation."""
    
    def test_monthly_spend(self):
        """Test monthly subscription spend."""
        monthly_spend = calculate_monthly_recurring_spend('monthly', 15.99, 6)
        assert monthly_spend == 15.99
    
    def test_weekly_spend(self):
        """Test weekly subscription spend."""
        weekly_spend = calculate_monthly_recurring_spend('weekly', 9.99, 8)
        assert abs(weekly_spend - (9.99 * 4.33)) < 0.01
    
    def test_biweekly_spend(self):
        """Test biweekly subscription spend."""
        biweekly_spend = calculate_monthly_recurring_spend('biweekly', 20.00, 4)
        assert biweekly_spend == 40.00  # 2 per month


class TestActiveSubscription:
    """Test active subscription detection."""
    
    def test_active_monthly_subscription(self):
        """Test active monthly subscription."""
        last_date = date.today() - timedelta(days=15)  # Within 60 days
        is_active = is_active_subscription(last_date, 'monthly', date.today())
        assert is_active is True
    
    def test_inactive_monthly_subscription(self):
        """Test inactive monthly subscription."""
        last_date = date.today() - timedelta(days=90)  # Beyond 60 days
        is_active = is_active_subscription(last_date, 'monthly', date.today())
        assert is_active is False


class TestSubscriptionDetection:
    """Test subscription detection."""
    
    def test_detect_monthly_subscriptions(self, monthly_subscription_transactions):
        """Test detecting monthly subscriptions."""
        subscriptions = detect_subscriptions(monthly_subscription_transactions, min_occurrences=3)
        
        assert len(subscriptions) == 1
        assert subscriptions[0].merchant_name == "Netflix"
        assert subscriptions[0].cadence == 'monthly'
        assert subscriptions[0].transaction_count == 6
        assert subscriptions[0].monthly_recurring_spend == 15.99
    
    def test_detect_multiple_subscriptions(self, mixed_transactions):
        """Test detecting multiple subscriptions."""
        subscriptions = detect_subscriptions(mixed_transactions, min_occurrences=3)
        
        # Should detect the subscription but not the one-time purchase
        assert len(subscriptions) == 1
        assert subscriptions[0].merchant_name == "Subscription Service"
    
    def test_min_occurrences_threshold(self):
        """Test minimum occurrences threshold."""
        # Create only 2 transactions (below threshold)
        transactions = [
            Transaction(
                transaction_id=f"TXN-{i}",
                account_id="ACC-1",
                date=date(2024, 1, 1) + timedelta(days=i * 30),
                amount=-10.0,
                merchant_name="Service",
                payment_channel=PaymentChannel.ONLINE,
                pending=False,
                iso_currency_code="USD"
            ) for i in range(2)
        ]
        
        subscriptions = detect_subscriptions(transactions, min_occurrences=3)
        assert len(subscriptions) == 0


class TestSubscriptionMetrics:
    """Test subscription metrics calculation."""
    
    def test_calculate_metrics(self):
        """Test calculating subscription metrics."""
        from features.subscription_detection import SubscriptionPattern
        
        subscriptions = [
            SubscriptionPattern(
                merchant_name="Service 1",
                merchant_entity_id="MERCH-1",
                cadence='monthly',
                transaction_count=6,
                first_transaction_date=date(2024, 1, 1),
                last_transaction_date=date(2024, 6, 1),
                total_spend=120.0,
                monthly_recurring_spend=20.0,
                average_amount=20.0,
                date_intervals=[30, 30, 30, 30, 30],
                confidence_score=0.9,
                is_active=True
            ),
            SubscriptionPattern(
                merchant_name="Service 2",
                merchant_entity_id="MERCH-2",
                cadence='weekly',
                transaction_count=8,
                first_transaction_date=date(2024, 1, 1),
                last_transaction_date=date(2024, 2, 26),
                total_spend=80.0,
                monthly_recurring_spend=43.32,  # 10.0 * 4.33
                average_amount=10.0,
                date_intervals=[7, 7, 7, 7, 7, 7, 7],
                confidence_score=0.8,
                is_active=True
            )
        ]
        
        total_spend = 500.0
        metrics = calculate_subscription_metrics(subscriptions, total_spend)
        
        assert metrics['subscription_count'] == 2
        assert metrics['active_subscription_count'] == 2
        assert abs(metrics['total_monthly_recurring_spend'] - 63.32) < 0.01
        assert abs(metrics['subscription_share_of_total'] - (63.32 / 500.0 * 100)) < 0.01


"""
Comprehensive Balance Analysis with Action Items.

Analyzes account balances, debts, credits and generates status indicators
and recommended actions for operator review.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from ingest.queries import (
    get_accounts_by_customer,
    get_credit_card_liabilities_by_customer,
    get_transactions_by_customer
)
from ingest.schemas import AccountType


class ActionPriority(str, Enum):
    """Priority levels for action items."""
    CRITICAL = "critical"  # Red - Immediate attention required
    HIGH = "high"  # Orange - Important but not urgent
    MEDIUM = "medium"  # Blue - Should be addressed
    LOW = "low"  # Yellow - Monitor
    GOOD = "good"  # Green - No action needed


@dataclass
class ActionItem:
    """Represents an action item for an account."""
    priority: ActionPriority
    title: str
    description: str
    recommendation: str
    color_code: str  # Hex color for UI
    
    def __post_init__(self):
        """Set color code based on priority."""
        color_map = {
            ActionPriority.CRITICAL: "#DC3545",  # Red
            ActionPriority.HIGH: "#FD7E14",  # Orange
            ActionPriority.MEDIUM: "#0D6EFD",  # Blue
            ActionPriority.LOW: "#FFC107",  # Yellow
            ActionPriority.GOOD: "#28A745"  # Green
        }
        if not self.color_code:
            self.color_code = color_map.get(self.priority, "#6C757D")


@dataclass
class AccountBalance:
    """Enhanced account balance with status and actions."""
    account_id: str
    customer_id: str
    account_type: str
    account_subtype: str
    
    # Balance details
    current_balance: float
    available_balance: Optional[float]
    credit_limit: Optional[float]
    
    # Classification
    is_asset: bool  # True for depository, False for credit/loan
    is_debt: bool  # True for credit/loan, False for depository
    
    # Status indicators
    status: str  # "healthy", "warning", "critical"
    status_color: str
    
    # Action items
    actions: List[ActionItem]
    primary_action: Optional[ActionItem]
    
    # Additional metrics
    utilization_rate: Optional[float] = None  # For credit cards
    days_until_due: Optional[int] = None  # For credit cards
    minimum_payment: Optional[float] = None  # For credit cards
    is_overdue: bool = False
    
    # Remarks
    remarks: List[str] = None
    
    def __post_init__(self):
        """Initialize remarks list."""
        if self.remarks is None:
            self.remarks = []


def analyze_customer_balances(
    customer_id: str,
    db_path: str
) -> Dict[str, Any]:
    """
    Comprehensive balance analysis for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to database
        
    Returns:
        Dictionary with detailed balance analysis
    """
    # Get accounts and liabilities
    accounts = get_accounts_by_customer(customer_id, db_path)
    liabilities = get_credit_card_liabilities_by_customer(customer_id, db_path)
    
    # Create liability lookup
    liability_map = {l.account_id: l for l in liabilities}
    
    # Analyze each account
    account_balances = []
    total_assets = 0.0
    total_debts = 0.0
    critical_actions = []
    high_actions = []
    medium_actions = []
    low_actions = []
    
    for account in accounts:
        balance_info = _analyze_account_balance(account, liability_map)
        account_balances.append(balance_info)
        
        # Aggregate totals
        if balance_info.is_asset:
            total_assets += balance_info.current_balance
        elif balance_info.is_debt:
            total_debts += balance_info.current_balance
        
        # Collect actions by priority
        for action in balance_info.actions:
            if action.priority == ActionPriority.CRITICAL:
                critical_actions.append(action)
            elif action.priority == ActionPriority.HIGH:
                high_actions.append(action)
            elif action.priority == ActionPriority.MEDIUM:
                medium_actions.append(action)
            elif action.priority == ActionPriority.LOW:
                low_actions.append(action)
    
    # Calculate net worth
    net_worth = total_assets - total_debts
    
    # Overall status
    overall_status = _determine_overall_status(
        len(critical_actions),
        len(high_actions),
        net_worth,
        total_debts,
        total_assets
    )
    
    return {
        'customer_id': customer_id,
        'account_balances': account_balances,
        'summary': {
            'total_assets': total_assets,
            'total_debts': total_debts,
            'net_worth': net_worth,
            'account_count': len(accounts),
            'overall_status': overall_status['status'],
            'overall_status_color': overall_status['color']
        },
        'actions_summary': {
            'critical_count': len(critical_actions),
            'high_count': len(high_actions),
            'medium_count': len(medium_actions),
            'low_count': len(low_actions),
            'critical_actions': critical_actions,
            'high_actions': high_actions
        }
    }


def _analyze_account_balance(
    account,
    liability_map: Dict[str, Any]
) -> AccountBalance:
    """Analyze a single account and generate action items."""
    
    is_asset = account.type == AccountType.DEPOSITORY
    is_debt = account.type == AccountType.CREDIT
    
    current_balance = account.balances.current or 0.0
    available_balance = account.balances.available
    credit_limit = account.balances.limit
    
    # Get liability details if credit account
    liability = liability_map.get(account.account_id)
    is_overdue = liability.is_overdue if liability else False
    minimum_payment = liability.minimum_payment_amount if liability else None
    days_until_due = None
    
    if liability and liability.next_payment_due_date:
        days_until_due = (liability.next_payment_due_date - date.today()).days
    
    # Calculate utilization for credit cards
    utilization_rate = None
    if is_debt and credit_limit and credit_limit > 0:
        utilization_rate = (current_balance / credit_limit) * 100
    
    # Generate action items
    actions = []
    remarks = []
    
    if is_debt:
        # Credit card analysis
        actions, remarks = _analyze_credit_account(
            current_balance, credit_limit, utilization_rate,
            is_overdue, days_until_due, minimum_payment
        )
    elif is_asset:
        # Depository account analysis
        actions, remarks = _analyze_depository_account(
            current_balance, available_balance
        )
    
    # Determine status and color
    status, status_color = _determine_account_status(actions)
    
    # Get primary action (highest priority)
    primary_action = actions[0] if actions else None
    
    return AccountBalance(
        account_id=account.account_id,
        customer_id=account.customer_id,
        account_type=account.type.value,
        account_subtype=account.subtype.value,
        current_balance=current_balance,
        available_balance=available_balance,
        credit_limit=credit_limit,
        is_asset=is_asset,
        is_debt=is_debt,
        status=status,
        status_color=status_color,
        actions=actions,
        primary_action=primary_action,
        utilization_rate=utilization_rate,
        days_until_due=days_until_due,
        minimum_payment=minimum_payment,
        is_overdue=is_overdue,
        remarks=remarks
    )


def _analyze_credit_account(
    balance: float,
    limit: Optional[float],
    utilization: Optional[float],
    is_overdue: bool,
    days_until_due: Optional[int],
    minimum_payment: Optional[float]
) -> tuple[List[ActionItem], List[str]]:
    """Analyze credit account and generate actions."""
    actions = []
    remarks = []
    
    # Critical: Overdue payment
    if is_overdue:
        actions.append(ActionItem(
            priority=ActionPriority.CRITICAL,
            title="Payment Overdue",
            description=f"Credit card payment is overdue. Balance: ${balance:,.2f}",
            recommendation="Contact customer immediately to arrange payment and avoid further penalties.",
            color_code=""
        ))
        remarks.append("⚠️ OVERDUE PAYMENT")
    
    # Critical: Payment due very soon
    elif days_until_due is not None and days_until_due <= 3:
        actions.append(ActionItem(
            priority=ActionPriority.CRITICAL,
            title="Payment Due Imminently",
            description=f"Payment due in {days_until_due} days. Minimum: ${minimum_payment:,.2f}",
            recommendation="Send payment reminder to avoid late fee.",
            color_code=""
        ))
        remarks.append(f"⏰ Payment due in {days_until_due} days")
    
    # High: Payment due soon
    elif days_until_due is not None and days_until_due <= 7:
        actions.append(ActionItem(
            priority=ActionPriority.HIGH,
            title="Payment Due Soon",
            description=f"Payment due in {days_until_due} days. Minimum: ${minimum_payment:,.2f}",
            recommendation="Send payment reminder.",
            color_code=""
        ))
        remarks.append(f"📅 Payment due in {days_until_due} days")
    
    # High: Very high utilization (>80%)
    if utilization and utilization > 80:
        actions.append(ActionItem(
            priority=ActionPriority.HIGH,
            title="Very High Credit Utilization",
            description=f"Utilization at {utilization:.1f}% (${balance:,.2f} of ${limit:,.2f})",
            recommendation="Recommend balance transfer or payment plan to reduce utilization.",
            color_code=""
        ))
        remarks.append(f"💳 High utilization: {utilization:.1f}%")
    
    # Medium: High utilization (50-80%)
    elif utilization and utilization > 50:
        actions.append(ActionItem(
            priority=ActionPriority.MEDIUM,
            title="Elevated Credit Utilization",
            description=f"Utilization at {utilization:.1f}% (${balance:,.2f} of ${limit:,.2f})",
            recommendation="Consider suggesting payment above minimum to reduce balance.",
            color_code=""
        ))
        remarks.append(f"💳 Utilization: {utilization:.1f}%")
    
    # Low: Moderate utilization (30-50%)
    elif utilization and utilization > 30:
        actions.append(ActionItem(
            priority=ActionPriority.LOW,
            title="Moderate Credit Utilization",
            description=f"Utilization at {utilization:.1f}%",
            recommendation="Monitor utilization trends.",
            color_code=""
        ))
        remarks.append(f"📊 Utilization: {utilization:.1f}%")
    
    # Good: Low utilization
    elif utilization and utilization <= 30:
        actions.append(ActionItem(
            priority=ActionPriority.GOOD,
            title="Healthy Credit Utilization",
            description=f"Utilization at {utilization:.1f}% - well managed",
            recommendation="No action needed. Credit management is good.",
            color_code=""
        ))
        remarks.append(f"✅ Good utilization: {utilization:.1f}%")
    
    # Medium: High balance relative to limit
    if limit and balance > limit * 0.9:
        actions.append(ActionItem(
            priority=ActionPriority.MEDIUM,
            title="Near Credit Limit",
            description=f"Balance ${balance:,.2f} near limit ${limit:,.2f}",
            recommendation="Risk of declined transactions. Suggest payment.",
            color_code=""
        ))
        remarks.append("⚠️ Near credit limit")
    
    return actions, remarks


def _analyze_depository_account(
    balance: float,
    available: Optional[float]
) -> tuple[List[ActionItem], List[str]]:
    """Analyze depository account and generate actions."""
    actions = []
    remarks = []
    
    # Critical: Negative or very low balance
    if balance <= 0:
        actions.append(ActionItem(
            priority=ActionPriority.CRITICAL,
            title="Negative or Zero Balance",
            description=f"Account balance: ${balance:,.2f}",
            recommendation="Contact customer about overdraft risk. Review recent transactions.",
            color_code=""
        ))
        remarks.append("🚨 Negative/zero balance")
    
    # High: Very low balance (<$100)
    elif balance < 100:
        actions.append(ActionItem(
            priority=ActionPriority.HIGH,
            title="Very Low Balance",
            description=f"Account balance: ${balance:,.2f}",
            recommendation="Risk of overdraft. Monitor for incoming deposits.",
            color_code=""
        ))
        remarks.append(f"⚠️ Low balance: ${balance:,.2f}")
    
    # Medium: Low balance (<$500)
    elif balance < 500:
        actions.append(ActionItem(
            priority=ActionPriority.MEDIUM,
            title="Low Balance",
            description=f"Account balance: ${balance:,.2f}",
            recommendation="Monitor account activity. Consider low balance alert.",
            color_code=""
        ))
        remarks.append(f"📊 Balance: ${balance:,.2f}")
    
    # Good: Healthy balance
    elif balance >= 1000:
        actions.append(ActionItem(
            priority=ActionPriority.GOOD,
            title="Healthy Balance",
            description=f"Account balance: ${balance:,.2f}",
            recommendation="Account in good standing. No action needed.",
            color_code=""
        ))
        remarks.append(f"✅ Healthy balance: ${balance:,.2f}")
    
    # Low: Moderate balance
    else:
        actions.append(ActionItem(
            priority=ActionPriority.LOW,
            title="Moderate Balance",
            description=f"Account balance: ${balance:,.2f}",
            recommendation="Monitor for normal activity.",
            color_code=""
        ))
        remarks.append(f"📊 Balance: ${balance:,.2f}")
    
    # Check available vs current balance discrepancy
    if available is not None and available < balance * 0.5:
        actions.append(ActionItem(
            priority=ActionPriority.MEDIUM,
            title="Low Available Balance",
            description=f"Available: ${available:,.2f} vs Current: ${balance:,.2f}",
            recommendation="Large pending transactions. Monitor for sufficient funds.",
            color_code=""
        ))
        remarks.append(f"⏳ Available: ${available:,.2f}")
    
    return actions, remarks


def _determine_account_status(actions: List[ActionItem]) -> tuple[str, str]:
    """Determine account status based on actions."""
    if not actions:
        return "unknown", "#6C757D"
    
    # Get highest priority action
    priority_order = [
        ActionPriority.CRITICAL,
        ActionPriority.HIGH,
        ActionPriority.MEDIUM,
        ActionPriority.LOW,
        ActionPriority.GOOD
    ]
    
    for priority in priority_order:
        for action in actions:
            if action.priority == priority:
                status_map = {
                    ActionPriority.CRITICAL: ("critical", "#DC3545"),
                    ActionPriority.HIGH: ("warning", "#FD7E14"),
                    ActionPriority.MEDIUM: ("attention", "#0D6EFD"),
                    ActionPriority.LOW: ("monitor", "#FFC107"),
                    ActionPriority.GOOD: ("healthy", "#28A745")
                }
                return status_map.get(priority, ("unknown", "#6C757D"))
    
    return "unknown", "#6C757D"


def _determine_overall_status(
    critical_count: int,
    high_count: int,
    net_worth: float,
    total_debts: float,
    total_assets: float
) -> Dict[str, Any]:
    """Determine overall customer financial status."""
    
    if critical_count > 0:
        return {
            'status': 'critical',
            'color': '#DC3545',
            'description': f'{critical_count} critical issue(s) require immediate attention'
        }
    
    if high_count > 0:
        return {
            'status': 'warning',
            'color': '#FD7E14',
            'description': f'{high_count} important issue(s) need attention'
        }
    
    if net_worth < 0:
        return {
            'status': 'warning',
            'color': '#FD7E14',
            'description': 'Net worth is negative'
        }
    
    if total_assets > 0 and (total_debts / total_assets) > 0.5:
        return {
            'status': 'attention',
            'color': '#0D6EFD',
            'description': 'Debt-to-asset ratio above 50%'
        }
    
    return {
        'status': 'healthy',
        'color': '#28A745',
        'description': 'Financial health is good'
    }


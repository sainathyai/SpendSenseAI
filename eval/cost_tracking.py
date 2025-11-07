"""
Cost Tracking for SpendSenseAI.

Tracks LLM API costs and usage:
- Request tracking
- Cost calculation based on model and tokens
- Daily/monthly aggregation
- Cost per user metrics
"""

from typing import Dict, Optional, List
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json

from ingest.database import get_connection


# OpenAI pricing (as of 2024, in USD per 1M tokens)
# Input tokens
PRICING_INPUT = {
    "gpt-4o-mini": 0.15,  # $0.15 per 1M input tokens
    "gpt-4o": 2.50,
    "gpt-4-turbo": 10.00,
    "gpt-3.5-turbo": 0.50
}

# Output tokens
PRICING_OUTPUT = {
    "gpt-4o-mini": 0.60,  # $0.60 per 1M output tokens
    "gpt-4o": 10.00,
    "gpt-4-turbo": 30.00,
    "gpt-3.5-turbo": 1.50
}


@dataclass
class LLMUsage:
    """LLM API usage record."""
    request_id: str
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    user_id: Optional[str] = None
    recommendation_id: Optional[str] = None


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for LLM API call.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Cost in USD
    """
    input_price = PRICING_INPUT.get(model, PRICING_INPUT["gpt-4o-mini"])
    output_price = PRICING_OUTPUT.get(model, PRICING_OUTPUT["gpt-4o-mini"])
    
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    
    return input_cost + output_cost


def create_cost_tracking_tables(db_path: str) -> None:
    """Create cost tracking tables in database."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage (
                request_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                user_id TEXT,
                recommendation_id TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp 
            ON llm_usage(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_usage_user 
            ON llm_usage(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_usage_date 
            ON llm_usage(DATE(timestamp))
        """)
        
        conn.commit()


def track_llm_usage(
    db_path: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    user_id: Optional[str] = None,
    recommendation_id: Optional[str] = None
) -> LLMUsage:
    """
    Track LLM API usage and cost.
    
    Args:
        db_path: Path to database
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        user_id: Optional user ID
        recommendation_id: Optional recommendation ID
        
    Returns:
        LLMUsage object
    """
    create_cost_tracking_tables(db_path)
    
    total_tokens = input_tokens + output_tokens
    cost = calculate_cost(model, input_tokens, output_tokens)
    
    request_id = f"LLM-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    usage = LLMUsage(
        request_id=request_id,
        timestamp=datetime.now(),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost=cost,
        user_id=user_id,
        recommendation_id=recommendation_id
    )
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO llm_usage 
            (request_id, timestamp, model, input_tokens, output_tokens, total_tokens, cost, user_id, recommendation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usage.request_id,
            usage.timestamp.isoformat(),
            usage.model,
            usage.input_tokens,
            usage.output_tokens,
            usage.total_tokens,
            usage.cost,
            usage.user_id,
            usage.recommendation_id
        ))
        conn.commit()
    
    return usage


def get_cost_summary(
    db_path: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """
    Get cost summary for date range.
    
    Args:
        db_path: Path to database
        start_date: Start date (default: today)
        end_date: End date (default: today)
        
    Returns:
        Dictionary with cost summary
    """
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = date.today()
    
    create_cost_tracking_tables(db_path)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Daily costs
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as request_count,
                SUM(cost) as total_cost,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens
            FROM llm_usage
            WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (start_date.isoformat(), end_date.isoformat()))
        
        daily_costs = []
        for row in cursor.fetchall():
            daily_costs.append({
                "date": row[0],
                "request_count": row[1],
                "total_cost": row[2] or 0.0,
                "total_input_tokens": row[3] or 0,
                "total_output_tokens": row[4] or 0,
                "total_tokens": row[5] or 0
            })
        
        # Total summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost_per_request,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens
            FROM llm_usage
            WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ?
        """, (start_date.isoformat(), end_date.isoformat()))
        
        row = cursor.fetchone()
        total_requests = row[0] or 0
        total_cost = row[1] or 0.0
        avg_cost = row[2] or 0.0
        total_input_tokens = row[3] or 0
        total_output_tokens = row[4] or 0
        
        # Today's costs
        today = date.today().isoformat()
        cursor.execute("""
            SELECT 
                COUNT(*) as request_count,
                SUM(cost) as total_cost
            FROM llm_usage
            WHERE DATE(timestamp) = ?
        """, (today,))
        
        today_row = cursor.fetchone()
        today_requests = today_row[0] or 0
        today_cost = today_row[1] or 0.0
        
        # This month's costs
        month_start = date.today().replace(day=1).isoformat()
        cursor.execute("""
            SELECT 
                COUNT(*) as request_count,
                SUM(cost) as total_cost
            FROM llm_usage
            WHERE DATE(timestamp) >= ?
        """, (month_start,))
        
        month_row = cursor.fetchone()
        month_requests = month_row[0] or 0
        month_cost = month_row[1] or 0.0
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_requests": total_requests,
        "total_cost": total_cost,
        "avg_cost_per_request": avg_cost,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "today_requests": today_requests,
        "today_cost": today_cost,
        "month_requests": month_requests,
        "month_cost": month_cost,
        "daily_costs": daily_costs
    }



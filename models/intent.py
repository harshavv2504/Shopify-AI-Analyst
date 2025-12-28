"""
Intent data models for question classification
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class IntentType(str, Enum):
    """Types of analytics intents"""
    INVENTORY_PROJECTION = "inventory_projection"
    SALES_TRENDS = "sales_trends"
    CUSTOMER_BEHAVIOR = "customer_behavior"
    PRODUCT_PERFORMANCE = "product_performance"
    STOCKOUT_PREDICTION = "stockout_prediction"
    UNKNOWN = "unknown"


@dataclass
class TimePeriod:
    """Represents a time period extracted from a question"""
    description: str  # e.g., "last week", "next month"
    days: Optional[int] = None  # Number of days (positive for future, negative for past)
    start_date: Optional[str] = None  # ISO format date
    end_date: Optional[str] = None  # ISO format date


@dataclass
class Intent:
    """
    Represents the classified intent of a user question
    """
    type: IntentType
    time_period: Optional[TimePeriod]
    entities: List[str]  # Product names, customer segments, etc.
    metrics: List[str]  # count, sum, average, etc.
    confidence: float  # 0.0 to 1.0
    raw_question: str
    
    def is_ambiguous(self) -> bool:
        """Check if the intent is ambiguous (low confidence)"""
        return self.confidence < 0.7

"""
Intent Classifier
Uses OpenAI GPT-4o-mini to classify user questions and extract structured information
"""
import json
import logging
from typing import Dict, Any
import re
from datetime import datetime, timedelta, timezone

from services.openai_service import OpenAIService
from models.intent import Intent, IntentType, TimePeriod

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies natural language questions into structured intents
    Uses dependency injection for OpenAI service
    """
    
    def __init__(self, openai_service: OpenAIService):
        """
        Initialize intent classifier
        
        Args:
            openai_service: OpenAI service instance for LLM calls
        """
        self.openai_service = openai_service
        logger.info("Intent classifier initialized")
    
    def classify(self, question: str) -> Intent:
        """
        Classify a natural language question into a structured intent
        
        Args:
            question: User's natural language question
        
        Returns:
            Intent object with classified information
        """
        try:
            # Build prompt for intent classification
            prompt = self._build_classification_prompt(question)
            
            # Get classification from OpenAI
            messages = self.openai_service.create_prompt(
                system_message=self._get_system_message(),
                user_message=prompt
            )
            
            response = self.openai_service.chat_completion_json(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent classification
                max_tokens=500
            )
            
            # Parse response into Intent object
            intent = self._parse_classification_response(response, question)
            
            logger.info(f"Classified question as {intent.type} with confidence {intent.confidence}")
            
            return intent
        
        except Exception as e:
            logger.error(f"Failed to classify intent: {e}")
            # Return unknown intent as fallback
            return Intent(
                type=IntentType.UNKNOWN,
                time_period=None,
                entities=[],
                metrics=[],
                confidence=0.0,
                raw_question=question
            )
    
    def _get_system_message(self) -> str:
        """Get the system message for intent classification"""
        return """You are an expert at analyzing business analytics questions for Shopify stores.
Your task is to classify questions and extract structured information.

Classify questions into these intent types:
- inventory_projection: Questions about future inventory needs
- sales_trends: Questions about sales patterns and top products
- customer_behavior: Questions about customer patterns and segments
- product_performance: Questions about specific product metrics
- stockout_prediction: Questions about products running out of stock
- unknown: Questions that don't fit the above categories

Extract:
1. Time period (e.g., "last week", "next month", "30 days")
2. Entities (product names, customer types, etc.)
3. Metrics (count, sum, average, total, etc.)
4. Confidence level (0.0 to 1.0)

Respond in JSON format."""
    
    def _build_classification_prompt(self, question: str) -> str:
        """
        Build the classification prompt
        
        Args:
            question: User's question
        
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this question and provide classification:

Question: "{question}"

Respond with JSON in this exact format:
{{
    "intent_type": "inventory_projection|sales_trends|customer_behavior|product_performance|stockout_prediction|unknown",
    "time_period": {{
        "description": "description of time period or null",
        "days": number of days (negative for past, positive for future) or null
    }},
    "entities": ["list", "of", "entities"],
    "metrics": ["list", "of", "metrics"],
    "confidence": 0.0 to 1.0
}}

Examples:
- "What were my top 5 selling products last week?" → intent_type: "sales_trends", time_period: {{"description": "last week", "days": -7}}, metrics: ["count", "sum"]
- "How many units of Product X will I need next month?" → intent_type: "inventory_projection", time_period: {{"description": "next month", "days": 30}}, entities: ["Product X"]
- "Which customers placed repeat orders?" → intent_type: "customer_behavior", entities: ["repeat customers"], metrics: ["count"]"""
    
    def _parse_classification_response(self, response: Dict[str, Any], original_question: str) -> Intent:
        """
        Parse OpenAI response into Intent object
        
        Args:
            response: JSON response from OpenAI
            original_question: Original user question
        
        Returns:
            Intent object
        """
        try:
            # Extract intent type
            intent_type_str = response.get("intent_type", "unknown")
            try:
                intent_type = IntentType(intent_type_str)
            except ValueError:
                logger.warning(f"Unknown intent type: {intent_type_str}")
                intent_type = IntentType.UNKNOWN
            
            # Extract time period
            time_period_data = response.get("time_period")
            time_period = None
            if time_period_data and time_period_data.get("description"):
                time_period = TimePeriod(
                    description=time_period_data.get("description"),
                    days=time_period_data.get("days")
                )
            
            # Extract entities and metrics
            entities = response.get("entities", [])
            metrics = response.get("metrics", [])
            confidence = float(response.get("confidence", 0.5))
            
            return Intent(
                type=intent_type,
                time_period=time_period,
                entities=entities,
                metrics=metrics,
                confidence=confidence,
                raw_question=original_question
            )
        
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                time_period=None,
                entities=[],
                metrics=[],
                confidence=0.0,
                raw_question=original_question
            )
    
    def extract_time_period_dates(self, time_period: TimePeriod) -> TimePeriod:
        """
        Convert time period description to actual dates
        
        Args:
            time_period: TimePeriod with description and days
        
        Returns:
            TimePeriod with start_date and end_date filled in
        """
        if not time_period or not time_period.days:
            return time_period
        
        now = datetime.now(timezone.utc)
        
        if time_period.days < 0:
            # Past period
            end_date = now
            start_date = now + timedelta(days=time_period.days)
        else:
            # Future period
            start_date = now
            end_date = now + timedelta(days=time_period.days)
        
        time_period.start_date = start_date.isoformat()
        time_period.end_date = end_date.isoformat()
        
        return time_period

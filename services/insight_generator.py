"""
Insight Generator
Analyzes query results and generates business insights using OpenAI GPT-4o-mini
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Generates business insights from query results
    Uses dependency injection for OpenAI service
    """
    
    MIN_DATA_POINTS = 10
    MIN_DAYS_FOR_HIGH_CONFIDENCE = 7
    
    def __init__(self, openai_service: OpenAIService):
        """
        Initialize insight generator
        
        Args:
            openai_service: OpenAI service instance
        """
        self.openai_service = openai_service
        logger.info("Insight generator initialized")
    
    def generate_insights(
        self,
        query_results: List[Dict[str, Any]],
        question: str,
        intent_type: str
    ) -> Dict[str, Any]:
        """
        Generate insights from query results
        
        Args:
            query_results: Raw data from Shopify query
            question: Original user question
            intent_type: Type of intent
        
        Returns:
            Dictionary with insights and metadata
        """
        try:
            # Calculate confidence based on data quality
            confidence = self._determine_confidence(query_results)
            
            # Generate insights using LLM
            insights = self._generate_insights_with_llm(query_results, question, intent_type)
            
            return {
                "insights": insights,
                "confidence": confidence,
                "data_points": len(query_results)
            }
        
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return {
                "insights": "Unable to generate insights from the data.",
                "confidence": "low",
                "data_points": 0
            }
    
    def calculate_sales_velocity(self, orders: List[Dict[str, Any]], days: int = 30) -> float:
        """
        Calculate sales velocity (units per day)
        
        Args:
            orders: List of order dictionaries
            days: Number of days to calculate over
        
        Returns:
            Units per day
        """
        if not orders or days <= 0:
            return 0.0
        
        total_quantity = sum(
            sum(item.get("quantity", 0) for item in order.get("line_items", []))
            for order in orders
        )
        
        velocity = total_quantity / days
        logger.debug(f"Calculated sales velocity: {velocity:.2f} units/day")
        return velocity
    
    def identify_top_products(
        self,
        orders: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify top-performing products
        
        Args:
            orders: List of order dictionaries
            limit: Number of top products to return
        
        Returns:
            List of top products with metrics
        """
        product_metrics = {}
        
        for order in orders:
            for item in order.get("line_items", []):
                product_title = item.get("title", "Unknown")
                quantity = item.get("quantity", 0)
                price = item.get("price", 0)
                
                if product_title not in product_metrics:
                    product_metrics[product_title] = {
                        "title": product_title,
                        "quantity_sold": 0,
                        "revenue": 0.0
                    }
                
                product_metrics[product_title]["quantity_sold"] += quantity
                product_metrics[product_title]["revenue"] += quantity * float(price)
        
        # Sort by revenue
        top_products = sorted(
            product_metrics.values(),
            key=lambda x: x["revenue"],
            reverse=True
        )[:limit]
        
        logger.debug(f"Identified {len(top_products)} top products")
        return top_products
    
    def analyze_order_frequency(self, customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze customer order frequency
        
        Args:
            customers: List of customer dictionaries
        
        Returns:
            Dictionary with frequency analysis
        """
        if not customers:
            return {"one_time": 0, "repeat": 0, "frequent": 0, "total": 0}
        
        one_time = sum(1 for c in customers if c.get("orders_count", 0) == 1)
        repeat = sum(1 for c in customers if 1 < c.get("orders_count", 0) <= 5)
        frequent = sum(1 for c in customers if c.get("orders_count", 0) > 5)
        
        analysis = {
            "one_time": one_time,
            "repeat": repeat,
            "frequent": frequent,
            "total": len(customers)
        }
        
        logger.debug(f"Order frequency analysis: {analysis}")
        return analysis
    
    def _determine_confidence(self, data: List[Dict[str, Any]]) -> str:
        """
        Determine confidence level based on data quality
        
        Args:
            data: Query results
        
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if not data:
            return "low"
        
        data_points = len(data)
        
        if data_points < self.MIN_DATA_POINTS:
            return "low"
        elif data_points < 30:
            return "medium"
        else:
            return "high"
    
    def _generate_insights_with_llm(
        self,
        data: List[Dict[str, Any]],
        question: str,
        intent_type: str
    ) -> str:
        """
        Generate insights using OpenAI
        
        Args:
            data: Query results
            question: Original question
            intent_type: Type of intent
        
        Returns:
            Generated insights as string
        """
        prompt = self._build_insight_prompt(data, question, intent_type)
        
        messages = self.openai_service.create_prompt(
            system_message=self._get_system_message(),
            user_message=prompt
        )
        
        insights = self.openai_service.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=500
        )
        
        return insights.strip()
    
    def _get_system_message(self) -> str:
        """Get system message for insight generation"""
        return """You are a business analytics expert helping Shopify store owners understand their data.

Your role is to:
1. Analyze data and identify key patterns
2. Provide actionable insights
3. Use simple, business-friendly language
4. Include specific numbers and context
5. Make recommendations when appropriate

Avoid technical jargon. Speak like you're advising a friend who owns a store."""
    
    def _build_insight_prompt(
        self,
        data: List[Dict[str, Any]],
        question: str,
        intent_type: str
    ) -> str:
        """
        Build prompt for insight generation
        
        Args:
            data: Query results
            question: Original question
            intent_type: Type of intent
        
        Returns:
            Formatted prompt
        """
        # Summarize data for prompt
        data_summary = self._summarize_data(data)
        
        prompt = f"""Analyze this data and provide business insights.

Original Question: "{question}"
Analysis Type: {intent_type}

Data Summary:
{data_summary}

Provide:
1. A clear answer to the question
2. Key insights from the data
3. Actionable recommendations
4. Context for the numbers

Keep it concise (2-3 paragraphs) and business-friendly."""
        
        return prompt
    
    def _summarize_data(self, data: List[Dict[str, Any]], max_items: int = 10) -> str:
        """
        Summarize data for LLM prompt
        
        Args:
            data: Query results
            max_items: Maximum items to include
        
        Returns:
            String summary of data
        """
        if not data:
            return "No data available"
        
        summary_items = data[:max_items]
        summary = f"Total records: {len(data)}\n\n"
        
        for i, item in enumerate(summary_items, 1):
            summary += f"{i}. {item}\n"
        
        if len(data) > max_items:
            summary += f"\n... and {len(data) - max_items} more records"
        
        return summary

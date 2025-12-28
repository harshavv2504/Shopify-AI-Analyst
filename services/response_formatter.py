"""
Response Formatter
Formats technical insights into business-friendly language using OpenAI GPT-4o-mini
"""
import logging
import re
from typing import Dict, Any, List

from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formats responses in business-friendly language
    Uses dependency injection for OpenAI service
    """
    
    # Technical jargon to avoid
    TECHNICAL_TERMS = [
        "API", "query", "database", "SQL", "JSON", "HTTP",
        "endpoint", "parameter", "aggregation", "schema"
    ]
    
    def __init__(self, openai_service: OpenAIService):
        """
        Initialize response formatter
        
        Args:
            openai_service: OpenAI service instance
        """
        self.openai_service = openai_service
        logger.info("Response formatter initialized")
    
    def format_response(
        self,
        insights: str,
        question: str,
        confidence: str,
        data_summary: Dict[str, Any]
    ) -> str:
        """
        Format insights into business-friendly response
        
        Args:
            insights: Raw insights from insight generator
            question: Original question
            confidence: Confidence level
            data_summary: Summary of data used
        
        Returns:
            Formatted response string
        """
        try:
            # Use LLM to ensure business-friendly language
            formatted = self._format_with_llm(insights, question, confidence)
            
            # Validate no technical jargon
            if self._contains_technical_jargon(formatted):
                logger.warning("Response contains technical jargon, reformatting")
                formatted = self._remove_jargon(formatted)
            
            # Add numerical context
            formatted = self._add_numerical_context(formatted, data_summary)
            
            # Structure response
            structured = self._structure_response(formatted, confidence)
            
            return structured
        
        except Exception as e:
            logger.error(f"Failed to format response: {e}")
            return insights  # Return raw insights as fallback
    
    def _format_with_llm(self, insights: str, question: str, confidence: str) -> str:
        """
        Format insights using OpenAI
        
        Args:
            insights: Raw insights
            question: Original question
            confidence: Confidence level
        
        Returns:
            Formatted response
        """
        prompt = self._build_formatting_prompt(insights, question, confidence)
        
        messages = self.openai_service.create_prompt(
            system_message=self._get_system_message(),
            user_message=prompt
        )
        
        formatted = self.openai_service.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=600
        )
        
        return formatted.strip()
    
    def _get_system_message(self) -> str:
        """Get system message for formatting"""
        return """You are an expert at explaining business analytics in simple terms.

Your role is to:
1. Convert technical analysis into plain English
2. Avoid jargon and technical terms
3. Use conversational, friendly language
4. Include specific numbers with context
5. Make insights actionable

Write like you're explaining to a friend who owns a store, not a data scientist."""
    
    def _build_formatting_prompt(self, insights: str, question: str, confidence: str) -> str:
        """Build prompt for formatting"""
        return f"""Rewrite this analysis in simple, business-friendly language.

Original Question: "{question}"
Confidence: {confidence}

Analysis:
{insights}

Requirements:
- Use simple, conversational language
- Avoid technical jargon
- Include specific numbers with context
- Make it actionable
- Keep it concise (2-3 paragraphs)

Rewritten response:"""
    
    def _contains_technical_jargon(self, text: str) -> bool:
        """
        Check if text contains technical jargon
        
        Args:
            text: Text to check
        
        Returns:
            True if jargon found
        """
        text_lower = text.lower()
        for term in self.TECHNICAL_TERMS:
            if term.lower() in text_lower:
                logger.debug(f"Found technical term: {term}")
                return True
        return False
    
    def _remove_jargon(self, text: str) -> str:
        """
        Remove or replace technical jargon
        
        Args:
            text: Text with potential jargon
        
        Returns:
            Cleaned text
        """
        replacements = {
            "API": "system",
            "query": "search",
            "database": "records",
            "SQL": "data",
            "JSON": "data",
            "HTTP": "connection",
            "endpoint": "service",
            "parameter": "setting",
            "aggregation": "summary",
            "schema": "structure"
        }
        
        result = text
        for term, replacement in replacements.items():
            result = re.sub(rf'\b{term}\b', replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _add_numerical_context(self, text: str, data_summary: Dict[str, Any]) -> str:
        """
        Add context to numerical data
        
        Args:
            text: Response text
            data_summary: Summary of data
        
        Returns:
            Text with added context
        """
        # Add data point context if not already present
        data_points = data_summary.get("data_points", 0)
        
        if data_points > 0 and "based on" not in text.lower():
            context = f"\n\n(Based on analysis of {data_points} data points)"
            text += context
        
        return text
    
    def _structure_response(self, text: str, confidence: str) -> str:
        """
        Structure response with clear sections
        
        Args:
            text: Response text
            confidence: Confidence level
        
        Returns:
            Structured response
        """
        # Ensure confidence is communicated
        if confidence in ["low", "medium"] and "confidence" not in text.lower():
            confidence_note = f"\n\nNote: This analysis has {confidence} confidence due to limited data. Consider gathering more information for better insights."
            text += confidence_note
        
        return text
    
    def generate_reorder_recommendation(
        self,
        velocity: float,
        days: int,
        current_stock: int = 0
    ) -> str:
        """
        Generate reorder recommendation
        
        Args:
            velocity: Sales velocity (units per day)
            days: Number of days to project
            current_stock: Current stock level
        
        Returns:
            Recommendation string
        """
        projected_need = velocity * days
        reorder_amount = max(0, projected_need - current_stock)
        
        recommendation = f"Based on your sales velocity of {velocity:.1f} units per day, "
        recommendation += f"you'll need approximately {projected_need:.0f} units over the next {days} days. "
        
        if current_stock > 0:
            recommendation += f"With {current_stock} units currently in stock, "
            recommendation += f"consider reordering {reorder_amount:.0f} units to avoid stockouts."
        else:
            recommendation += f"Consider ordering {projected_need:.0f} units."
        
        return recommendation
    
    def format_customer_analysis(
        self,
        one_time: int,
        repeat: int,
        frequent: int,
        total: int
    ) -> str:
        """
        Format customer analysis with counts and percentages
        
        Args:
            one_time: Number of one-time customers
            repeat: Number of repeat customers
            frequent: Number of frequent customers
            total: Total customers
        
        Returns:
            Formatted analysis
        """
        if total == 0:
            return "No customer data available for analysis."
        
        one_time_pct = (one_time / total) * 100
        repeat_pct = (repeat / total) * 100
        frequent_pct = (frequent / total) * 100
        
        analysis = f"Out of {total} customers:\n"
        analysis += f"- {one_time} ({one_time_pct:.1f}%) are one-time buyers\n"
        analysis += f"- {repeat} ({repeat_pct:.1f}%) are repeat customers (2-5 orders)\n"
        analysis += f"- {frequent} ({frequent_pct:.1f}%) are frequent buyers (5+ orders)\n"
        
        # Add recommendation
        if one_time_pct > 60:
            analysis += "\nConsider implementing a loyalty program to convert one-time buyers into repeat customers."
        elif frequent_pct > 30:
            analysis += "\nYou have a strong base of loyal customers. Focus on retention and referral programs."
        
        return analysis
    
    def explain_methodology(self, method_type: str, details: Dict[str, Any]) -> str:
        """
        Explain calculation methodology in simple terms
        
        Args:
            method_type: Type of calculation
            details: Calculation details
        
        Returns:
            Explanation string
        """
        explanations = {
            "sales_velocity": f"We calculated your average daily sales by dividing total units sold ({details.get('total_units', 0)}) by the number of days ({details.get('days', 0)}).",
            "projection": f"We projected future needs by multiplying your daily sales rate by the number of days ahead.",
            "trend_analysis": f"We compared sales across different time periods to identify patterns.",
            "customer_segmentation": f"We grouped customers based on their purchase frequency."
        }
        
        return explanations.get(method_type, "Analysis based on your historical data.")

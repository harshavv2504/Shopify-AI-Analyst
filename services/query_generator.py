"""
ShopifyQL Query Generator
Generates ShopifyQL queries from structured intents using OpenAI GPT-4o-mini
"""
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone

from services.openai_service import OpenAIService
from models.intent import Intent, IntentType, TimePeriod

logger = logging.getLogger(__name__)


class ShopifyQLGenerator:
    """
    Generates ShopifyQL queries from structured intents
    Uses dependency injection for OpenAI service
    """
    
    # Mapping of intent types to Shopify data sources
    INTENT_TO_DATA_SOURCES = {
        IntentType.INVENTORY_PROJECTION: ["orders", "products", "inventory_levels"],
        IntentType.SALES_TRENDS: ["orders", "products"],
        IntentType.CUSTOMER_BEHAVIOR: ["customers", "orders"],
        IntentType.PRODUCT_PERFORMANCE: ["products", "orders"],
        IntentType.STOCKOUT_PREDICTION: ["products", "inventory_levels", "orders"],
    }
    
    def __init__(self, openai_service: OpenAIService):
        """
        Initialize query generator
        
        Args:
            openai_service: OpenAI service instance for LLM calls
        """
        self.openai_service = openai_service
        logger.info("ShopifyQL generator initialized")
    
    def generate(self, intent: Intent) -> str:
        """
        Generate ShopifyQL query from intent
        
        Args:
            intent: Classified intent object
        
        Returns:
            ShopifyQL query string
        
        Raises:
            ValueError: If query cannot be generated
        """
        try:
            # Map intent to data sources
            data_sources = self._map_intent_to_data_sources(intent)
            
            # Build time filters
            time_filter = self._build_time_filter(intent.time_period)
            
            # Build aggregations
            aggregations = self._build_aggregations(intent.metrics)
            
            # Generate query using OpenAI
            query = self._generate_query_with_llm(intent, data_sources, time_filter, aggregations)
            
            # Validate syntax
            self._validate_query_syntax(query)
            
            logger.info(f"Generated ShopifyQL query for {intent.type}")
            return query
        
        except Exception as e:
            logger.error(f"Failed to generate query: {e}")
            raise ValueError(f"Cannot generate query: {str(e)}")
    
    def _map_intent_to_data_sources(self, intent: Intent) -> List[str]:
        """
        Map intent type to required Shopify data sources
        
        Args:
            intent: Intent object
        
        Returns:
            List of data source names
        """
        data_sources = self.INTENT_TO_DATA_SOURCES.get(intent.type, ["orders"])
        logger.debug(f"Mapped {intent.type} to data sources: {data_sources}")
        return data_sources
    
    def _build_time_filter(self, time_period: Optional[TimePeriod]) -> str:
        """
        Build time filter clause from time period
        
        Args:
            time_period: TimePeriod object or None
        
        Returns:
            Time filter string for query
        """
        if not time_period or not time_period.days:
            return ""
        
        now = datetime.now(timezone.utc)
        
        if time_period.days < 0:
            # Past period
            start_date = now + timedelta(days=time_period.days)
            end_date = now
            return f"created_at >= '{start_date.isoformat()}' AND created_at <= '{end_date.isoformat()}'"
        else:
            # Future period (for projections)
            return f"projected_date <= '{(now + timedelta(days=time_period.days)).isoformat()}'"
    
    def _build_aggregations(self, metrics: List[str]) -> str:
        """
        Build aggregation clause from metrics
        
        Args:
            metrics: List of metric names
        
        Returns:
            Aggregation string for query
        """
        if not metrics:
            return ""
        
        aggregation_map = {
            "count": "COUNT(*)",
            "sum": "SUM(quantity)",
            "average": "AVG(price)",
            "total": "SUM(total_price)",
            "max": "MAX(quantity)",
            "min": "MIN(quantity)"
        }
        
        aggs = [aggregation_map.get(m.lower(), "COUNT(*)") for m in metrics]
        return ", ".join(aggs)
    
    def _generate_query_with_llm(
        self,
        intent: Intent,
        data_sources: List[str],
        time_filter: str,
        aggregations: str
    ) -> str:
        """
        Generate ShopifyQL query using OpenAI
        
        Args:
            intent: Intent object
            data_sources: List of data sources
            time_filter: Time filter clause
            aggregations: Aggregation clause
        
        Returns:
            Generated ShopifyQL query
        """
        prompt = self._build_query_generation_prompt(intent, data_sources, time_filter, aggregations)
        
        messages = self.openai_service.create_prompt(
            system_message=self._get_system_message(),
            user_message=prompt
        )
        
        query = self.openai_service.chat_completion(
            messages=messages,
            temperature=0.2,  # Low temperature for consistent query generation
            max_tokens=300
        )
        
        # Clean up the query
        query = query.strip()
        if query.startswith("```"):
            # Remove code block markers if present
            query = query.replace("```sql", "").replace("```", "").strip()
        
        return query
    
    def _get_system_message(self) -> str:
        """Get system message for query generation"""
        return """You are an expert at generating ShopifyQL queries for Shopify Analytics.

ShopifyQL is similar to SQL but specific to Shopify data.

Available tables:
- orders: id, created_at, total_price, line_items (array), customer_id
- products: id, title, vendor, product_type, variants (array)
- customers: id, email, orders_count, total_spent, created_at
- inventory_levels: inventory_item_id, location_id, available

Generate syntactically correct ShopifyQL queries. Use proper aggregations, filters, and joins.
Return ONLY the query, no explanations."""
    
    def _build_query_generation_prompt(
        self,
        intent: Intent,
        data_sources: List[str],
        time_filter: str,
        aggregations: str
    ) -> str:
        """
        Build prompt for query generation
        
        Args:
            intent: Intent object
            data_sources: List of data sources
            time_filter: Time filter clause
            aggregations: Aggregation clause
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Generate a ShopifyQL query for this request:

Question: "{intent.raw_question}"
Intent: {intent.type.value}
Data sources needed: {', '.join(data_sources)}
"""
        
        if time_filter:
            prompt += f"Time filter: {time_filter}\n"
        
        if aggregations:
            prompt += f"Aggregations: {aggregations}\n"
        
        if intent.entities:
            prompt += f"Entities: {', '.join(intent.entities)}\n"
        
        prompt += "\nGenerate the ShopifyQL query:"
        
        return prompt
    
    def _validate_query_syntax(self, query: str) -> bool:
        """
        Validate ShopifyQL query syntax
        
        Args:
            query: Query string to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If query is invalid
        """
        if not query or len(query.strip()) == 0:
            raise ValueError("Query is empty")
        
        # Basic syntax checks
        query_upper = query.upper()
        
        # Must contain SELECT
        if "SELECT" not in query_upper:
            raise ValueError("Query must contain SELECT statement")
        
        # Must contain FROM
        if "FROM" not in query_upper:
            raise ValueError("Query must contain FROM clause")
        
        # Check for dangerous operations (basic security)
        # Use word boundaries to avoid false positives (e.g., "created_at" contains "create")
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        for keyword in dangerous_keywords:
            # Check for whole word matches using word boundaries
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper):
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        logger.debug("Query syntax validation passed")
        return True

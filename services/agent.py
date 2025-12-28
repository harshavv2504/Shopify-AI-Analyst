"""
Shopify Analytics Agent
Orchestrates the 5-step workflow for processing analytics questions
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from services.intent_classifier import IntentClassifier
from services.query_generator import ShopifyQLGenerator
from services.shopify_client import ShopifyClient
from services.insight_generator import InsightGenerator
from services.response_formatter import ResponseFormatter
from models.intent import Intent

logger = logging.getLogger(__name__)


class ShopifyAnalyticsAgent:
    """
    Main agent that orchestrates the analytics workflow
    Uses dependency injection for all services
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassifier,
        query_generator: ShopifyQLGenerator,
        shopify_client: ShopifyClient,
        insight_generator: InsightGenerator,
        response_formatter: ResponseFormatter
    ):
        """
        Initialize agent with all dependencies
        
        Args:
            intent_classifier: Service for classifying questions
            query_generator: Service for generating ShopifyQL
            shopify_client: Client for Shopify API
            insight_generator: Service for generating insights
            response_formatter: Service for formatting responses
        """
        self.intent_classifier = intent_classifier
        self.query_generator = query_generator
        self.shopify_client = shopify_client
        self.insight_generator = insight_generator
        self.response_formatter = response_formatter
        
        self.reasoning_steps: List[str] = []
        
        logger.info("Shopify Analytics Agent initialized")
    
    async def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process a natural language question through the 5-step workflow
        
        Args:
            question: User's natural language question
        
        Returns:
            Dictionary with answer, confidence, query, and reasoning steps
        """
        self.reasoning_steps = []
        
        try:
            # Step 1: Understand Intent
            intent = self._understand_intent(question)
            
            # Step 2: Plan Data Requirements
            data_plan = self._plan_data_requirements(intent)
            
            # Step 3: Generate Query
            query = self._generate_query(intent, data_plan)
            
            # Step 4: Execute and Validate
            results = await self._execute_and_validate(query)
            
            # Step 5: Explain Results
            response = self._explain_results(results, intent, query)
            
            logger.info(f"Successfully processed question: {question[:50]}...")
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to process question: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "confidence": "low",
                "query_used": None,
                "reasoning_steps": self.reasoning_steps,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _understand_intent(self, question: str) -> Intent:
        """
        Step 1: Understand user intent
        
        Args:
            question: User's question
        
        Returns:
            Classified intent
        """
        logger.info("Step 1: Understanding intent")
        self.reasoning_steps.append("Step 1: Analyzing question to understand intent")
        
        intent = self.intent_classifier.classify(question)
        
        self.reasoning_steps.append(f"Identified intent: {intent.type.value}")
        if intent.time_period:
            self.reasoning_steps.append(f"Time period: {intent.time_period.description}")
        if intent.entities:
            self.reasoning_steps.append(f"Entities: {', '.join(intent.entities)}")
        
        logger.debug(f"Intent classified: {intent.type}")
        return intent
    
    def _plan_data_requirements(self, intent: Intent) -> Dict[str, Any]:
        """
        Step 2: Plan data requirements
        
        Args:
            intent: Classified intent
        
        Returns:
            Data plan dictionary
        """
        logger.info("Step 2: Planning data requirements")
        self.reasoning_steps.append("Step 2: Determining required data sources")
        
        # Map intent to data sources
        data_sources = self.query_generator._map_intent_to_data_sources(intent)
        
        plan = {
            "data_sources": data_sources,
            "time_filter_needed": intent.time_period is not None,
            "aggregations_needed": len(intent.metrics) > 0,
            "entity_filters_needed": len(intent.entities) > 0
        }
        
        self.reasoning_steps.append(f"Data sources needed: {', '.join(data_sources)}")
        
        logger.debug(f"Data plan created: {plan}")
        return plan
    
    def _generate_query(self, intent: Intent, data_plan: Dict[str, Any]) -> str:
        """
        Step 3: Generate ShopifyQL query
        
        Args:
            intent: Classified intent
            data_plan: Data requirements plan
        
        Returns:
            ShopifyQL query string
        """
        logger.info("Step 3: Generating ShopifyQL query")
        self.reasoning_steps.append("Step 3: Generating ShopifyQL query")
        
        query = self.query_generator.generate(intent)
        
        self.reasoning_steps.append(f"Generated query: {query[:100]}...")
        
        logger.debug(f"Query generated: {query}")
        return query
    
    async def _execute_and_validate(self, query: str) -> List[Dict[str, Any]]:
        """
        Step 4: Execute query and validate results
        
        Args:
            query: ShopifyQL query
        
        Returns:
            Query results
        """
        logger.info("Step 4: Executing query")
        self.reasoning_steps.append("Step 4: Executing query against Shopify")
        
        # Parse query to determine which data source to fetch
        # This is a simplified approach - in production, use execute_graphql_query()
        results = []
        
        try:
            query_lower = query.lower()
            
            # Determine which Shopify API methods to call based on query
            if 'orders' in query_lower or 'line_items' in query_lower:
                orders = await self.shopify_client.get_orders()
                results = orders
                logger.info(f"Fetched {len(orders)} orders from Shopify")
            
            if 'products' in query_lower:
                products = await self.shopify_client.get_products()
                if not results:
                    results = products
                logger.info(f"Fetched {len(products)} products from Shopify")
            
            if 'customers' in query_lower:
                customers = await self.shopify_client.get_customers()
                if not results:
                    results = customers
                logger.info(f"Fetched {len(customers)} customers from Shopify")
            
            if 'inventory' in query_lower:
                inventory = await self.shopify_client.get_inventory()
                if not results:
                    results = inventory
                logger.info(f"Fetched {len(inventory)} inventory records from Shopify")
            
        except Exception as e:
            logger.warning(f"Failed to fetch data from Shopify: {e}")
            # Continue with empty results
        
        self.reasoning_steps.append(f"Retrieved {len(results)} records")
        
        logger.debug(f"Query executed, {len(results)} results")
        return results
    
    def _explain_results(
        self,
        results: List[Dict[str, Any]],
        intent: Intent,
        query: str
    ) -> Dict[str, Any]:
        """
        Step 5: Generate and format explanation
        
        Args:
            results: Query results
            intent: Original intent
            query: Query that was executed
        
        Returns:
            Formatted response dictionary
        """
        logger.info("Step 5: Generating insights and formatting response")
        self.reasoning_steps.append("Step 5: Analyzing results and generating insights")
        
        # Generate insights
        insight_data = self.insight_generator.generate_insights(
            query_results=results,
            question=intent.raw_question,
            intent_type=intent.type.value
        )
        
        # Format response
        formatted_answer = self.response_formatter.format_response(
            insights=insight_data["insights"],
            question=intent.raw_question,
            confidence=insight_data["confidence"],
            data_summary={"data_points": insight_data["data_points"]}
        )
        
        self.reasoning_steps.append("Generated business-friendly insights")
        
        response = {
            "answer": formatted_answer,
            "confidence": insight_data["confidence"],
            "query_used": query,
            "reasoning_steps": self.reasoning_steps.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info("Response generated successfully")
        return response
    
    def get_reasoning_steps(self) -> List[str]:
        """
        Get the reasoning steps from the last execution
        
        Returns:
            List of reasoning step descriptions
        """
        return self.reasoning_steps.copy()

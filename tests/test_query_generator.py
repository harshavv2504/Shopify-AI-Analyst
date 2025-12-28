"""
Tests for ShopifyQL Query Generator
Includes property-based tests using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock

from services.query_generator import ShopifyQLGenerator
from services.openai_service import OpenAIService
from models.intent import Intent, IntentType, TimePeriod


class TestShopifyQLGenerator:
    """Test suite for ShopifyQLGenerator"""
    
    @pytest.fixture
    def mock_openai_service(self):
        """Create a mock OpenAI service"""
        return Mock(spec=OpenAIService)
    
    @pytest.fixture
    def query_generator(self, mock_openai_service):
        """Create a ShopifyQLGenerator instance"""
        return ShopifyQLGenerator(openai_service=mock_openai_service)
    
    # Feature: shopify-ai-analytics, Property 12: Data Source Mapping
    # For any classified intent, the Agent should map it to the appropriate Shopify data sources
    @pytest.mark.parametrize("intent_type,expected_sources", [
        (IntentType.INVENTORY_PROJECTION, ["orders", "products", "inventory_levels"]),
        (IntentType.SALES_TRENDS, ["orders", "products"]),
        (IntentType.CUSTOMER_BEHAVIOR, ["customers", "orders"]),
        (IntentType.PRODUCT_PERFORMANCE, ["products", "orders"]),
        (IntentType.STOCKOUT_PREDICTION, ["products", "inventory_levels", "orders"]),
    ])
    def test_data_source_mapping_property(self, query_generator, intent_type, expected_sources):
        """
        Property test: Each intent type maps to correct data sources
        """
        intent = Intent(
            type=intent_type,
            time_period=None,
            entities=[],
            metrics=[],
            confidence=0.9,
            raw_question="test question"
        )
        
        data_sources = query_generator._map_intent_to_data_sources(intent)
        
        assert data_sources == expected_sources, f"{intent_type} should map to {expected_sources}"
    
    # Feature: shopify-ai-analytics, Property 13: ShopifyQL Syntax Validity
    # For any generated ShopifyQL query, it should be syntactically correct and parseable
    @settings(max_examples=50, deadline=None)
    @given(
        intent_type=st.sampled_from(list(IntentType))
    )
    def test_query_syntax_validity_property(self, query_generator, mock_openai_service, intent_type):
        """
        Property test: All generated queries have valid syntax
        """
        if intent_type == IntentType.UNKNOWN:
            return  # Skip unknown intents
        
        intent = Intent(
            type=intent_type,
            time_period=TimePeriod(description="last week", days=-7),
            entities=["Product X"],
            metrics=["count"],
            confidence=0.9,
            raw_question="test question"
        )
        
        # Mock OpenAI to return a valid query
        mock_query = "SELECT product_title, SUM(quantity) FROM orders WHERE created_at >= '2024-01-01' GROUP BY product_title"
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion = Mock(return_value=mock_query)
        
        query = query_generator.generate(intent)
        
        # Verify query has required components
        assert "SELECT" in query.upper(), "Query must contain SELECT"
        assert "FROM" in query.upper(), "Query must contain FROM"
        
        # Verify no dangerous keywords (using word boundaries to avoid false positives like "CREATED_AT")
        import re
        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        for keyword in dangerous:
            pattern = r'\b' + keyword + r'\b'
            assert not re.search(pattern, query.upper()), f"Query should not contain {keyword} as a standalone keyword"
    
    # Feature: shopify-ai-analytics, Property 14: Time Filter Inclusion
    # For any question that mentions a time period, the generated query should include
    # appropriate time filters matching that period
    @settings(max_examples=50, deadline=None)
    @given(
        days=st.integers(min_value=-365, max_value=365).filter(lambda x: x != 0)
    )
    def test_time_filter_inclusion_property(self, query_generator, days):
        """
        Property test: Time periods are correctly converted to filters
        """
        time_period = TimePeriod(
            description=f"{'last' if days < 0 else 'next'} {abs(days)} days",
            days=days
        )
        
        time_filter = query_generator._build_time_filter(time_period)
        
        if days < 0:
            # Past period should have created_at filter
            assert "created_at" in time_filter.lower(), "Past periods should filter by created_at"
            assert ">=" in time_filter, "Should have start date"
            assert "<=" in time_filter or "AND" in time_filter, "Should have end date"
        else:
            # Future period should have projected_date
            assert "projected_date" in time_filter.lower() or "created_at" in time_filter.lower()
    
    # Feature: shopify-ai-analytics, Property 15: Aggregation Inclusion
    # For any question requesting metrics, the generated query should include
    # the appropriate aggregation functions
    @pytest.mark.parametrize("metrics,expected_in_result", [
        (["count"], "COUNT"),
        (["sum"], "SUM"),
        (["average"], "AVG"),
        (["total"], "SUM"),
        (["max"], "MAX"),
        (["min"], "MIN"),
        (["count", "sum"], "COUNT"),  # Should include at least one
    ])
    def test_aggregation_inclusion_property(self, query_generator, metrics, expected_in_result):
        """
        Property test: Metrics are converted to appropriate aggregations
        """
        aggregations = query_generator._build_aggregations(metrics)
        
        assert expected_in_result in aggregations.upper(), f"Should include {expected_in_result} for {metrics}"
    
    def test_inventory_projection_query_generation(self, query_generator, mock_openai_service):
        """Test query generation for inventory projection"""
        intent = Intent(
            type=IntentType.INVENTORY_PROJECTION,
            time_period=TimePeriod(description="next month", days=30),
            entities=["Product X"],
            metrics=["sum"],
            confidence=0.95,
            raw_question="How many units of Product X will I need next month?"
        )
        
        mock_query = "SELECT product_title, SUM(quantity) FROM orders WHERE product_title = 'Product X' GROUP BY product_title"
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion = Mock(return_value=mock_query)
        
        query = query_generator.generate(intent)
        
        assert "SELECT" in query
        assert "FROM" in query
    
    def test_sales_trends_query_generation(self, query_generator, mock_openai_service):
        """Test query generation for sales trends"""
        intent = Intent(
            type=IntentType.SALES_TRENDS,
            time_period=TimePeriod(description="last week", days=-7),
            entities=[],
            metrics=["count", "sum"],
            confidence=0.92,
            raw_question="What were my top selling products last week?"
        )
        
        mock_query = "SELECT product_title, COUNT(*), SUM(quantity) FROM orders WHERE created_at >= '2024-01-01' GROUP BY product_title ORDER BY SUM(quantity) DESC LIMIT 10"
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion = Mock(return_value=mock_query)
        
        query = query_generator.generate(intent)
        
        assert "SELECT" in query
        assert "FROM" in query
    
    def test_query_validation_rejects_dangerous_keywords(self, query_generator):
        """Test that dangerous SQL keywords are rejected"""
        dangerous_queries = [
            "SELECT * FROM orders; DROP TABLE orders",
            "SELECT * FROM products; DELETE FROM products",
            "SELECT * FROM customers; UPDATE customers SET email = 'hack'",
            "SELECT * FROM orders; INSERT INTO orders VALUES (1, 2, 3)",
        ]
        
        for query in dangerous_queries:
            with pytest.raises(ValueError, match="forbidden keyword"):
                query_generator._validate_query_syntax(query)
    
    def test_query_validation_requires_select(self, query_generator):
        """Test that queries must contain SELECT"""
        with pytest.raises(ValueError, match="SELECT"):
            query_generator._validate_query_syntax("FROM orders")
    
    def test_query_validation_requires_from(self, query_generator):
        """Test that queries must contain FROM"""
        with pytest.raises(ValueError, match="FROM"):
            query_generator._validate_query_syntax("SELECT * WHERE id = 1")
    
    def test_empty_query_rejected(self, query_generator):
        """Test that empty queries are rejected"""
        with pytest.raises(ValueError, match="empty"):
            query_generator._validate_query_syntax("")

"""
Tests for Insight Generator
Includes property-based tests using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock
from datetime import datetime, timedelta

from services.insight_generator import InsightGenerator
from services.openai_service import OpenAIService


class TestInsightGenerator:
    """Test suite for InsightGenerator"""
    
    @pytest.fixture
    def mock_openai_service(self):
        """Create a mock OpenAI service"""
        mock = Mock(spec=OpenAIService)
        mock.create_prompt = Mock(return_value=[])
        mock.chat_completion = Mock(return_value="Based on the data, you should reorder 50 units.")
        return mock
    
    @pytest.fixture
    def insight_generator(self, mock_openai_service):
        """Create an InsightGenerator instance"""
        return InsightGenerator(openai_service=mock_openai_service)
    
    # Feature: shopify-ai-analytics, Property 20: Insight Generation Completeness
    # For any query results, the Agent should generate insights that include
    # an answer, confidence level, and reasoning
    @settings(max_examples=50, deadline=None)
    @given(
        num_results=st.integers(min_value=0, max_value=100)
    )
    def test_insight_generation_completeness_property(self, insight_generator, num_results):
        """
        Property test: All insights include required components
        """
        # Generate mock query results
        query_results = [
            {"product": f"Product {i}", "quantity": i * 10}
            for i in range(num_results)
        ]
        
        result = insight_generator.generate_insights(
            query_results=query_results,
            question="Test question",
            intent_type="sales_trends"
        )
        
        # Verify all required components are present
        assert "insights" in result, "Result must include insights"
        assert "confidence" in result, "Result must include confidence"
        assert "data_points" in result, "Result must include data_points"
        
        # Verify confidence is valid
        assert result["confidence"] in ["low", "medium", "high"], "Confidence must be valid level"
        
        # Verify data points match
        assert result["data_points"] == num_results, "Data points should match input"
    
    # Feature: shopify-ai-analytics, Property 21: Inventory Projection Calculation
    # For inventory projection questions, the Agent should calculate sales velocity
    # and project future needs based on historical data
    @settings(max_examples=50, deadline=None)
    @given(
        total_quantity=st.integers(min_value=10, max_value=1000),  # Avoid edge cases with very small numbers
        days=st.integers(min_value=1, max_value=365)
    )
    def test_inventory_projection_calculation_property(self, insight_generator, total_quantity, days):
        """
        Property test: Sales velocity calculation is correct
        """
        # Create mock orders with evenly distributed quantities
        quantity_per_order = total_quantity / days
        orders = [
            {
                "line_items": [
                    {"quantity": int(quantity_per_order), "title": "Product X"}
                ]
            }
            for _ in range(days)
        ]
        
        velocity = insight_generator.calculate_sales_velocity(orders, days)
        
        # Verify velocity is non-negative
        assert velocity >= 0, "Velocity should be non-negative"
        
        # Verify velocity calculation (allow for rounding errors)
        expected_velocity = total_quantity / days
        assert abs(velocity - expected_velocity) < 1.0, "Velocity calculation should be reasonably accurate"
    
    # Feature: shopify-ai-analytics, Property 23: Insufficient Data Confidence
    # When query results contain fewer than 10 data points, confidence should be "low"
    @pytest.mark.parametrize("num_points,expected_confidence", [
        (0, "low"),
        (5, "low"),
        (9, "low"),
        (10, "medium"),
        (15, "medium"),
        (30, "high"),
        (50, "high"),
    ])
    def test_insufficient_data_confidence_property(self, insight_generator, num_points, expected_confidence):
        """
        Property test: Confidence levels based on data quantity
        """
        query_results = [{"data": i} for i in range(num_points)]
        
        result = insight_generator.generate_insights(
            query_results=query_results,
            question="Test question",
            intent_type="sales_trends"
        )
        
        assert result["confidence"] == expected_confidence, \
            f"With {num_points} points, confidence should be {expected_confidence}"
    
    # Feature: shopify-ai-analytics, Property 24: Sales Trend Analysis
    # For sales trend questions, the Agent should identify top products
    # and calculate their performance metrics
    @settings(max_examples=30, deadline=None)
    @given(
        num_products=st.integers(min_value=1, max_value=20),
        orders_per_product=st.integers(min_value=1, max_value=10)
    )
    def test_sales_trend_analysis_property(self, insight_generator, num_products, orders_per_product):
        """
        Property test: Top products are correctly identified
        """
        # Create mock orders with varying quantities
        orders = []
        for product_id in range(num_products):
            for order_num in range(orders_per_product):
                orders.append({
                    "line_items": [
                        {
                            "title": f"Product {product_id}",
                            "quantity": (product_id + 1) * 10,  # Higher product IDs sell more
                            "price": "10.00"
                        }
                    ]
                })
        
        top_products = insight_generator.identify_top_products(orders, limit=5)
        
        # Verify we get results
        assert len(top_products) > 0, "Should identify at least one top product"
        assert len(top_products) <= 5, "Should not exceed limit"
        
        # Verify products are sorted by revenue (descending)
        if len(top_products) > 1:
            for i in range(len(top_products) - 1):
                assert top_products[i]["revenue"] >= top_products[i + 1]["revenue"], \
                    "Products should be sorted by revenue"
    
    # Feature: shopify-ai-analytics, Property 25: Customer Behavior Analysis
    # For customer behavior questions, the Agent should segment customers
    # by order frequency and provide counts
    @settings(max_examples=30, deadline=None)
    @given(
        one_time=st.integers(min_value=0, max_value=50),
        repeat=st.integers(min_value=0, max_value=50),
        frequent=st.integers(min_value=0, max_value=50)
    )
    def test_customer_behavior_analysis_property(self, insight_generator, one_time, repeat, frequent):
        """
        Property test: Customer segmentation is accurate
        """
        # Create mock customers
        customers = []
        
        # One-time customers (1 order)
        for _ in range(one_time):
            customers.append({"orders_count": 1})
        
        # Repeat customers (2-5 orders)
        for _ in range(repeat):
            customers.append({"orders_count": 3})
        
        # Frequent customers (5+ orders)
        for _ in range(frequent):
            customers.append({"orders_count": 10})
        
        analysis = insight_generator.analyze_order_frequency(customers)
        
        # Verify counts match
        assert analysis["one_time"] == one_time, "One-time count should match"
        assert analysis["repeat"] == repeat, "Repeat count should match"
        assert analysis["frequent"] == frequent, "Frequent count should match"
        assert analysis["total"] == one_time + repeat + frequent, "Total should match sum"
    
    def test_sales_velocity_with_empty_orders(self, insight_generator):
        """Test sales velocity with no orders"""
        velocity = insight_generator.calculate_sales_velocity([], 30)
        assert velocity == 0.0, "Empty orders should have zero velocity"
    
    def test_sales_velocity_with_zero_days(self, insight_generator):
        """Test sales velocity with zero days"""
        orders = [{"line_items": [{"quantity": 10}]}]
        velocity = insight_generator.calculate_sales_velocity(orders, 0)
        assert velocity == 0.0, "Zero days should return zero velocity"
    
    def test_top_products_with_empty_orders(self, insight_generator):
        """Test top products with no orders"""
        top_products = insight_generator.identify_top_products([])
        assert len(top_products) == 0, "Empty orders should return no products"
    
    def test_order_frequency_with_empty_customers(self, insight_generator):
        """Test order frequency with no customers"""
        analysis = insight_generator.analyze_order_frequency([])
        assert analysis["one_time"] == 0
        assert analysis["repeat"] == 0
        assert analysis["frequent"] == 0
        assert analysis["total"] == 0
    
    def test_confidence_determination_thresholds(self, insight_generator):
        """Test confidence level thresholds"""
        # Low confidence: < 10 data points
        assert insight_generator._determine_confidence([]) == "low"
        assert insight_generator._determine_confidence([{}] * 5) == "low"
        
        # Medium confidence: 10-29 data points
        assert insight_generator._determine_confidence([{}] * 10) == "medium"
        assert insight_generator._determine_confidence([{}] * 29) == "medium"
        
        # High confidence: 30+ data points
        assert insight_generator._determine_confidence([{}] * 30) == "high"
        assert insight_generator._determine_confidence([{}] * 100) == "high"
    
    def test_insight_generation_with_llm(self, insight_generator, mock_openai_service):
        """Test insight generation uses LLM correctly"""
        query_results = [{"product": "Widget", "quantity": 100}]
        
        result = insight_generator.generate_insights(
            query_results=query_results,
            question="What are my top products?",
            intent_type="product_performance"
        )
        
        # Verify LLM was called
        assert mock_openai_service.create_prompt.called
        assert mock_openai_service.chat_completion.called
        
        # Verify result structure
        assert isinstance(result["insights"], str)
        assert len(result["insights"]) > 0

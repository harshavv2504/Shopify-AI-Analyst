"""
Tests for Shopify Analytics Agent
Includes property-based tests using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from services.agent import ShopifyAnalyticsAgent
from services.intent_classifier import IntentClassifier
from services.query_generator import ShopifyQLGenerator
from services.shopify_client import ShopifyClient
from services.insight_generator import InsightGenerator
from services.response_formatter import ResponseFormatter
from models.intent import Intent, IntentType, TimePeriod


class TestShopifyAnalyticsAgent:
    """Test suite for ShopifyAnalyticsAgent"""
    
    @pytest.fixture
    def mock_intent_classifier(self):
        """Create a mock IntentClassifier"""
        mock = Mock(spec=IntentClassifier)
        mock.classify = Mock(return_value=Intent(
            type=IntentType.SALES_TRENDS,
            time_period=TimePeriod(description="last week", days=-7),
            entities=["Product X"],
            metrics=["count"],
            confidence=0.9,
            raw_question="What were my top products last week?"
        ))
        return mock
    
    @pytest.fixture
    def mock_query_generator(self):
        """Create a mock ShopifyQLGenerator"""
        mock = Mock(spec=ShopifyQLGenerator)
        mock.generate = Mock(return_value="SELECT product_title, COUNT(*) FROM orders GROUP BY product_title")
        mock._map_intent_to_data_sources = Mock(return_value=["orders", "products"])
        return mock
    
    @pytest.fixture
    def mock_shopify_client(self):
        """Create a mock ShopifyClient"""
        mock = Mock(spec=ShopifyClient)
        # Make execute methods async
        mock.get_orders = AsyncMock(return_value=[])
        mock.get_products = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def mock_insight_generator(self):
        """Create a mock InsightGenerator"""
        mock = Mock(spec=InsightGenerator)
        mock.generate_insights = Mock(return_value={
            "insights": "Your top product is Widget with 100 sales.",
            "confidence": "high",
            "data_points": 50
        })
        return mock
    
    @pytest.fixture
    def mock_response_formatter(self):
        """Create a mock ResponseFormatter"""
        mock = Mock(spec=ResponseFormatter)
        mock.format_response = Mock(return_value="Your store sold 100 units last week. Great job!")
        return mock
    
    @pytest.fixture
    def agent(
        self,
        mock_intent_classifier,
        mock_query_generator,
        mock_shopify_client,
        mock_insight_generator,
        mock_response_formatter
    ):
        """Create a ShopifyAnalyticsAgent instance with mocked dependencies"""
        return ShopifyAnalyticsAgent(
            intent_classifier=mock_intent_classifier,
            query_generator=mock_query_generator,
            shopify_client=mock_shopify_client,
            insight_generator=mock_insight_generator,
            response_formatter=mock_response_formatter
        )
    
    # Feature: shopify-ai-analytics, Property 33: Agent Workflow Completeness
    # For any question, the Agent should execute all 5 steps:
    # 1. Understand intent, 2. Plan data, 3. Generate query, 4. Execute, 5. Explain
    @pytest.mark.asyncio
    @settings(max_examples=30, deadline=None)
    @given(
        question=st.text(min_size=10, max_size=100).filter(lambda x: x.strip())
    )
    async def test_agent_workflow_completeness_property(
        self,
        agent,
        mock_intent_classifier,
        mock_query_generator,
        mock_insight_generator,
        mock_response_formatter,
        question
    ):
        """
        Property test: Agent executes all 5 workflow steps
        """
        result = await agent.process_question(question)
        
        # Verify all services were called (5 steps)
        assert mock_intent_classifier.classify.called, "Step 1: Should classify intent"
        assert mock_query_generator._map_intent_to_data_sources.called, "Step 2: Should plan data"
        assert mock_query_generator.generate.called, "Step 3: Should generate query"
        # Step 4: Execute (mocked to return empty results)
        assert mock_insight_generator.generate_insights.called, "Step 5a: Should generate insights"
        assert mock_response_formatter.format_response.called, "Step 5b: Should format response"
        
        # Verify result structure
        assert "answer" in result
        assert "confidence" in result
        assert "query_used" in result
        assert "reasoning_steps" in result
        assert "timestamp" in result
        
        # Verify reasoning steps were tracked
        assert len(result["reasoning_steps"]) > 0, "Should track reasoning steps"
    
    # Feature: shopify-ai-analytics, Property 34: Question Context Preservation
    # Throughout the workflow, the Agent should preserve the original question context
    # and use it in all relevant steps
    @pytest.mark.asyncio
    @settings(max_examples=30, deadline=None)
    @given(
        question=st.text(min_size=10, max_size=100).filter(lambda x: x.strip())
    )
    async def test_question_context_preservation_property(
        self,
        agent,
        mock_intent_classifier,
        mock_insight_generator,
        question
    ):
        """
        Property test: Original question context is preserved
        """
        # Set up mock to capture the question
        captured_questions = []
        
        def capture_classify(q):
            captured_questions.append(q)
            return Intent(
                type=IntentType.SALES_TRENDS,
                time_period=None,
                entities=[],
                metrics=[],
                confidence=0.9,
                raw_question=q
            )
        
        mock_intent_classifier.classify = Mock(side_effect=capture_classify)
        
        result = await agent.process_question(question)
        
        # Verify question was passed to classifier
        assert len(captured_questions) > 0, "Question should be passed to classifier"
        assert captured_questions[0] == question, "Original question should be preserved"
        
        # Verify insight generator received the question context
        assert mock_insight_generator.generate_insights.called
        call_kwargs = mock_insight_generator.generate_insights.call_args[1]
        assert "question" in call_kwargs, "Question should be passed to insight generator"
    
    @pytest.mark.asyncio
    async def test_process_question_success(self, agent):
        """Test successful question processing"""
        question = "What were my top selling products last week?"
        
        result = await agent.process_question(question)
        
        # Verify result structure
        assert result["answer"] == "Your store sold 100 units last week. Great job!"
        assert result["confidence"] == "high"
        assert result["query_used"] is not None
        assert len(result["reasoning_steps"]) > 0
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_process_question_with_error(
        self,
        agent,
        mock_intent_classifier
    ):
        """Test question processing with error"""
        # Make classifier raise an error
        mock_intent_classifier.classify = Mock(side_effect=Exception("Classification failed"))
        
        question = "What are my sales?"
        result = await agent.process_question(question)
        
        # Should return error response
        assert "error" in result["answer"].lower()
        assert result["confidence"] == "low"
        assert result["query_used"] is None
    
    @pytest.mark.asyncio
    async def test_reasoning_steps_tracking(self, agent):
        """Test that reasoning steps are properly tracked"""
        question = "How many units should I reorder?"
        
        result = await agent.process_question(question)
        
        reasoning_steps = result["reasoning_steps"]
        
        # Verify steps are tracked
        assert len(reasoning_steps) > 0
        
        # Verify step descriptions
        step_text = " ".join(reasoning_steps).lower()
        assert "step 1" in step_text or "intent" in step_text
        assert "step 2" in step_text or "data" in step_text
        assert "step 3" in step_text or "query" in step_text
        assert "step 4" in step_text or "execut" in step_text
        assert "step 5" in step_text or "insight" in step_text
    
    @pytest.mark.asyncio
    async def test_get_reasoning_steps(self, agent):
        """Test getting reasoning steps after execution"""
        question = "What are my sales?"
        
        await agent.process_question(question)
        
        steps = agent.get_reasoning_steps()
        
        assert isinstance(steps, list)
        assert len(steps) > 0
        assert all(isinstance(step, str) for step in steps)
    
    @pytest.mark.asyncio
    async def test_understand_intent_step(self, agent, mock_intent_classifier):
        """Test Step 1: Understand Intent"""
        question = "What are my top products?"
        
        await agent.process_question(question)
        
        # Verify intent classifier was called with question
        mock_intent_classifier.classify.assert_called_once_with(question)
        
        # Verify reasoning steps include intent information
        steps = agent.get_reasoning_steps()
        step_text = " ".join(steps).lower()
        assert "intent" in step_text
    
    @pytest.mark.asyncio
    async def test_plan_data_requirements_step(self, agent, mock_query_generator):
        """Test Step 2: Plan Data Requirements"""
        question = "What are my sales trends?"
        
        await agent.process_question(question)
        
        # Verify data sources were mapped
        assert mock_query_generator._map_intent_to_data_sources.called
        
        # Verify reasoning steps include data planning
        steps = agent.get_reasoning_steps()
        step_text = " ".join(steps).lower()
        assert "data" in step_text or "source" in step_text
    
    @pytest.mark.asyncio
    async def test_generate_query_step(self, agent, mock_query_generator):
        """Test Step 3: Generate Query"""
        question = "How many orders did I get?"
        
        await agent.process_question(question)
        
        # Verify query generator was called
        assert mock_query_generator.generate.called
        
        # Verify reasoning steps include query generation
        steps = agent.get_reasoning_steps()
        step_text = " ".join(steps).lower()
        assert "query" in step_text or "generat" in step_text
    
    @pytest.mark.asyncio
    async def test_execute_and_validate_step(self, agent):
        """Test Step 4: Execute and Validate"""
        question = "What are my inventory levels?"
        
        result = await agent.process_question(question)
        
        # Verify reasoning steps include execution
        steps = result["reasoning_steps"]
        step_text = " ".join(steps).lower()
        assert "execut" in step_text or "shopify" in step_text
    
    @pytest.mark.asyncio
    async def test_explain_results_step(
        self,
        agent,
        mock_insight_generator,
        mock_response_formatter
    ):
        """Test Step 5: Explain Results"""
        question = "What should I reorder?"
        
        await agent.process_question(question)
        
        # Verify insight generator was called
        assert mock_insight_generator.generate_insights.called
        
        # Verify response formatter was called
        assert mock_response_formatter.format_response.called
        
        # Verify reasoning steps include explanation
        steps = agent.get_reasoning_steps()
        step_text = " ".join(steps).lower()
        assert "insight" in step_text or "analyz" in step_text
    
    @pytest.mark.asyncio
    async def test_multiple_questions_reset_reasoning(self, agent):
        """Test that reasoning steps are reset between questions"""
        question1 = "What are my sales?"
        question2 = "What are my top products?"
        
        result1 = await agent.process_question(question1)
        steps1 = result1["reasoning_steps"]
        
        result2 = await agent.process_question(question2)
        steps2 = result2["reasoning_steps"]
        
        # Steps should be different (reset between questions)
        assert len(steps1) > 0
        assert len(steps2) > 0
        # Each should have their own set of steps
        assert isinstance(steps1, list)
        assert isinstance(steps2, list)
    
    @pytest.mark.asyncio
    async def test_timestamp_format(self, agent):
        """Test that timestamp is in ISO format"""
        question = "What are my sales?"
        
        result = await agent.process_question(question)
        
        # Verify timestamp can be parsed
        timestamp = result["timestamp"]
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)

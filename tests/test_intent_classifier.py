"""
Tests for Intent Classifier
Includes property-based tests using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch

from services.intent_classifier import IntentClassifier
from services.openai_service import OpenAIService
from models.intent import Intent, IntentType, TimePeriod


class TestIntentClassifier:
    """Test suite for IntentClassifier"""
    
    @pytest.fixture
    def mock_openai_service(self):
        """Create a mock OpenAI service"""
        return Mock(spec=OpenAIService)
    
    @pytest.fixture
    def intent_classifier(self, mock_openai_service):
        """Create an IntentClassifier instance with mocked OpenAI service"""
        return IntentClassifier(openai_service=mock_openai_service)
    
    # Feature: shopify-ai-analytics, Property 10: Question Parsing Completeness
    # For any natural language question, the Agent should extract all relevant components:
    # intent type, time period (if mentioned), entities (products/customers), and metrics requested
    @pytest.mark.parametrize("question,expected_intent,expected_has_time,expected_has_entities,expected_has_metrics", [
        ("What were my top 5 selling products last week?", IntentType.SALES_TRENDS, True, False, True),
        ("How many units of Product X will I need next month?", IntentType.INVENTORY_PROJECTION, True, True, True),
        ("Which customers placed repeat orders in the last 90 days?", IntentType.CUSTOMER_BEHAVIOR, True, True, True),
        ("Which products are likely to go out of stock in 7 days?", IntentType.STOCKOUT_PREDICTION, True, False, False),
        ("Show me product performance", IntentType.PRODUCT_PERFORMANCE, False, False, False),
    ])
    def test_question_parsing_completeness(
        self, 
        intent_classifier, 
        mock_openai_service,
        question,
        expected_intent,
        expected_has_time,
        expected_has_entities,
        expected_has_metrics
    ):
        """
        Property test: All questions are parsed to extract complete information
        """
        # Mock OpenAI response
        mock_response = {
            "intent_type": expected_intent.value,
            "time_period": {
                "description": "last week" if expected_has_time else None,
                "days": -7 if expected_has_time else None
            } if expected_has_time else None,
            "entities": ["Product X"] if expected_has_entities else [],
            "metrics": ["count", "sum"] if expected_has_metrics else [],
            "confidence": 0.9
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[
            {"role": "system", "content": "test"},
            {"role": "user", "content": question}
        ])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        # Classify question
        intent = intent_classifier.classify(question)
        
        # Verify all components are extracted
        assert intent.type == expected_intent, "Intent type should be extracted"
        assert intent.raw_question == question, "Original question should be preserved"
        assert intent.confidence > 0, "Confidence should be present"
        
        if expected_has_time:
            assert intent.time_period is not None, "Time period should be extracted"
            assert intent.time_period.description is not None
        
        if expected_has_entities:
            assert len(intent.entities) > 0, "Entities should be extracted"
        
        if expected_has_metrics:
            assert len(intent.metrics) > 0, "Metrics should be extracted"
    
    @settings(max_examples=50, deadline=None)
    @given(
        question=st.text(min_size=10, max_size=200),
        confidence=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_all_questions_return_valid_intent(self, intent_classifier, mock_openai_service, question, confidence):
        """
        Property test: Any question returns a valid Intent object with all required fields
        """
        # Mock OpenAI response
        mock_response = {
            "intent_type": "sales_trends",
            "time_period": {"description": "last week", "days": -7},
            "entities": ["test"],
            "metrics": ["count"],
            "confidence": confidence
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        # Classify question
        intent = intent_classifier.classify(question)
        
        # Verify intent structure
        assert isinstance(intent, Intent), "Should return Intent object"
        assert isinstance(intent.type, IntentType), "Should have valid intent type"
        assert intent.raw_question == question, "Should preserve original question"
        assert 0.0 <= intent.confidence <= 1.0, "Confidence should be between 0 and 1"
        assert isinstance(intent.entities, list), "Entities should be a list"
        assert isinstance(intent.metrics, list), "Metrics should be a list"
    
    def test_inventory_projection_question(self, intent_classifier, mock_openai_service):
        """Test inventory projection question parsing"""
        question = "How much inventory should I reorder for next week?"
        
        mock_response = {
            "intent_type": "inventory_projection",
            "time_period": {"description": "next week", "days": 7},
            "entities": [],
            "metrics": ["sum"],
            "confidence": 0.95
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        assert intent.type == IntentType.INVENTORY_PROJECTION
        assert intent.time_period is not None
        assert intent.time_period.days == 7
        assert intent.confidence == 0.95
    
    def test_sales_trends_question(self, intent_classifier, mock_openai_service):
        """Test sales trends question parsing"""
        question = "What were my top 5 selling products last month?"
        
        mock_response = {
            "intent_type": "sales_trends",
            "time_period": {"description": "last month", "days": -30},
            "entities": [],
            "metrics": ["count", "sum"],
            "confidence": 0.92
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        assert intent.type == IntentType.SALES_TRENDS
        assert intent.time_period.days == -30
        assert "count" in intent.metrics
    
    def test_customer_behavior_question(self, intent_classifier, mock_openai_service):
        """Test customer behavior question parsing"""
        question = "Which customers placed repeat orders?"
        
        mock_response = {
            "intent_type": "customer_behavior",
            "time_period": None,
            "entities": ["repeat customers"],
            "metrics": ["count"],
            "confidence": 0.88
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        assert intent.type == IntentType.CUSTOMER_BEHAVIOR
        assert "repeat customers" in intent.entities


    # Feature: shopify-ai-analytics, Property 11: Ambiguity Confidence Calibration
    # For any ambiguous question where the Agent makes assumptions, the confidence level
    # in the response should be "low" or "medium", never "high"
    @settings(max_examples=50, deadline=None)
    @given(
        confidence=st.floats(min_value=0.0, max_value=0.69)  # Below 0.7 threshold
    )
    def test_low_confidence_indicates_ambiguity(self, intent_classifier, mock_openai_service, confidence):
        """
        Property test: Low confidence scores correctly indicate ambiguous questions
        """
        question = "Tell me about my store"
        
        mock_response = {
            "intent_type": "unknown",
            "time_period": None,
            "entities": [],
            "metrics": [],
            "confidence": confidence
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        # Verify low confidence is preserved
        assert intent.confidence < 0.7, "Ambiguous questions should have confidence < 0.7"
        assert intent.is_ambiguous(), "Should be marked as ambiguous"
    
    @settings(max_examples=50, deadline=None)
    @given(
        confidence=st.floats(min_value=0.7, max_value=1.0)  # Above threshold
    )
    def test_high_confidence_indicates_clarity(self, intent_classifier, mock_openai_service, confidence):
        """
        Property test: High confidence scores indicate clear questions
        """
        question = "What were my top 5 selling products last week?"
        
        mock_response = {
            "intent_type": "sales_trends",
            "time_period": {"description": "last week", "days": -7},
            "entities": [],
            "metrics": ["count"],
            "confidence": confidence
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        # Verify high confidence is preserved
        assert intent.confidence >= 0.7, "Clear questions should have confidence >= 0.7"
        assert not intent.is_ambiguous(), "Should not be marked as ambiguous"
    
    def test_ambiguous_question_low_confidence(self, intent_classifier, mock_openai_service):
        """Test that ambiguous questions get low confidence"""
        question = "Show me stuff"
        
        mock_response = {
            "intent_type": "unknown",
            "time_period": None,
            "entities": [],
            "metrics": [],
            "confidence": 0.3
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        assert intent.confidence < 0.7
        assert intent.is_ambiguous()
        assert intent.type == IntentType.UNKNOWN
    
    def test_clear_question_high_confidence(self, intent_classifier, mock_openai_service):
        """Test that clear questions get high confidence"""
        question = "How many units of Product X did I sell in the last 30 days?"
        
        mock_response = {
            "intent_type": "sales_trends",
            "time_period": {"description": "last 30 days", "days": -30},
            "entities": ["Product X"],
            "metrics": ["count", "sum"],
            "confidence": 0.95
        }
        
        mock_openai_service.create_prompt = Mock(return_value=[])
        mock_openai_service.chat_completion_json = Mock(return_value=mock_response)
        
        intent = intent_classifier.classify(question)
        
        assert intent.confidence >= 0.7
        assert not intent.is_ambiguous()

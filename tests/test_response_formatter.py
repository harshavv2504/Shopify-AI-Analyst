"""
Tests for Response Formatter
Includes property-based tests using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock

from services.response_formatter import ResponseFormatter
from services.openai_service import OpenAIService


class TestResponseFormatter:
    """Test suite for ResponseFormatter"""
    
    @pytest.fixture
    def mock_openai_service(self):
        """Create a mock OpenAI service"""
        mock = Mock(spec=OpenAIService)
        mock.create_prompt = Mock(return_value=[])
        mock.chat_completion = Mock(return_value="Your store sold 100 units last week. This is great performance!")
        return mock
    
    @pytest.fixture
    def response_formatter(self, mock_openai_service):
        """Create a ResponseFormatter instance"""
        return ResponseFormatter(openai_service=mock_openai_service)
    
    # Feature: shopify-ai-analytics, Property 27: Business Language Formatting
    # For any technical insights, the formatted response should not contain
    # technical jargon (API, SQL, JSON, etc.)
    @settings(max_examples=50, deadline=None)
    @given(
        jargon_term=st.sampled_from([
            "API", "query", "database", "SQL", "JSON",
            "HTTP", "endpoint", "parameter", "aggregation", "schema"
        ])
    )
    def test_business_language_formatting_property(self, response_formatter, jargon_term):
        """
        Property test: Technical jargon is detected and removed
        """
        # Test jargon detection
        text_with_jargon = f"The {jargon_term} returned 100 results"
        assert response_formatter._contains_technical_jargon(text_with_jargon), \
            f"Should detect {jargon_term} as jargon"
        
        # Test jargon removal
        cleaned = response_formatter._remove_jargon(text_with_jargon)
        assert jargon_term not in cleaned, f"Should remove {jargon_term}"
    
    # Feature: shopify-ai-analytics, Property 28: Numerical Context Inclusion
    # For any response containing numbers, the formatter should add context
    # explaining what those numbers represent
    @settings(max_examples=30, deadline=None)
    @given(
        data_points=st.integers(min_value=1, max_value=1000)
    )
    def test_numerical_context_inclusion_property(self, response_formatter, data_points):
        """
        Property test: Numerical context is added to responses
        """
        text = "Your sales are trending upward."
        data_summary = {"data_points": data_points}
        
        result = response_formatter._add_numerical_context(text, data_summary)
        
        # Verify context was added
        assert "based on" in result.lower() or str(data_points) in result, \
            "Should add context about data points"
    
    # Feature: shopify-ai-analytics, Property 30: Response Structure Clarity
    # For any formatted response, it should have clear structure with
    # answer, context, and recommendations when appropriate
    @settings(max_examples=30, deadline=None)
    @given(
        confidence=st.sampled_from(["low", "medium", "high"])
    )
    def test_response_structure_clarity_property(self, response_formatter, confidence):
        """
        Property test: Responses are properly structured
        """
        text = "Your sales are good."
        
        structured = response_formatter._structure_response(text, confidence)
        
        # Verify structure
        assert isinstance(structured, str), "Should return string"
        assert len(structured) > 0, "Should not be empty"
        
        # Low/medium confidence should include note
        if confidence in ["low", "medium"]:
            assert "confidence" in structured.lower() or "limited data" in structured.lower(), \
                f"{confidence} confidence should include a note"
    
    def test_format_response_complete_workflow(self, response_formatter, mock_openai_service):
        """Test complete formatting workflow"""
        insights = "The API query returned 100 results from the database."
        question = "What are my sales?"
        confidence = "high"
        data_summary = {"data_points": 50}
        
        result = response_formatter.format_response(
            insights=insights,
            question=question,
            confidence=confidence,
            data_summary=data_summary
        )
        
        # Verify LLM was called
        assert mock_openai_service.create_prompt.called
        assert mock_openai_service.chat_completion.called
        
        # Verify result is formatted
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_reorder_recommendation_generation(self, response_formatter):
        """Test reorder recommendation generation"""
        velocity = 10.5  # units per day
        days = 30
        current_stock = 50
        
        recommendation = response_formatter.generate_reorder_recommendation(
            velocity=velocity,
            days=days,
            current_stock=current_stock
        )
        
        # Verify recommendation includes key information
        assert str(velocity) in recommendation or "10.5" in recommendation
        assert str(days) in recommendation
        assert "units" in recommendation.lower()
        assert "reorder" in recommendation.lower() or "order" in recommendation.lower()
    
    def test_reorder_recommendation_no_stock(self, response_formatter):
        """Test reorder recommendation with no current stock"""
        velocity = 5.0
        days = 14
        
        recommendation = response_formatter.generate_reorder_recommendation(
            velocity=velocity,
            days=days,
            current_stock=0
        )
        
        # Should recommend ordering projected amount
        projected = velocity * days
        assert "order" in recommendation.lower()
        assert str(int(projected)) in recommendation or str(projected) in recommendation
    
    def test_customer_analysis_formatting(self, response_formatter):
        """Test customer analysis formatting"""
        one_time = 50
        repeat = 30
        frequent = 20
        total = 100
        
        analysis = response_formatter.format_customer_analysis(
            one_time=one_time,
            repeat=repeat,
            frequent=frequent,
            total=total
        )
        
        # Verify all segments are included
        assert "one-time" in analysis.lower()
        assert "repeat" in analysis.lower()
        assert "frequent" in analysis.lower()
        
        # Verify counts are present
        assert str(one_time) in analysis
        assert str(repeat) in analysis
        assert str(frequent) in analysis
        assert str(total) in analysis
        
        # Verify percentages are included
        assert "%" in analysis
    
    def test_customer_analysis_with_zero_customers(self, response_formatter):
        """Test customer analysis with no customers"""
        analysis = response_formatter.format_customer_analysis(
            one_time=0,
            repeat=0,
            frequent=0,
            total=0
        )
        
        assert "no customer data" in analysis.lower()
    
    def test_customer_analysis_recommendations(self, response_formatter):
        """Test that customer analysis includes recommendations"""
        # High one-time percentage should suggest loyalty program
        analysis = response_formatter.format_customer_analysis(
            one_time=70,
            repeat=20,
            frequent=10,
            total=100
        )
        assert "loyalty" in analysis.lower() or "convert" in analysis.lower()
        
        # High frequent percentage should suggest retention
        analysis = response_formatter.format_customer_analysis(
            one_time=20,
            repeat=30,
            frequent=50,
            total=100
        )
        assert "retention" in analysis.lower() or "loyal" in analysis.lower()
    
    def test_methodology_explanation(self, response_formatter):
        """Test methodology explanations"""
        # Sales velocity explanation
        explanation = response_formatter.explain_methodology(
            "sales_velocity",
            {"total_units": 300, "days": 30}
        )
        assert "average" in explanation.lower() or "daily" in explanation.lower()
        assert "300" in explanation
        assert "30" in explanation
        
        # Projection explanation
        explanation = response_formatter.explain_methodology(
            "projection",
            {}
        )
        assert "project" in explanation.lower() or "future" in explanation.lower()
        
        # Unknown method should return default
        explanation = response_formatter.explain_methodology(
            "unknown_method",
            {}
        )
        assert "historical data" in explanation.lower()
    
    def test_jargon_detection_case_insensitive(self, response_formatter):
        """Test that jargon detection is case-insensitive"""
        assert response_formatter._contains_technical_jargon("The API is working")
        assert response_formatter._contains_technical_jargon("The api is working")
        assert response_formatter._contains_technical_jargon("The Api is working")
    
    def test_jargon_removal_preserves_meaning(self, response_formatter):
        """Test that jargon removal preserves sentence meaning"""
        original = "The API query returned data from the database"
        cleaned = response_formatter._remove_jargon(original)
        
        # Should still be readable
        assert len(cleaned) > 0
        assert "returned" in cleaned
        assert "from" in cleaned
    
    def test_numerical_context_not_duplicated(self, response_formatter):
        """Test that numerical context is not added if already present"""
        text = "Based on analysis of 50 orders, your sales are good."
        data_summary = {"data_points": 50}
        
        result = response_formatter._add_numerical_context(text, data_summary)
        
        # Should not duplicate "based on"
        assert result.lower().count("based on") == 1
    
    def test_confidence_note_for_low_confidence(self, response_formatter):
        """Test that low confidence includes a note"""
        text = "Your sales are trending upward."
        
        result = response_formatter._structure_response(text, "low")
        
        assert "low confidence" in result.lower() or "limited data" in result.lower()
    
    def test_confidence_note_for_medium_confidence(self, response_formatter):
        """Test that medium confidence includes a note"""
        text = "Your sales are trending upward."
        
        result = response_formatter._structure_response(text, "medium")
        
        assert "medium confidence" in result.lower() or "limited data" in result.lower()
    
    def test_high_confidence_no_extra_note(self, response_formatter):
        """Test that high confidence doesn't add unnecessary notes"""
        text = "Your sales are trending upward."
        
        result = response_formatter._structure_response(text, "high")
        
        # Should not add confidence warning for high confidence
        # (unless already in text)
        if "confidence" not in text.lower():
            assert result == text

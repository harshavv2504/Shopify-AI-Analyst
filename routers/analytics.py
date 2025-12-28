"""
Analytics router for processing natural language questions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from models.database import get_db
from models.store import Store
from models.schemas import QuestionRequest, AnalyticsResponse, ErrorResponse
from services.openai_service import OpenAIService
from services.intent_classifier import IntentClassifier
from services.query_generator import ShopifyQLGenerator
from services.shopify_client import ShopifyClient
from services.insight_generator import InsightGenerator
from services.response_formatter import ResponseFormatter
from services.agent import ShopifyAnalyticsAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analytics"])


def create_agent(store: Store) -> ShopifyAnalyticsAgent:
    """
    Factory function to create ShopifyAnalyticsAgent with all dependencies
    
    Args:
        store: Store model with credentials
    
    Returns:
        Configured ShopifyAnalyticsAgent instance
    """
    # Initialize OpenAI service
    openai_service = OpenAIService()
    
    # Initialize all services with dependency injection
    intent_classifier = IntentClassifier(openai_service=openai_service)
    query_generator = ShopifyQLGenerator(openai_service=openai_service)
    shopify_client = ShopifyClient(
        shop_domain=store.shop_domain,
        access_token=store.access_token
    )
    insight_generator = InsightGenerator(openai_service=openai_service)
    response_formatter = ResponseFormatter(openai_service=openai_service)
    
    # Create and return agent
    agent = ShopifyAnalyticsAgent(
        intent_classifier=intent_classifier,
        query_generator=query_generator,
        shopify_client=shopify_client,
        insight_generator=insight_generator,
        response_formatter=response_formatter
    )
    
    return agent


@router.post("/questions", response_model=AnalyticsResponse)
async def process_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Process a natural language analytics question
    
    This endpoint:
    1. Validates the request
    2. Retrieves store credentials
    3. Processes the question through the AI agent
    4. Returns business-friendly insights
    """
    try:
        # Retrieve store credentials
        store = db.query(Store).filter(
            Store.shop_domain == request.store_id
        ).first()
        
        if not store:
            raise HTTPException(
                status_code=404,
                detail="Store not found. Please authenticate first at /api/v1/auth/shopify"
            )
        
        # Create agent with all dependencies
        agent = create_agent(store)
        
        # Process question through agent
        logger.info(f"Processing question for store {request.store_id}: {request.question}")
        response = await agent.process_question(request.question)
        
        # Return formatted response
        return AnalyticsResponse(
            answer=response["answer"],
            confidence=response["confidence"],
            query_used=response.get("query_used"),
            reasoning_steps=response.get("reasoning_steps"),
            timestamp=response["timestamp"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your question"
        )

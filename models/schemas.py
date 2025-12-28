"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

class QuestionRequest(BaseModel):
    """Request schema for analytics questions"""
    store_id: str = Field(..., description="Shopify store domain")
    question: str = Field(..., description="Natural language question")
    
    @field_validator('store_id')
    @classmethod
    def validate_store_id(cls, v):
        """Validate store_id format"""
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$'
        if not re.match(pattern, v):
            raise ValueError('Invalid store_id format. Must be a valid Shopify domain (e.g., store-name.myshopify.com)')
        return v
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        """Validate question is not empty"""
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

class AnalyticsResponse(BaseModel):
    """Response schema for analytics answers"""
    answer: str
    confidence: str
    query_used: Optional[str] = None
    reasoning_steps: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OAuthInitiateResponse(BaseModel):
    """OAuth initiation response"""
    authorization_url: str

class OAuthCallbackResponse(BaseModel):
    """OAuth callback success response"""
    message: str
    shop_domain: str
    scope: Optional[str] = None

"""
Authentication router for Shopify OAuth
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import os
import secrets
import httpx
import logging

from models.database import get_db
from models.store import Store
from models.schemas import OAuthInitiateResponse, OAuthCallbackResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.get("/shopify", response_model=OAuthInitiateResponse)
async def initiate_oauth(
    shop: str = Query(..., description="Shopify store domain"),
    request: Request = None
):
    """
    Initiate Shopify OAuth flow
    
    Redirects user to Shopify authorization page
    """
    try:
        # Normalize shop domain
        shop_domain = Store.normalize_shop_domain(shop)
        
        # Get configuration
        api_key = os.getenv("SHOPIFY_API_KEY")
        scopes = os.getenv("SHOPIFY_SCOPES", "read_products,read_orders,read_customers,read_inventory")
        
        if not api_key:
            raise HTTPException(status_code=500, detail="Shopify API key not configured")
        
        # Build redirect URI
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/api/v1/auth/shopify/callback"
        
        # Generate state for CSRF protection
        state = secrets.token_hex(16)
        
        # Build authorization URL
        params = {
            "client_id": api_key,
            "scope": scopes,
            "redirect_uri": redirect_uri,
            "state": state
        }
        
        auth_url = f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"
        
        logger.info(f"Initiating OAuth for shop: {shop_domain}")
        
        # Return redirect response
        return RedirectResponse(url=auth_url)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")

@router.get("/shopify/callback", response_model=OAuthCallbackResponse)
async def oauth_callback(
    shop: str = Query(..., description="Shopify store domain"),
    code: str = Query(..., description="Authorization code"),
    hmac: str = Query(..., description="HMAC signature"),
    state: str = Query(None, description="State parameter"),
    db: Session = Depends(get_db)
):
    """
    Handle Shopify OAuth callback
    
    Exchanges authorization code for access token and stores credentials
    """
    try:
        # Normalize shop domain
        shop_domain = Store.normalize_shop_domain(shop)
        
        # Get configuration
        api_key = os.getenv("SHOPIFY_API_KEY")
        api_secret = os.getenv("SHOPIFY_API_SECRET")
        
        if not api_key or not api_secret:
            raise HTTPException(status_code=500, detail="Shopify credentials not configured")
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{shop_domain}/admin/oauth/access_token",
                json={
                    "client_id": api_key,
                    "client_secret": api_secret,
                    "code": code
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            scope = token_data.get("scope")
        
        # Store credentials in database
        store = db.query(Store).filter(Store.shop_domain == shop_domain).first()
        
        if store:
            # Update existing store
            store.access_token = access_token
            store.scope = scope
        else:
            # Create new store
            store = Store(
                shop_domain=shop_domain,
                scope=scope
            )
            store.access_token = access_token
            db.add(store)
        
        db.commit()
        db.refresh(store)
        
        logger.info(f"Successfully authenticated shop: {shop_domain}")
        
        return OAuthCallbackResponse(
            message="Authentication successful",
            shop_domain=shop_domain,
            scope=scope
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to complete OAuth flow")

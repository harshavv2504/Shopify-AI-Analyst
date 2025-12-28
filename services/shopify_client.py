"""
Shopify API Client
Handles all interactions with Shopify API including data retrieval and query execution
"""
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class ShopifyClient:
    """
    Modular client for Shopify API interactions
    Handles authentication, rate limiting, and data retrieval
    """
    
    API_VERSION = "2024-01"
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, shop_domain: str, access_token: str, http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize Shopify client
        
        Args:
            shop_domain: Shopify store domain (e.g., store.myshopify.com)
            access_token: OAuth access token
            http_client: Optional HTTP client for dependency injection
        """
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = os.getenv("SHOPIFY_API_VERSION", self.API_VERSION)
        self.base_url = f"https://{shop_domain}/admin/api/{self.api_version}"
        self.http_client = http_client or httpx.AsyncClient()
        
        logger.info(f"Initialized Shopify client for {shop_domain}")
    
    async def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Shopify API with rate limit handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /orders.json)
            params: Query parameters
            json_data: JSON body for POST requests
        
        Returns:
            Response data as dictionary
        
        Raises:
            httpx.HTTPError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        retry_count = 0
        retry_delay = self.INITIAL_RETRY_DELAY
        
        while retry_count <= self.MAX_RETRIES:
            try:
                response = await self.http_client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=30.0
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    if retry_count < self.MAX_RETRIES:
                        logger.warning(f"Rate limit hit, retrying in {retry_delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        retry_count += 1
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        raise httpx.HTTPError(f"Rate limit exceeded after {self.MAX_RETRIES} retries")
                
                # Raise for other error status codes
                response.raise_for_status()
                
                return response.json()
            
            except httpx.TimeoutException as e:
                if retry_count < self.MAX_RETRIES:
                    logger.warning(f"Request timeout, retrying in {retry_delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                    retry_count += 1
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"Request timeout after {self.MAX_RETRIES} retries")
                    raise
            
            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise
        
        raise httpx.HTTPError("Max retries exceeded")
    
    async def get_orders(
        self,
        status: str = "any",
        limit: int = 250,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve orders from Shopify
        
        Args:
            status: Order status filter (any, open, closed, cancelled)
            limit: Maximum number of orders to retrieve (max 250)
            created_at_min: Filter orders created after this date (ISO 8601)
            created_at_max: Filter orders created before this date (ISO 8601)
        
        Returns:
            List of order dictionaries
        """
        params = {
            "status": status,
            "limit": min(limit, 250)
        }
        
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max
        
        try:
            response = await self._make_authenticated_request("GET", "/orders.json", params=params)
            orders = response.get("orders", [])
            
            if not orders:
                logger.info("No orders found matching criteria")
                return []
            
            logger.info(f"Retrieved {len(orders)} orders")
            return orders
        
        except Exception as e:
            logger.error(f"Failed to retrieve orders: {e}")
            raise
    
    async def get_products(
        self,
        limit: int = 250,
        product_type: Optional[str] = None,
        vendor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products from Shopify
        
        Args:
            limit: Maximum number of products to retrieve (max 250)
            product_type: Filter by product type
            vendor: Filter by vendor
        
        Returns:
            List of product dictionaries
        """
        params = {"limit": min(limit, 250)}
        
        if product_type:
            params["product_type"] = product_type
        if vendor:
            params["vendor"] = vendor
        
        try:
            response = await self._make_authenticated_request("GET", "/products.json", params=params)
            products = response.get("products", [])
            
            if not products:
                logger.info("No products found matching criteria")
                return []
            
            logger.info(f"Retrieved {len(products)} products")
            return products
        
        except Exception as e:
            logger.error(f"Failed to retrieve products: {e}")
            raise
    
    async def get_inventory(
        self,
        location_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve inventory levels from Shopify
        
        Args:
            location_ids: Filter by specific location IDs
        
        Returns:
            List of inventory level dictionaries
        """
        try:
            # First get locations if not specified
            if not location_ids:
                locations_response = await self._make_authenticated_request("GET", "/locations.json")
                locations = locations_response.get("locations", [])
                location_ids = [loc["id"] for loc in locations]
            
            # Get inventory levels for each location
            all_inventory = []
            for location_id in location_ids:
                params = {"location_ids": location_id, "limit": 250}
                response = await self._make_authenticated_request("GET", "/inventory_levels.json", params=params)
                inventory_levels = response.get("inventory_levels", [])
                all_inventory.extend(inventory_levels)
            
            if not all_inventory:
                logger.info("No inventory data found")
                return []
            
            logger.info(f"Retrieved {len(all_inventory)} inventory records")
            return all_inventory
        
        except Exception as e:
            logger.error(f"Failed to retrieve inventory: {e}")
            raise
    
    async def get_customers(
        self,
        limit: int = 250,
        created_at_min: Optional[str] = None,
        updated_at_min: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customers from Shopify
        
        Args:
            limit: Maximum number of customers to retrieve (max 250)
            created_at_min: Filter customers created after this date (ISO 8601)
            updated_at_min: Filter customers updated after this date (ISO 8601)
        
        Returns:
            List of customer dictionaries
        """
        params = {"limit": min(limit, 250)}
        
        if created_at_min:
            params["created_at_min"] = created_at_min
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        
        try:
            response = await self._make_authenticated_request("GET", "/customers.json", params=params)
            customers = response.get("customers", [])
            
            if not customers:
                logger.info("No customers found matching criteria")
                return []
            
            logger.info(f"Retrieved {len(customers)} customers")
            return customers
        
        except Exception as e:
            logger.error(f"Failed to retrieve customers: {e}")
            raise
    
    async def execute_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Shopify Admin API
        This can be used for ShopifyQL queries
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
        
        Returns:
            Query results as dictionary
        """
        endpoint = "/graphql.json"
        json_data = {"query": query}
        
        if variables:
            json_data["variables"] = variables
        
        try:
            response = await self._make_authenticated_request("POST", endpoint, json_data=json_data)
            
            if "errors" in response:
                logger.error(f"GraphQL errors: {response['errors']}")
                raise ValueError(f"GraphQL query failed: {response['errors']}")
            
            return response.get("data", {})
        
        except Exception as e:
            logger.error(f"Failed to execute GraphQL query: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()

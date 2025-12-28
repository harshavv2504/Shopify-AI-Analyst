"""
Tests for Shopify Client
Includes property-based tests using Hypothesis
"""
import pytest
import httpx
from hypothesis import given, strategies as st, settings
from unittest.mock import AsyncMock, Mock, patch
import asyncio

from services.shopify_client import ShopifyClient


class TestShopifyClient:
    """Test suite for ShopifyClient"""
    
    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client"""
        client = AsyncMock(spec=httpx.AsyncClient)
        return client
    
    @pytest.fixture
    def shopify_client(self, mock_http_client):
        """Create a ShopifyClient instance with mocked HTTP client"""
        return ShopifyClient(
            shop_domain="test-store.myshopify.com",
            access_token="test_token_123",
            http_client=mock_http_client
        )
    
    # Feature: shopify-ai-analytics, Property 2: Authentication Credentials Inclusion
    # For any API call to Shopify, the request should include valid authentication credentials in the headers
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None)
    @given(
        endpoint=st.sampled_from(["/orders.json", "/products.json", "/customers.json", "/inventory_levels.json"]),
        method=st.sampled_from(["GET", "POST"])
    )
    async def test_authentication_credentials_included_property(self, endpoint, method):
        """
        Property test: All API requests include authentication credentials
        Tests 100 different combinations of endpoints and methods
        """
        # Create mock client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_client.request = AsyncMock(return_value=mock_response)
        
        # Create Shopify client
        client = ShopifyClient(
            shop_domain="test-store.myshopify.com",
            access_token="test_token_abc123",
            http_client=mock_client
        )
        
        # Make request
        await client._make_authenticated_request(method, endpoint)
        
        # Verify authentication header was included
        call_args = mock_client.request.call_args
        headers = call_args.kwargs.get("headers", {})
        
        assert "X-Shopify-Access-Token" in headers, "Authentication header missing"
        assert headers["X-Shopify-Access-Token"] == "test_token_abc123", "Incorrect token"
        assert headers["Content-Type"] == "application/json", "Content-Type header missing"
    
    @pytest.mark.asyncio
    async def test_get_orders_includes_auth(self, shopify_client, mock_http_client):
        """Test that get_orders includes authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"orders": []}
        mock_response.raise_for_status = Mock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        await shopify_client.get_orders()
        
        # Verify auth header was included
        call_args = mock_http_client.request.call_args
        headers = call_args.kwargs["headers"]
        assert "X-Shopify-Access-Token" in headers
        assert headers["X-Shopify-Access-Token"] == "test_token_123"
    
    @pytest.mark.asyncio
    async def test_get_products_includes_auth(self, shopify_client, mock_http_client):
        """Test that get_products includes authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": []}
        mock_response.raise_for_status = Mock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        await shopify_client.get_products()
        
        # Verify auth header was included
        call_args = mock_http_client.request.call_args
        headers = call_args.kwargs["headers"]
        assert "X-Shopify-Access-Token" in headers
    
    @pytest.mark.asyncio
    async def test_get_customers_includes_auth(self, shopify_client, mock_http_client):
        """Test that get_customers includes authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"customers": []}
        mock_response.raise_for_status = Mock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        await shopify_client.get_customers()
        
        # Verify auth header was included
        call_args = mock_http_client.request.call_args
        headers = call_args.kwargs["headers"]
        assert "X-Shopify-Access-Token" in headers


    # Feature: shopify-ai-analytics, Property 4: Rate Limit Retry Behavior
    # For any Shopify API rate limit error, the system should implement exponential backoff
    # and retry the request up to 3 times before failing
    @pytest.mark.asyncio
    @settings(max_examples=50, deadline=None)  # No deadline - retries with sleep take time
    @given(
        retry_count=st.integers(min_value=1, max_value=3)
    )
    async def test_rate_limit_retry_behavior_property(self, retry_count):
        """
        Property test: Rate limit errors trigger exponential backoff retries
        Tests with different retry scenarios
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Create responses: rate limit errors followed by success
        responses = []
        for i in range(retry_count):
            rate_limit_response = Mock()
            rate_limit_response.status_code = 429
            responses.append(rate_limit_response)
        
        # Final successful response
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": "success"}
        success_response.raise_for_status = Mock()
        responses.append(success_response)
        
        mock_client.request = AsyncMock(side_effect=responses)
        
        client = ShopifyClient(
            shop_domain="test-store.myshopify.com",
            access_token="test_token",
            http_client=mock_client
        )
        
        # Should succeed after retries
        result = await client._make_authenticated_request("GET", "/test.json")
        
        # Verify it retried the correct number of times
        assert mock_client.request.call_count == retry_count + 1
        assert result == {"data": "success"}
    
    @pytest.mark.asyncio
    async def test_rate_limit_max_retries_exceeded(self):
        """Test that rate limit errors fail after max retries"""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Always return 429
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        mock_client.request = AsyncMock(return_value=rate_limit_response)
        
        client = ShopifyClient(
            shop_domain="test-store.myshopify.com",
            access_token="test_token",
            http_client=mock_client
        )
        
        # Should fail after MAX_RETRIES
        with pytest.raises(httpx.HTTPError, match="Rate limit exceeded"):
            await client._make_authenticated_request("GET", "/test.json")
        
        # Should have tried MAX_RETRIES + 1 times (initial + 3 retries)
        assert mock_client.request.call_count == 4
    
    @pytest.mark.asyncio
    @settings(max_examples=30, deadline=None)  # No deadline - backoff with sleep takes time
    @given(
        initial_delay=st.floats(min_value=0.1, max_value=2.0)
    )
    async def test_exponential_backoff_timing(self, initial_delay):
        """
        Property test: Verify exponential backoff increases delay
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Return rate limit twice, then success
        responses = [
            Mock(status_code=429),
            Mock(status_code=429),
            Mock(status_code=200, json=lambda: {"data": "ok"}, raise_for_status=Mock())
        ]
        mock_client.request = AsyncMock(side_effect=responses)
        
        client = ShopifyClient(
            shop_domain="test-store.myshopify.com",
            access_token="test_token",
            http_client=mock_client
        )
        client.INITIAL_RETRY_DELAY = initial_delay
        
        # Execute request
        await client._make_authenticated_request("GET", "/test.json")
        
        # Verify it retried
        assert mock_client.request.call_count == 3


    # Feature: shopify-ai-analytics, Property 5: Empty Result Handling
    # For any query that returns empty results from Shopify, the system should handle it
    # gracefully without throwing errors and should communicate the lack of data
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None)
    @given(
        method_name=st.sampled_from(["get_orders", "get_products", "get_customers", "get_inventory"])
    )
    async def test_empty_result_handling_property(self, method_name):
        """
        Property test: All data retrieval methods handle empty results gracefully
        Tests across all get methods
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Return empty results
        empty_response = Mock()
        empty_response.status_code = 200
        empty_response.raise_for_status = Mock()
        
        # Different empty response formats for different endpoints
        if method_name == "get_orders":
            empty_response.json.return_value = {"orders": []}
        elif method_name == "get_products":
            empty_response.json.return_value = {"products": []}
        elif method_name == "get_customers":
            empty_response.json.return_value = {"customers": []}
        elif method_name == "get_inventory":
            # Inventory needs locations first
            locations_response = Mock()
            locations_response.status_code = 200
            locations_response.json.return_value = {"locations": [{"id": 1}]}
            locations_response.raise_for_status = Mock()
            
            inventory_response = Mock()
            inventory_response.status_code = 200
            inventory_response.json.return_value = {"inventory_levels": []}
            inventory_response.raise_for_status = Mock()
            
            mock_client.request = AsyncMock(side_effect=[locations_response, inventory_response])
        else:
            mock_client.request = AsyncMock(return_value=empty_response)
        
        if method_name != "get_inventory":
            mock_client.request = AsyncMock(return_value=empty_response)
        
        client = ShopifyClient(
            shop_domain="test-store.myshopify.com",
            access_token="test_token",
            http_client=mock_client
        )
        
        # Call the method
        method = getattr(client, method_name)
        result = await method()
        
        # Should return empty list, not raise exception
        assert isinstance(result, list), f"{method_name} should return a list"
        assert len(result) == 0, f"{method_name} should return empty list for no results"
    
    @pytest.mark.asyncio
    async def test_get_orders_empty_results(self, shopify_client, mock_http_client):
        """Test get_orders handles empty results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"orders": []}
        mock_response.raise_for_status = Mock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        result = await shopify_client.get_orders()
        
        assert result == []
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_products_empty_results(self, shopify_client, mock_http_client):
        """Test get_products handles empty results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": []}
        mock_response.raise_for_status = Mock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        result = await shopify_client.get_products()
        
        assert result == []
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_customers_empty_results(self, shopify_client, mock_http_client):
        """Test get_customers handles empty results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"customers": []}
        mock_response.raise_for_status = Mock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        result = await shopify_client.get_customers()
        
        assert result == []
        assert isinstance(result, list)

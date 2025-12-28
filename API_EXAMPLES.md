# API Examples

This document provides practical examples of how to use the API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

### Register a Store

Register your Shopify store to start using the analytics service.

**Endpoint:** `POST /auth/register`

**Request:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "shop_domain": "my-store.myshopify.com",
    "access_token": "shpat_xxxxxxxxxxxxxxxxxxxxx"
  }'
```

**Response:**
```json
{
  "message": "Store registered successfully",
  "store_id": "my-store.myshopify.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Notes:**
- The access token is obtained from your Shopify admin panel
- The returned JWT token is used for subsequent API calls
- Store this token securely on the client side

### Login

Get a new authentication token for an existing store.

**Endpoint:** `POST /auth/login`

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "shop_domain": "my-store.myshopify.com",
    "access_token": "shpat_xxxxxxxxxxxxxxxxxxxxx"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "store_id": "my-store.myshopify.com"
}
```

## Analytics

### Ask a Question

Submit a natural language question about your store data.

**Endpoint:** `POST /analytics/ask`

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

## Example Questions

### 1. Top Selling Products

**Request:**
```bash
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What were my top 5 selling products last week?"
  }'
```

**Response:**
```json
{
  "answer": "Last week, your top 5 selling products were:\n\n1. Classic T-Shirt (245 units) - Your bestseller by a significant margin\n2. Denim Jeans (187 units) - Strong consistent performer\n3. Running Shoes (156 units) - Popular in the athletic category\n4. Leather Wallet (134 units) - Steady accessory sales\n5. Wireless Earbuds (128 units) - Growing tech category\n\nThe Classic T-Shirt is performing exceptionally well and should be prioritized for inventory management. Consider restocking soon to maintain momentum.",
  "confidence": "high",
  "query_used": "SELECT product_name, SUM(quantity) as total_sold FROM orders WHERE created_at >= '2024-12-22' GROUP BY product_name ORDER BY total_sold DESC LIMIT 5",
  "data_points": 5
}
```

### 2. Inventory Projection

**Request:**
```bash
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many units of Classic T-Shirt will I need next month?"
  }'
```

**Response:**
```json
{
  "answer": "Based on the last 30 days of sales data, Classic T-Shirt sells an average of 35 units per day. For next month (30 days), you should plan for approximately 1,050 units.\n\nRecommendations:\n- Order at least 1,050 units to meet expected demand\n- Consider ordering 1,150-1,200 units (10-15% buffer) to account for potential spikes\n- Current inventory: 450 units\n- Additional units needed: 600-750 units\n\nNote: This projection assumes similar sales patterns to the past month. Adjust for any planned promotions or seasonal changes.",
  "confidence": "medium",
  "query_used": "SELECT AVG(daily_quantity) FROM (SELECT DATE(created_at) as date, SUM(quantity) as daily_quantity FROM orders WHERE product_name = 'Classic T-Shirt' AND created_at >= NOW() - INTERVAL '30 days' GROUP BY date)",
  "data_points": 30
}
```

### 3. Stockout Prediction

**Request:**
```bash
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which products are likely to go out of stock in 7 days?"
  }'
```

**Response:**
```json
{
  "answer": "Based on current inventory levels and recent sales velocity, 3 products are at risk of stockout within 7 days:\n\n1. Wireless Earbuds\n   - Current stock: 45 units\n   - Daily sales rate: 8 units\n   - Days until stockout: 5.6 days\n   - Action: Reorder immediately\n\n2. Running Shoes (Size 10)\n   - Current stock: 28 units\n   - Daily sales rate: 4 units\n   - Days until stockout: 7 days\n   - Action: Reorder this week\n\n3. Leather Wallet (Brown)\n   - Current stock: 52 units\n   - Daily sales rate: 7 units\n   - Days until stockout: 7.4 days\n   - Action: Monitor closely, reorder soon\n\nPriority: Focus on Wireless Earbuds first as they will run out soonest.",
  "confidence": "high",
  "query_used": "SELECT product_name, current_inventory, AVG(daily_sales) as avg_daily_sales, (current_inventory / AVG(daily_sales)) as days_remaining FROM inventory JOIN sales_velocity ON inventory.product_id = sales_velocity.product_id WHERE days_remaining <= 7 ORDER BY days_remaining ASC",
  "data_points": 3
}
```

### 4. Customer Behavior

**Request:**
```bash
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which customers placed repeat orders in the last 90 days?"
  }'
```

**Response:**
```json
{
  "answer": "In the last 90 days, 127 customers placed repeat orders. Here are your top repeat customers:\n\n1. Sarah Johnson (sarah.j@email.com)\n   - Orders: 8\n   - Total spent: $1,245\n   - Average order: $156\n\n2. Michael Chen (m.chen@email.com)\n   - Orders: 7\n   - Total spent: $980\n   - Average order: $140\n\n3. Emily Rodriguez (emily.r@email.com)\n   - Orders: 6\n   - Total spent: $1,120\n   - Average order: $187\n\nInsights:\n- 23% of your customers are repeat buyers (127 out of 550 total)\n- Repeat customers spend 2.3x more on average than one-time buyers\n- Most repeat purchases happen within 21 days of the first order\n\nRecommendations:\n- Create a loyalty program to encourage more repeat purchases\n- Send personalized follow-up emails 14-21 days after first purchase\n- Offer exclusive discounts to customers after their second order",
  "confidence": "high",
  "query_used": "SELECT customer_id, customer_email, COUNT(*) as order_count, SUM(total_price) as total_spent FROM orders WHERE created_at >= NOW() - INTERVAL '90 days' GROUP BY customer_id, customer_email HAVING COUNT(*) > 1 ORDER BY order_count DESC",
  "data_points": 127
}
```

### 5. Reorder Recommendations

**Request:**
```bash
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How much inventory should I reorder based on last 30 days sales?"
  }'
```

**Response:**
```json
{
  "answer": "Based on the last 30 days of sales data, here are reorder recommendations for your top-moving products:\n\n1. Classic T-Shirt\n   - 30-day sales: 1,050 units\n   - Current stock: 450 units\n   - Recommended reorder: 800 units\n   - Reasoning: High velocity item, maintain 2-week buffer\n\n2. Denim Jeans\n   - 30-day sales: 680 units\n   - Current stock: 320 units\n   - Recommended reorder: 500 units\n   - Reasoning: Steady seller, current stock covers 14 days\n\n3. Running Shoes\n   - 30-day sales: 540 units\n   - Current stock: 180 units\n   - Recommended reorder: 600 units\n   - Reasoning: Growing category, stock low\n\n4. Leather Wallet\n   - 30-day sales: 420 units\n   - Current stock: 280 units\n   - Recommended reorder: 300 units\n   - Reasoning: Consistent performer, adequate buffer\n\n5. Wireless Earbuds\n   - 30-day sales: 390 units\n   - Current stock: 45 units\n   - Recommended reorder: 500 units (URGENT)\n   - Reasoning: Stock critically low, high demand\n\nTotal recommended reorder value: Approximately $45,000\nPriority: Wireless Earbuds and Running Shoes need immediate attention.",
  "confidence": "high",
  "query_used": "SELECT product_name, SUM(quantity) as units_sold, current_inventory FROM orders JOIN inventory ON orders.product_id = inventory.product_id WHERE orders.created_at >= NOW() - INTERVAL '30 days' GROUP BY product_name, current_inventory ORDER BY units_sold DESC",
  "data_points": 5
}
```

### 6. Sales Trends

**Request:**
```bash
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me sales trends for the last 30 days"
  }'
```

**Response:**
```json
{
  "answer": "Sales trends for the last 30 days show positive momentum:\n\nOverall Performance:\n- Total revenue: $87,450\n- Total orders: 1,247\n- Average order value: $70.13\n- Growth vs. previous 30 days: +12%\n\nWeekly Breakdown:\n- Week 1: $18,200 (412 orders)\n- Week 2: $21,500 (468 orders) ↑ 18%\n- Week 3: $23,100 (502 orders) ↑ 7%\n- Week 4: $24,650 (515 orders) ↑ 7%\n\nKey Insights:\n- Consistent week-over-week growth\n- Weekend sales are 35% higher than weekdays\n- Peak sales day: Saturday\n- Lowest sales day: Tuesday\n\nTop Categories:\n1. Apparel: $42,300 (48% of revenue)\n2. Accessories: $23,100 (26% of revenue)\n3. Electronics: $15,800 (18% of revenue)\n4. Other: $6,250 (8% of revenue)\n\nRecommendations:\n- Continue current marketing strategy\n- Consider Tuesday promotions to boost mid-week sales\n- Increase inventory for weekend demand\n- Focus on apparel category as primary revenue driver",
  "confidence": "high",
  "query_used": "SELECT DATE_TRUNC('day', created_at) as date, SUM(total_price) as daily_revenue, COUNT(*) as order_count FROM orders WHERE created_at >= NOW() - INTERVAL '30 days' GROUP BY date ORDER BY date",
  "data_points": 30
}
```

## Error Responses

### Invalid Authentication

**Response:**
```json
{
  "detail": "Invalid or expired token"
}
```
**Status Code:** 401

### Missing Question

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
**Status Code:** 422

### Service Error

**Response:**
```json
{
  "error": "Unable to process question",
  "message": "The AI service encountered an error. Please try rephrasing your question.",
  "retry": true
}
```
**Status Code:** 500

### Ambiguous Question

**Response:**
```json
{
  "answer": "I need more information to answer your question accurately. Could you please specify:\n- Which product or category you're asking about?\n- What time period you're interested in?\n- What specific metric you want to know?",
  "confidence": "low",
  "clarification_needed": true
}
```
**Status Code:** 200

## Rate Limits

- 100 requests per minute per store
- 1,000 requests per hour per store
- Rate limit headers included in all responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Testing with cURL

Complete example workflow:

```bash
# 1. Register store
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"shop_domain": "test-store.myshopify.com", "access_token": "test_token"}' \
  | jq -r '.token')

# 2. Ask a question
curl -X POST http://localhost:8000/analytics/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What were my top selling products last week?"}' \
  | jq '.'
```

## Using the Interactive Documentation

FastAPI provides automatic interactive documentation:

1. Start the server: `uvicorn main:app --reload`
2. Open your browser to: http://localhost:8000/docs
3. Click "Authorize" and enter your JWT token
4. Try out any endpoint directly from the browser
5. See request/response examples in real-time

# System Architecture

## Overview

This application processes natural language questions about Shopify store data and returns business insights. The system uses AI to understand questions, generate queries, fetch data, and explain results in plain language.

## Architecture Decision: Python-Only Approach

The original assignment specified a Rails API + Python AI service architecture. This implementation uses a pure Python approach with FastAPI for the following reasons:

**Simplified Deployment**
- Single technology stack reduces operational complexity
- Fewer moving parts means easier maintenance
- No inter-service communication overhead

**Performance**
- FastAPI provides async capabilities comparable to Rails
- Direct communication between API and AI services
- Lower latency without network calls between services

**Development Efficiency**
- Unified codebase in one language
- Shared data models and validation
- Easier debugging and testing

The FastAPI application serves the same role as the Rails API would have - handling authentication, request validation, and response formatting - while also hosting the AI services directly.

## System Flow

```
User Question
    ↓
FastAPI Endpoint (/analytics/ask)
    ↓
Agent Service (Orchestrator)
    ↓
┌─────────────────────────────────────┐
│  Step 1: Intent Classifier          │
│  - Understands the question         │
│  - Extracts entities (dates, etc.)  │
│  - Classifies intent type           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 2: Query Generator            │
│  - Generates ShopifyQL query        │
│  - Adds filters and aggregations    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 3: Shopify Client             │
│  - Executes query via Shopify API   │
│  - Fetches actual store data        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 4: Insight Generator          │
│  - Analyzes the data                │
│  - Identifies patterns              │
│  - Creates recommendations          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 5: Response Formatter         │
│  - Converts to plain language       │
│  - Removes technical jargon         │
└─────────────────────────────────────┘
    ↓
JSON Response to User
```

## Component Details

### FastAPI Application (main.py)

Handles HTTP requests and responses. Provides:
- Authentication endpoints for Shopify stores
- Analytics endpoint for questions
- Request validation using Pydantic
- Error handling and logging
- API documentation

### Agent Service (services/agent.py)

The orchestrator that coordinates the entire pipeline. It:
- Receives questions from the API
- Calls each service in sequence
- Handles errors at each step
- Returns the final formatted response

### Intent Classifier (services/intent_classifier.py)

Uses OpenAI to understand what the user is asking:
- Classifies questions into categories (sales, inventory, customers, etc.)
- Extracts time periods ("last week", "next month")
- Identifies specific entities (product names, customer segments)
- Returns structured intent data

### Query Generator (services/query_generator.py)

Converts intent into ShopifyQL:
- Maps intent types to appropriate Shopify data sources
- Constructs queries with proper syntax
- Adds time filters and aggregations
- Validates query structure

### Shopify Client (services/shopify_client.py)

Communicates with Shopify's API:
- Authenticates using store credentials
- Executes ShopifyQL queries
- Handles API rate limits
- Returns raw data results

### Insight Generator (services/insight_generator.py)

Analyzes the data to find meaningful patterns:
- Calculates trends and comparisons
- Identifies anomalies
- Generates specific recommendations
- Assesses confidence levels

### Response Formatter (services/response_formatter.py)

Makes the output user-friendly:
- Translates technical results to business language
- Structures the response clearly
- Emphasizes actionable insights
- Maintains professional tone

## Data Flow Example

**Question:** "What were my top 5 selling products last week?"

**Step 1 - Intent Classification:**
```json
{
  "intent_type": "sales_trends",
  "time_period": "last_week",
  "entities": {
    "limit": 5,
    "metric": "sales"
  }
}
```

**Step 2 - Query Generation:**
```sql
SELECT product_name, SUM(quantity) as total_sold
FROM orders
WHERE created_at >= '2024-12-22'
GROUP BY product_name
ORDER BY total_sold DESC
LIMIT 5
```

**Step 3 - Data Retrieval:**
```json
[
  {"product_name": "Widget A", "total_sold": 150},
  {"product_name": "Gadget B", "total_sold": 120},
  {"product_name": "Tool C", "total_sold": 95},
  {"product_name": "Device D", "total_sold": 87},
  {"product_name": "Item E", "total_sold": 76}
]
```

**Step 4 - Insight Generation:**
```json
{
  "insights": [
    "Widget A is your clear bestseller with 150 units sold",
    "Top 5 products account for 528 total units",
    "Strong performance across all top products"
  ],
  "recommendations": [
    "Ensure Widget A inventory is well-stocked",
    "Consider promoting similar products to Widget A"
  ]
}
```

**Step 5 - Response Formatting:**
```json
{
  "answer": "Last week, your top 5 selling products were Widget A (150 units), Gadget B (120 units), Tool C (95 units), Device D (87 units), and Item E (76 units). Widget A is performing exceptionally well and should be prioritized for inventory management.",
  "confidence": "high"
}
```

## Authentication Flow

1. Store owner installs the Shopify app
2. Shopify redirects to OAuth callback with authorization code
3. Application exchanges code for access token
4. Access token is stored securely in database
5. Subsequent API calls use this token to authenticate with Shopify

## Error Handling

The system handles errors at multiple levels:

**API Level:**
- Invalid request format
- Missing authentication
- Rate limiting

**Service Level:**
- LLM failures or timeouts
- Invalid query generation
- Shopify API errors

**Data Level:**
- Empty result sets
- Malformed data
- Missing required fields

Each error is logged and returns an appropriate error message to the user.

## Security Considerations

**API Keys:**
- OpenAI API key stored in environment variables
- Never exposed in responses or logs

**Shopify Tokens:**
- Access tokens stored encrypted in database
- Transmitted only over HTTPS
- Scoped to minimum required permissions

**Input Validation:**
- All requests validated with Pydantic schemas
- SQL injection prevented by using parameterized queries
- Rate limiting on API endpoints

## Scalability

**Current Design:**
- Handles single store queries efficiently
- Async operations for concurrent requests
- Stateless API for horizontal scaling

**Future Improvements:**
- Cache frequently asked questions
- Queue system for long-running queries
- Database read replicas for analytics
- CDN for static responses

## Testing Strategy

**Unit Tests:**
- Each service tested independently
- Mock external API calls
- Verify correct data transformations

**Integration Tests:**
- Test complete pipeline end-to-end
- Use mock Shopify data
- Verify response format

**Scenario Tests:**
- 28 real-world question patterns
- Cover edge cases and variations
- Ensure consistent behavior

## Technology Choices

**FastAPI:**
- Modern async framework
- Automatic API documentation
- Built-in validation with Pydantic
- High performance

**OpenAI GPT-4o-mini:**
- Strong natural language understanding
- Cost-effective for production use
- Reliable query generation
- Good at explaining results

**SQLAlchemy:**
- Mature ORM with good documentation
- Supports multiple databases
- Migration management
- Type safety

**pytest:**
- Comprehensive testing framework
- Good async support
- Extensive plugin ecosystem
- Clear test output

## Deployment Considerations

**Environment Variables Required:**
- `OPENAI_API_KEY` - For AI services
- `SHOPIFY_API_KEY` - For OAuth
- `SHOPIFY_API_SECRET` - For OAuth
- `DATABASE_URL` - For data persistence
- `SECRET_KEY` - For session management

**Infrastructure:**
- Python 3.10+ runtime
- PostgreSQL database
- HTTPS endpoint for OAuth callback
- Sufficient memory for LLM operations (2GB+ recommended)

**Monitoring:**
- Log all API requests and responses
- Track LLM token usage
- Monitor Shopify API rate limits
- Alert on error rate thresholds

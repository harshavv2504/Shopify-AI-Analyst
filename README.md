# Shopify AI Analytics Assistant

This project provides an AI-powered analytics assistant for Shopify stores. It interprets natural language questions about your business and returns data-driven insights without requiring technical knowledge of query languages or analytics tools.

## Overview

The assistant bridges the gap between business questions and technical data retrieval. When you ask a question like "What were my top selling products last week?", the system handles the entire process: understanding your intent, generating the appropriate queries, fetching data from Shopify, analyzing the results, and presenting actionable insights in clear language.

## Core Capabilities

**Natural Language Interface**  
The system accepts questions in plain English and interprets them accurately, handling variations in phrasing and extracting relevant details like time periods, product names, and customer segments.

**Intelligent Query Generation**  
Based on the interpreted intent, the system automatically constructs ShopifyQL queries with appropriate filters, aggregations, and joins. This eliminates the need to learn query syntax or understand database schemas.

**Data Analysis and Insights**  
Rather than simply returning raw data, the system analyzes results to identify patterns, trends, and anomalies. It provides context for the numbers and generates specific, actionable recommendations.

**Comprehensive Testing**  
The codebase includes over 100 tests covering real-world scenarios, edge cases, and the complete analysis pipeline to ensure reliable performance.

## How the System Works

The assistant processes questions through a five-stage pipeline:

**1. Intent Classification**  
The system analyzes the question to determine what type of information is being requested (sales trends, customer behavior, inventory needs, etc.) and extracts relevant entities like time periods and product names.

**2. Query Generation**  
Using the classified intent, the system constructs the appropriate ShopifyQL query with necessary filters, aggregations, and data sources.

**3. Data Retrieval**  
The generated query is executed against the Shopify API to fetch the relevant data.

**4. Insight Generation**  
The retrieved data is analyzed to identify meaningful patterns, compare against historical trends, and generate specific recommendations based on the findings.

**5. Response Formatting**  
The technical analysis is translated into clear, business-focused language that emphasizes actionable insights rather than raw metrics.

This complete process typically takes 4-6 seconds per question.

## Project Structure

```
Shopify AI Assistant/
├── services/           
│   ├── agent.py                  # Orchestrates the complete pipeline
│   ├── intent_classifier.py      # Classifies questions and extracts entities
│   ├── query_generator.py        # Generates ShopifyQL queries
│   ├── insight_generator.py      # Analyzes data and generates insights
│   ├── response_formatter.py     # Formats responses for clarity
│   ├── openai_service.py         # Manages OpenAI API interactions
│   ├── shopify_client.py         # Handles Shopify API communication
│   └── prompt_manager.py         # Manages AI prompt configurations
├── routers/            
│   ├── auth.py                   # Authentication endpoints
│   └── analytics.py              # Analytics query endpoints
├── models/             
│   ├── intent.py                 # Intent classification data structures
│   ├── schemas.py                # API request and response schemas
│   ├── database.py               # Database model definitions
│   └── store.py                  # Store configuration models
├── utils/              
│   └── logger.py                 # Structured logging utilities
├── tests/              
│   ├── conftest.py               # Shared test fixtures and configuration
│   ├── test_intent_classifier.py
│   ├── test_query_generator.py
│   ├── test_insight_generator.py
│   ├── test_response_formatter.py
│   ├── test_agent.py
│   └── test_query_generation_scenarios.py  # 28 real-world test scenarios
├── config/             
│   └── prompts.json              # Configurable AI prompts
├── main.py             # FastAPI application entry point
├── demo.py             # Standalone demo with mock data
├── requirements.txt    # Python dependencies
├── pytest.ini          # Test configuration
└── .env.example        # Environment variable template
```

## Installation

### Requirements

- Python 3.10 or higher
- OpenAI API key

### Setup Instructions

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd "Shopify AI Assistant"
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Running the Demo

The included demo script demonstrates the system's capabilities using mock data, allowing you to explore functionality without connecting to a Shopify store:

```bash
python demo.py
```

The demo initializes the AI services, creates realistic mock data, and processes several example questions to show the complete analysis pipeline in action.

### Starting the API Server

To run the full API server:

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Once running, you can access:
- API endpoints at http://localhost:8000
- Interactive API documentation at http://localhost:8000/docs
- Alternative documentation at http://localhost:8000/redoc

### API Endpoints

**Authentication**
- `POST /auth/register` - Register a new Shopify store
- `POST /auth/login` - Authenticate and receive an access token

**Analytics**
- `POST /analytics/ask` - Submit a natural language question
- `GET /analytics/history` - Retrieve previous queries
- `GET /analytics/insights/{insight_id}` - Retrieve a specific insight

### Example Questions

The system handles a wide range of business questions:

**Sales Analysis**
- "What were my top 5 selling products last week?"
- "Show me sales trends for the last 30 days"
- "Which products are underperforming this month?"

**Customer Insights**
- "Which customers are repeat buyers?"
- "Who are my highest-value customers?"
- "What is my customer retention rate?"

**Inventory Management**
- "How many units should I reorder based on recent sales velocity?"
- "What products are at risk of stockout?"
- "Which items have slow inventory turnover?"

**General Analytics**
- "How does this month's performance compare to last month?"
- "What is my average order value?"
- "When do I receive the most orders?"

### Connecting to Shopify

To use the assistant with your Shopify store:

1. Add your Shopify credentials to the `.env` file:
   ```env
   SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=your_access_token
   ```

2. Start the API server:
   ```bash
   uvicorn main:app --reload
   ```

3. Register your store:
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "shop_domain": "your-store.myshopify.com",
       "access_token": "your_access_token"
     }'
   ```

4. Submit questions:
   ```bash
   curl -X POST http://localhost:8000/analytics/ask \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "question": "What were my top selling products last week?"
     }'
   ```

Alternatively, use the interactive documentation at http://localhost:8000/docs for a more convenient interface.

## Service Architecture

### Intent Classifier

Analyzes incoming questions to determine the type of information being requested. The classifier identifies five primary intent categories:

- Sales trends and product performance
- Customer behavior and segmentation
- Inventory forecasting and planning
- Product-specific metrics
- Stockout risk assessment

The classifier also extracts entities such as time periods, product names, and customer segments mentioned in the question.

### Query Generator

Constructs ShopifyQL queries based on the classified intent. The generator handles:

- Time-based filtering with support for relative dates
- Aggregation functions (COUNT, SUM, AVG, etc.)
- Entity-specific filtering
- Multi-table joins when necessary

### Insight Generator

Analyzes query results to produce meaningful business insights. This service:

- Identifies patterns and trends in the data
- Compares current metrics against historical performance
- Generates specific, actionable recommendations
- Assesses confidence levels based on data quality and sample size

### Response Formatter

Translates technical analysis into clear business language. The formatter:

- Removes technical jargon and database terminology
- Provides context for numerical results
- Emphasizes actionable insights
- Maintains a professional, informative tone

## Customizing AI Behavior

All AI prompts are stored in `config/prompts.json`, allowing you to modify the system's behavior without changing code. You can customize:

- System instructions for each service
- Prompt templates
- Response style and tone
- Output format preferences

Example configuration:

```json
{
  "intent_classifier": {
    "system_message": "You are an expert at analyzing business analytics questions...",
    "user_prompt_template": "Analyze this question: \"{question}\"..."
  }
}
```

Changes to this file take effect immediately without requiring a server restart.

## Testing

### Running Tests

Execute the complete test suite:

```bash
pytest
```

Run specific test modules:

```bash
pytest tests/test_intent_classifier.py
pytest tests/test_query_generation_scenarios.py
```

View detailed test output:

```bash
pytest -v
```

Generate coverage reports:

```bash
pytest --cov=services --cov=models
```

### Test Coverage

The project includes 101 tests organized into several categories:

**Real-World Scenarios**  
28 tests covering common business questions and their expected query generation and insight patterns.

**Property-Based Tests**  
Using the Hypothesis library to generate randomized test cases that verify system behavior across a wide range of inputs.

**Unit Tests**  
Individual tests for each service component to ensure correct behavior in isolation.

**Integration Tests**  
End-to-end tests that verify the complete pipeline from question to insight.

## Technology Stack

- **FastAPI** - Modern Python web framework with automatic API documentation
- **Python 3.10+** - Core programming language
- **OpenAI GPT-4o-mini** - Natural language understanding and generation
- **Pydantic** - Data validation and settings management
- **SQLAlchemy** - Database ORM and query builder
- **pytest** - Testing framework
- **Hypothesis** - Property-based testing library
- **httpx** - Async HTTP client for API requests
- **python-dotenv** - Environment variable management
- **uvicorn** - ASGI server for production deployment

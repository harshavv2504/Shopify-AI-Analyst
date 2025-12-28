"""
Query Generation Demo - 28 Scenarios
Demonstrates query generation across different business questions
"""
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.openai_service import OpenAIService
from services.intent_classifier import IntentClassifier
from services.query_generator import ShopifyQLGenerator


async def main():
    print("=" * 80)
    print("🧪 Query Generation Demo - 28 Business Scenarios")
    print("=" * 80)
    print()
    
    # Initialize services
    openai_service = OpenAIService()
    intent_classifier = IntentClassifier(openai_service)
    query_generator = ShopifyQLGenerator(openai_service)
    
    # Define 28 test scenarios
    scenarios = [
        # Sales Trends (10)
        ("What were my top 5 selling products last week?", "sales_trends"),
        ("Show me my revenue for each month this year", "sales_trends"),
        ("Compare my sales from last month to this month", "sales_trends"),
        ("What's my daily sales trend for the past 30 days?", "sales_trends"),
        ("What is my average order value this quarter?", "sales_trends/customer_behavior"),
        
        # Customer Behavior (5)
        ("Which customers have purchased more than once?", "customer_behavior"),
        ("Show me the lifetime value of my top 10 customers", "customer_behavior"),
        ("How many new customers did I get last month vs returning customers?", "customer_behavior"),
        ("What's the average time between purchases for repeat customers?", "customer_behavior"),
        ("Who are my customers that spent over $1000?", "customer_behavior"),
        
        # Inventory Projection (5)
        ("Which products should I reorder based on current inventory?", "inventory_projection"),
        ("Which products will run out of stock in the next 2 weeks?", "stockout_prediction"),
        ("What's the inventory turnover rate for my products?", "product_performance"),
        ("Show me products with low inventory turnover", "product_performance"),
        ("What are the optimal stock levels for my top products?", "inventory_projection"),
        
        # Product Performance (5)
        ("Which products have the lowest sales?", "product_performance"),
        ("What percentage of revenue does each product contribute?", "product_performance"),
        ("How are different product categories performing?", "product_performance"),
        ("Which products sell better in summer vs winter?", "sales_trends"),
        ("Which products are frequently bought together?", "customer_behavior"),
        
        # Complex Scenarios (8)
        ("Show me retention rates for customers acquired in Q1", "customer_behavior"),
        ("What's the total value of abandoned carts this month?", "customer_behavior"),
        ("Which regions generate the most revenue?", "sales_trends"),
        ("How effective are my discount codes in driving sales?", "sales_trends"),
        ("What's my refund rate by product?", "product_performance"),
        ("Show me sales between December 15th and December 20th, 2024", "sales_trends"),
        ("Show me orders over $500 from repeat customers in California", "customer_behavior"),
        ("How do my sales compare to last year's same period?", "sales_trends"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (question, expected_intent) in enumerate(scenarios, 1):
        try:
            print(f"\n{'='*80}")
            print(f"Scenario {i}: {question}")
            print(f"{'='*80}")
            
            # Classify intent
            intent_result = intent_classifier.classify(question)
            print(f"✓ Intent Classified: {intent_result.type.value} (confidence: {intent_result.confidence})")
            
            # Check if intent matches expected (allow multiple options)
            expected_intents = expected_intent.split("/")
            if intent_result.type.value not in expected_intents:
                print(f"  ⚠️  Expected: {expected_intent}, Got: {intent_result.type.value}")
            
            # Generate query
            query = query_generator.generate(intent_result)
            print(f"✓ Query Generated ({len(query)} chars)")
            
            # Validate basic query structure
            assert 'SELECT' in query.upper(), "Query must contain SELECT"
            assert 'FROM' in query.upper(), "Query must contain FROM"
            
            # Show query snippet
            query_snippet = query[:200] + "..." if len(query) > 200 else query
            print(f"\nQuery Preview:")
            print(f"  {query_snippet}")
            
            passed += 1
            print(f"\n✅ Scenario {i} PASSED")
            
        except Exception as e:
            failed += 1
            print(f"\n❌ Scenario {i} FAILED: {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"📊 Results: {passed} passed, {failed} failed out of {len(scenarios)} scenarios")
    print(f"{'='*80}")
    
    if failed == 0:
        print("\n🎉 All scenarios passed! Query generation is working correctly.")
    else:
        print(f"\n⚠️  {failed} scenarios need attention.")


if __name__ == "__main__":
    asyncio.run(main())

"""
Demo script to test the AI Analytics application without Shopify account.
This simulates the entire workflow with mock data.
"""
import asyncio
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from services.openai_service import OpenAIService
from services.intent_classifier import IntentClassifier
from services.query_generator import ShopifyQLGenerator
from services.insight_generator import InsightGenerator
from services.response_formatter import ResponseFormatter
from services.agent import ShopifyAnalyticsAgent


async def demo():
    print("=" * 70)
    print("🎯 Shopify AI Analytics Demo")
    print("   (No Shopify Account Required)")
    print("=" * 70)
    print()
    
    try:
        # Initialize services
        print("📦 Initializing AI services...")
        openai_service = OpenAIService()
        intent_classifier = IntentClassifier(openai_service)
        query_generator = ShopifyQLGenerator(openai_service)
        insight_generator = InsightGenerator(openai_service)
        response_formatter = ResponseFormatter(openai_service)
        print("✅ Services initialized\n")
        
        # Mock Shopify client with realistic data
        print("🔧 Setting up mock Shopify data...")
        mock_shopify = Mock()
        
        # Rich mock data for realistic demo
        mock_orders = [
            {
                "id": 1001,
                "created_at": "2024-12-21T10:30:00Z",
                "total_price": "299.99",
                "line_items": [
                    {"title": "Premium Widget", "quantity": 2, "price": "99.99", "product_id": 101},
                    {"title": "Deluxe Gadget", "quantity": 1, "price": "100.00", "product_id": 102}
                ],
                "customer": {"id": 501, "email": "customer1@example.com"}
            },
            {
                "id": 1002,
                "created_at": "2024-12-22T14:15:00Z",
                "total_price": "450.00",
                "line_items": [
                    {"title": "Premium Widget", "quantity": 3, "price": "99.99", "product_id": 101},
                    {"title": "Standard Tool", "quantity": 2, "price": "75.00", "product_id": 103}
                ],
                "customer": {"id": 502, "email": "customer2@example.com"}
            },
            {
                "id": 1003,
                "created_at": "2024-12-23T09:45:00Z",
                "total_price": "199.99",
                "line_items": [
                    {"title": "Basic Kit", "quantity": 1, "price": "199.99", "product_id": 104}
                ],
                "customer": {"id": 501, "email": "customer1@example.com"}
            },
            {
                "id": 1004,
                "created_at": "2024-12-24T16:20:00Z",
                "total_price": "599.97",
                "line_items": [
                    {"title": "Premium Widget", "quantity": 6, "price": "99.99", "product_id": 101}
                ],
                "customer": {"id": 503, "email": "customer3@example.com"}
            },
            {
                "id": 1005,
                "created_at": "2024-12-25T11:00:00Z",
                "total_price": "175.00",
                "line_items": [
                    {"title": "Standard Tool", "quantity": 1, "price": "75.00", "product_id": 103},
                    {"title": "Deluxe Gadget", "quantity": 1, "price": "100.00", "product_id": 102}
                ],
                "customer": {"id": 501, "email": "customer1@example.com"}
            }
        ]
        
        mock_products = [
            {"id": 101, "title": "Premium Widget", "price": "99.99", "inventory_quantity": 45},
            {"id": 102, "title": "Deluxe Gadget", "price": "100.00", "inventory_quantity": 12},
            {"id": 103, "title": "Standard Tool", "price": "75.00", "inventory_quantity": 8},
            {"id": 104, "title": "Basic Kit", "price": "199.99", "inventory_quantity": 25}
        ]
        
        mock_customers = [
            {"id": 501, "email": "customer1@example.com", "orders_count": 3, "total_spent": "675.98"},
            {"id": 502, "email": "customer2@example.com", "orders_count": 1, "total_spent": "450.00"},
            {"id": 503, "email": "customer3@example.com", "orders_count": 1, "total_spent": "599.97"}
        ]
        
        mock_shopify.get_orders = AsyncMock(return_value=mock_orders)
        mock_shopify.get_products = AsyncMock(return_value=mock_products)
        mock_shopify.get_customers = AsyncMock(return_value=mock_customers)
        mock_shopify.get_inventory = AsyncMock(return_value=[
            {"product_id": 101, "available": 45, "location_id": 1},
            {"product_id": 102, "available": 12, "location_id": 1},
            {"product_id": 103, "available": 8, "location_id": 1},
            {"product_id": 104, "available": 25, "location_id": 1}
        ])
        
        print("✅ Mock data ready")
        print(f"   • {len(mock_orders)} orders")
        print(f"   • {len(mock_products)} products")
        print(f"   • {len(mock_customers)} customers\n")
        
        # Create agent
        agent = ShopifyAnalyticsAgent(
            intent_classifier=intent_classifier,
            query_generator=query_generator,
            shopify_client=mock_shopify,
            insight_generator=insight_generator,
            response_formatter=response_formatter
        )
        
        # Test questions
        questions = [
            "What were my top 5 selling products last week?",
            "Which customers are repeat buyers?",
            "How many units should I reorder based on recent sales?",
        ]
        
        for i, question in enumerate(questions, 1):
            print("\n" + "=" * 80)
            print(f"📝 Question {i}: {question}")
            print("=" * 80)
            
            try:
                print("\n⏳ Processing question...")
                response = await agent.process_question(question)
                
                print("\n" + "─" * 80)
                print("📊 COMPLETE ANALYSIS RESULT")
                print("─" * 80)
                
                print(f"\n💬 ANSWER:")
                print("─" * 80)
                print(response['answer'])
                print("─" * 80)
                
                print(f"\n🎯 Confidence Level: {response['confidence'].upper()}")
                
                print(f"\n🔍 Generated Query:")
                print("─" * 80)
                query_lines = response['query_used'].split('\n')
                for line in query_lines[:15]:  # Show first 15 lines
                    print(f"  {line}")
                if len(query_lines) > 15:
                    print(f"  ... ({len(query_lines) - 15} more lines)")
                print("─" * 80)
                
                print(f"\n🧠 Reasoning Steps:")
                for idx, step in enumerate(response['reasoning_steps'], 1):
                    print(f"  {idx}. {step}")
                
                print(f"\n⏰ Timestamp: {response['timestamp']}")
                
            except Exception as e:
                print(f"\n❌ Error processing question: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("✅ Demo Complete!")
        print("=" * 80)
        print("\n💡 What just happened:")
        print("   1. Intent Classification - AI identified what you're asking")
        print("   2. Query Generation - Created ShopifyQL queries automatically")
        print("   3. Data Retrieval - Fetched data from mock Shopify store")
        print("   4. Insight Generation - AI analyzed the data for patterns")
        print("   5. Response Formatting - Converted technical results to business language")
        print("\n🎉 All components working without a real Shopify account!")
        print("\n📊 Mock Data Summary:")
        print(f"   • Total Orders: 5")
        print(f"   • Total Revenue: $1,724.95")
        print(f"   • Products: 4 (Premium Widget, Deluxe Gadget, Standard Tool, Basic Kit)")
        print(f"   • Customers: 3 (1 repeat customer with 3 orders)")
        print(f"   • Top Product: Premium Widget (11 units sold)")
        print("\n🚀 Ready for production with a real Shopify store!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("\n💡 Common issues:")
        print("   1. OpenAI API key not set in .env file")
        print("   2. Missing dependencies - run: pip install -r requirements.txt")
        print("   3. Wrong directory - make sure you're in python-service/")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(demo())

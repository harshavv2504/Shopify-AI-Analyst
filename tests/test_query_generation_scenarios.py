"""
Comprehensive Query Generation Test Suite
Tests 28 scenarios to verify query generation correctness
"""
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.openai_service import OpenAIService
from services.intent_classifier import IntentClassifier
from services.query_generator import ShopifyQLGenerator


class TestQueryGenerationScenarios:
    """Test suite for comprehensive query generation validation"""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance"""
        return OpenAIService()
    
    @pytest.fixture
    def intent_classifier(self, openai_service):
        """Create intent classifier instance"""
        return IntentClassifier(openai_service)
    
    @pytest.fixture
    def query_generator(self, openai_service):
        """Create query generator instance"""
        return ShopifyQLGenerator(openai_service)
    
    # Sales Trends Scenarios (10 tests)
    
    def test_scenario_01_top_selling_products_last_week(self, intent_classifier, query_generator):
        """Scenario 1: Top selling products in last week"""
        question = "What were my top 5 selling products last week?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        
        assert 'SELECT' in query.upper()
        assert 'FROM' in query.upper()
        
        print(f"\n✅ Scenario 1 - Top Selling Products")
        print(f"   Intent: {intent_result.type.value} (confidence: {intent_result.confidence})")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_02_revenue_by_month(self, intent_classifier, query_generator):
        """Scenario 2: Monthly revenue breakdown"""
        question = "Show me my revenue for each month this year"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 2 - Monthly Revenue")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_03_sales_comparison_periods(self, intent_classifier, query_generator):
        """Scenario 3: Compare sales between two periods"""
        question = "Compare my sales from last month to this month"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 3 - Sales Comparison")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_04_daily_sales_trend(self, intent_classifier, query_generator):
        """Scenario 4: Daily sales trend"""
        question = "What's my daily sales trend for the past 30 days?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 4 - Daily Sales Trend")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_05_average_order_value(self, intent_classifier, query_generator):
        """Scenario 5: Average order value"""
        question = "What is my average order value this quarter?"
        
        intent_result = intent_classifier.classify(question)
        # Can be either sales_trends or customer_behavior
        assert intent_result.type.value in ['sales_trends', 'customer_behavior']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 5 - Average Order Value")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    # Customer Behavior Scenarios (5 tests)
    
    def test_scenario_06_repeat_customers(self, intent_classifier, query_generator):
        """Scenario 6: Identify repeat customers"""
        question = "Which customers have purchased more than once?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'customer_behavior'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 6 - Repeat Customers")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_07_customer_lifetime_value(self, intent_classifier, query_generator):
        """Scenario 7: Customer lifetime value"""
        question = "Show me the lifetime value of my top 10 customers"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'customer_behavior'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 7 - Customer Lifetime Value")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_08_new_vs_returning(self, intent_classifier, query_generator):
        """Scenario 8: New vs returning customers"""
        question = "How many new customers did I get last month vs returning customers?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'customer_behavior'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 8 - New vs Returning Customers")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_09_customer_purchase_frequency(self, intent_classifier, query_generator):
        """Scenario 9: Customer purchase frequency"""
        question = "What's the average time between purchases for repeat customers?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'customer_behavior'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 9 - Purchase Frequency")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_10_high_value_customers(self, intent_classifier, query_generator):
        """Scenario 10: High value customers"""
        question = "Who are my customers that spent over $1000?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'customer_behavior'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 10 - High Value Customers")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    # Inventory Projection Scenarios (5 tests)
    
    def test_scenario_11_reorder_recommendations(self, intent_classifier, query_generator):
        """Scenario 11: Products needing reorder"""
        question = "Which products should I reorder based on current inventory?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'inventory_projection'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 11 - Reorder Recommendations")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_12_stockout_prediction(self, intent_classifier, query_generator):
        """Scenario 12: Predict stockouts"""
        question = "Which products will run out of stock in the next 2 weeks?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['inventory_projection', 'stockout_prediction']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 12 - Stockout Prediction")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_13_inventory_turnover(self, intent_classifier, query_generator):
        """Scenario 13: Inventory turnover rate"""
        question = "What's the inventory turnover rate for my products?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['inventory_projection', 'product_performance']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 13 - Inventory Turnover")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_14_slow_moving_inventory(self, intent_classifier, query_generator):
        """Scenario 14: Slow moving inventory"""
        question = "Show me products with low inventory turnover"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['inventory_projection', 'product_performance']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 14 - Slow Moving Inventory")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_15_optimal_stock_levels(self, intent_classifier, query_generator):
        """Scenario 15: Optimal stock levels"""
        question = "What are the optimal stock levels for my top products?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'inventory_projection'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 15 - Optimal Stock Levels")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    # Product Performance Scenarios (5 tests)
    
    def test_scenario_16_underperforming_products(self, intent_classifier, query_generator):
        """Scenario 16: Underperforming products"""
        question = "Which products have the lowest sales?"
        
        intent_result = intent_classifier.classify(question)
        # Can be either product_performance or sales_trends
        assert intent_result.type.value in ['product_performance', 'sales_trends']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 16 - Underperforming Products")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_17_product_revenue_contribution(self, intent_classifier, query_generator):
        """Scenario 17: Product revenue contribution"""
        question = "What percentage of revenue does each product contribute?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'product_performance'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 17 - Revenue Contribution")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_18_product_category_performance(self, intent_classifier, query_generator):
        """Scenario 18: Product category performance"""
        question = "How are different product categories performing?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'product_performance'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 18 - Category Performance")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_19_seasonal_product_trends(self, intent_classifier, query_generator):
        """Scenario 19: Seasonal product trends"""
        question = "Which products sell better in summer vs winter?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['product_performance', 'sales_trends']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 19 - Seasonal Trends")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_20_product_bundle_analysis(self, intent_classifier, query_generator):
        """Scenario 20: Products frequently bought together"""
        question = "Which products are frequently bought together?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['product_performance', 'customer_behavior']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 20 - Product Bundles")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    # Complex Scenarios (8 tests)
    
    def test_scenario_21_cohort_analysis(self, intent_classifier, query_generator):
        """Scenario 21: Customer cohort analysis"""
        question = "Show me retention rates for customers acquired in Q1"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'customer_behavior'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 21 - Cohort Analysis")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_22_abandoned_cart_value(self, intent_classifier, query_generator):
        """Scenario 22: Abandoned cart analysis"""
        question = "What's the total value of abandoned carts this month?"
        
        intent_result = intent_classifier.classify(question)
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 22 - Abandoned Carts")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_23_geographic_sales_distribution(self, intent_classifier, query_generator):
        """Scenario 23: Sales by geography"""
        question = "Which regions generate the most revenue?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 23 - Geographic Sales")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_24_discount_impact(self, intent_classifier, query_generator):
        """Scenario 24: Discount code effectiveness"""
        question = "How effective are my discount codes in driving sales?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['sales_trends', 'product_performance']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 24 - Discount Impact")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_25_refund_rate_analysis(self, intent_classifier, query_generator):
        """Scenario 25: Refund and return rates"""
        question = "What's my refund rate by product?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value in ['product_performance', 'sales_trends']
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 25 - Refund Rates")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    # Edge Cases (3 tests)
    
    def test_scenario_26_very_specific_date_range(self, intent_classifier, query_generator):
        """Scenario 26: Very specific date range"""
        question = "Show me sales between December 15th and December 20th, 2024"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 26 - Specific Date Range")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_27_multiple_filters(self, intent_classifier, query_generator):
        """Scenario 27: Multiple filters combined"""
        question = "Show me orders over $500 from repeat customers in California"
        
        intent_result = intent_classifier.classify(question)
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 27 - Multiple Filters")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")
    
    def test_scenario_28_comparison_with_benchmark(self, intent_classifier, query_generator):
        """Scenario 28: Comparison with industry benchmark"""
        question = "How do my sales compare to last year's same period?"
        
        intent_result = intent_classifier.classify(question)
        assert intent_result.type.value == 'sales_trends'
        
        query = query_generator.generate(intent_result)
        assert 'SELECT' in query.upper()
        
        print(f"\n✅ Scenario 28 - Year-over-Year Comparison")
        print(f"   Intent: {intent_result.type.value}")
        print(f"   Query: {query[:200]}...")


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Running Comprehensive Query Generation Test Suite")
    print("   Testing 28 different scenarios")
    print("=" * 80)
    pytest.main([__file__, "-v", "-s"])

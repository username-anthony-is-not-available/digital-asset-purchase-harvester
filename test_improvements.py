#!/usr/bin/env python3
"""
Test script for the improved Digital Asset Purchase Harvester
Tests the enhanced email processing capabilities
"""

import logging

from digital_asset_harvester.processing import EmailPurchaseExtractor

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_email_samples():
    """Test with various email samples to validate improvements."""
    
    extractor = EmailPurchaseExtractor()
    
    # Test emails covering different scenarios
    test_emails = [
        {
            "name": "Coinbase Purchase",
            "content": """Subject: Your Coinbase order is complete
From: no-reply@coinbase.com
Date: 2024-01-15 10:30:00
Body: Hi there, Your order to buy 0.001 BTC for $45.50 USD has been completed. 
Transaction ID: TX123456789
Order #: CB-ORDER-123
Date: January 15, 2024 at 10:30 AM UTC"""
        },
        {
            "name": "Binance Trade Confirmation", 
            "content": """Subject: Trade Confirmation - Order Filled
From: noreply@binance.com
Date: 2024-01-16 14:20:00
Body: Your buy order has been successfully executed.
Pair: ETH/USD
Side: Buy
Amount: 0.5 ETH
Price: $2,500.00
Total: $1,250.00
Order ID: BN789456123"""
        },
        {
            "name": "Newsletter (should be filtered)",
            "content": """Subject: Weekly Crypto Market Update
From: newsletter@cryptonews.com  
Date: 2024-01-17 09:00:00
Body: This week in cryptocurrency markets... Bitcoin reaches new highs.
Market analysis and trends. Subscribe to our newsletter for more updates."""
        },
        {
            "name": "Price Alert (should be filtered)",
            "content": """Subject: Bitcoin Price Alert - $50,000 reached
From: alerts@cointracker.com
Date: 2024-01-18 16:45:00
Body: Bitcoin has reached your target price of $50,000. 
Current price: $50,125. Set up more alerts in your dashboard."""
        },
        {
            "name": "Kraken Purchase Receipt",
            "content": """Subject: Purchase Receipt - Order #KRK-987654
From: receipts@kraken.com
Date: 2024-01-19 11:15:00
Body: Thank you for your purchase.
You bought: 2.0 LTC
For: $150.00 USD
Fee: $2.50 USD
Total charged: $152.50 USD
Transaction completed at: 2024-01-19 11:15:23 UTC"""
        }
    ]
    
    print("🚀 Testing Enhanced Email Processing System")
    print("=" * 60)
    
    results = []
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n📧 Test {i}: {email['name']}")
        print("-" * 40)
        
        result = extractor.process_email(email['content'])
        results.append({
            'name': email['name'],
            'result': result
        })
        
        if result['has_purchase']:
            print("✅ PURCHASE DETECTED")
            purchase_info = result['purchase_info']
            print(f"   Amount: {purchase_info.get('amount')} {purchase_info.get('item_name')}")
            print(f"   Cost: ${purchase_info.get('total_spent')} {purchase_info.get('currency')}")
            print(f"   Vendor: {purchase_info.get('vendor')}")
            print(f"   Date: {purchase_info.get('purchase_date')}")
        else:
            print("❌ NO PURCHASE DETECTED")
        
        # Show processing notes
        if 'processing_notes' in result and result['processing_notes']:
            print(f"   Notes: {', '.join(result['processing_notes'])}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY RESULTS")
    print("=" * 60)
    
    purchase_count = sum(1 for r in results if r['result']['has_purchase'])
    total_count = len(results)
    
    print(f"Total emails tested: {total_count}")
    print(f"Purchases detected: {purchase_count}")
    print(f"Non-purchases correctly filtered: {total_count - purchase_count}")
    
    # Expected results validation
    expected_purchases = ["Coinbase Purchase", "Binance Trade Confirmation", "Kraken Purchase Receipt"]
    expected_filtered = ["Newsletter (should be filtered)", "Price Alert (should be filtered)"]
    
    print("\n🎯 ACCURACY CHECK:")
    for result in results:
        expected = result['name'] in expected_purchases
        actual = result['result']['has_purchase']
        status = "✅" if expected == actual else "❌"
        print(f"{status} {result['name']}: Expected={expected}, Actual={actual}")


def test_preprocessing_speed():
    """Test the speed improvements from preprocessing."""
    import time
    
    extractor = EmailPurchaseExtractor()
    
    # Non-crypto email that should be quickly filtered
    non_crypto_email = """Subject: Your Amazon Order Has Shipped
From: shipment-tracking@amazon.com
Date: 2024-01-20 08:00:00
Body: Your order #123-4567890 has been shipped and is on its way.
Tracking number: 1Z999AA1234567890
Expected delivery: January 22, 2024"""
    
    print("\n⚡ Testing Preprocessing Speed")
    print("-" * 40)
    
    # Test preprocessing filter
    start_time = time.time()
    should_skip = extractor._should_skip_llm_analysis(non_crypto_email)
    preprocess_time = time.time() - start_time
    
    print(f"Preprocessing result: Should skip LLM = {should_skip}")
    print(f"Preprocessing time: {preprocess_time:.4f} seconds")
    
    if should_skip:
        print("✅ Successfully filtered non-crypto email before LLM analysis")
    else:
        print("❌ Failed to filter non-crypto email - will use LLM unnecessarily")


if __name__ == "__main__":
    try:
        test_email_samples()
        test_preprocessing_speed()
        print("\n🎉 All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise

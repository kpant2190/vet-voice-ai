#!/usr/bin/env python3
"""Speed test for AI receptionist endpoints."""

import requests
import time
import statistics

def test_endpoint_speed(endpoint, data, name):
    """Test the speed of an endpoint multiple times."""
    print(f"\n🚀 Testing {name} endpoint...")
    print(f"   URL: {endpoint}")
    
    times = []
    for i in range(5):
        start_time = time.time()
        try:
            response = requests.post(
                endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(response_time)
                print(f"   Test {i+1}: {response_time:.0f}ms ✅")
            else:
                print(f"   Test {i+1}: Error {response.status_code} ❌")
        except Exception as e:
            print(f"   Test {i+1}: Exception {str(e)[:50]} ❌")
    
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"📊 {name} Results:")
        print(f"   Average: {avg_time:.0f}ms")
        print(f"   Fastest: {min_time:.0f}ms")
        print(f"   Slowest: {max_time:.0f}ms")
        
        # Speed rating
        if avg_time < 200:
            rating = "🚀 LIGHTNING FAST"
        elif avg_time < 500:
            rating = "⚡ VERY FAST"
        elif avg_time < 1000:
            rating = "✅ FAST"
        else:
            rating = "🐌 NEEDS IMPROVEMENT"
        
        print(f"   Rating: {rating}")
        return avg_time
    else:
        print(f"❌ All tests failed for {name}")
        return None

def main():
    """Run speed tests on all endpoints."""
    base_url = "https://web-production-2b37.up.railway.app"
    
    test_data = {
        "SpeechResult": "appointment",
        "CallSid": "speed_test_123"
    }
    
    print("🏁 AI Receptionist Speed Test")
    print("=" * 50)
    
    # Test different endpoints
    endpoints = [
        ("/express", "EXPRESS (New Ultra-Fast)"),
        ("/speech", "SPEECH (Optimized)"),
        ("/speech-test", "SPEECH-TEST (Simple)")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        url = base_url + endpoint
        avg_time = test_endpoint_speed(url, test_data, name)
        if avg_time:
            results[name] = avg_time
    
    # Summary
    print("\n🏆 SPEED COMPARISON SUMMARY")
    print("=" * 50)
    
    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1])
        
        print("🥇 Fastest to Slowest:")
        for i, (name, time_ms) in enumerate(sorted_results, 1):
            medal = ["🥇", "🥈", "🥉"][min(i-1, 2)]
            print(f"   {medal} {name}: {time_ms:.0f}ms")
        
        fastest = sorted_results[0][1]
        print(f"\n⚡ Best response time: {fastest:.0f}ms")
        
        if fastest < 300:
            print("🎉 EXCELLENT! Your AI receptionist is responding super fast!")
        elif fastest < 600:
            print("👍 GOOD! Response time is quite fast for voice calls.")
        else:
            print("🔧 Could be faster - but still functional.")
    
    print(f"\n📞 Test your AI receptionist: +61468017757")
    print(f"🎯 Expected experience: Near-instant responses!")

if __name__ == "__main__":
    main()

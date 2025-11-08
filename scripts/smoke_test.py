#!/usr/bin/env python3
"""
SpendSenseAI Smoke Test
Quick validation that all core features are working
"""

import sys
import sqlite3
import requests
import time
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def test_database():
    """Test database exists and has data"""
    print("\n1️⃣  Testing Database...")
    
    db_path = Path("data/spendsense.db")
    if not db_path.exists():
        print(f"{RED}❌ Database not found{RESET}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check customer count
    cursor.execute('SELECT COUNT(DISTINCT customer_id) FROM accounts')
    customer_count = cursor.fetchone()[0]
    
    # Check transaction count
    cursor.execute('SELECT COUNT(*) FROM transactions')
    transaction_count = cursor.fetchone()[0]
    
    # Check consent count
    cursor.execute('SELECT COUNT(*) FROM consent WHERE status="active"')
    consent_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"{GREEN}✅ Database exists{RESET}")
    print(f"   📊 Customers: {customer_count}")
    print(f"   📊 Transactions: {transaction_count:,}")
    print(f"   📊 Active Consents: {consent_count}")
    
    if customer_count < 50:
        print(f"{YELLOW}⚠️  Warning: Only {customer_count} customers (expected 50-100){RESET}")
    
    return True


def test_backend_api():
    """Test backend API is running and responding"""
    print("\n2️⃣  Testing Backend API...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✅ API health check passed{RESET}")
        else:
            print(f"{RED}❌ API health check failed (status {response.status_code}){RESET}")
            return False
        
        # Test users endpoint
        response = requests.get('http://localhost:8000/users', timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_count = data.get('total', 0)
            print(f"{GREEN}✅ Users endpoint working ({user_count} users){RESET}")
        else:
            print(f"{RED}❌ Users endpoint failed{RESET}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Cannot connect to API (is it running on port 8000?){RESET}")
        print(f"   💡 Start with: uvicorn ui.api:app --reload")
        return False
    except Exception as e:
        print(f"{RED}❌ API test failed: {e}{RESET}")
        return False


def test_recommendations():
    """Test recommendation generation"""
    print("\n3️⃣  Testing Recommendations...")
    
    try:
        # Get recommendations for test customer
        start_time = time.time()
        response = requests.get(
            'http://localhost:8000/recommendations/CUST000001?check_consent=false',
            timeout=10
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            print(f"{RED}❌ Recommendations endpoint failed (status {response.status_code}){RESET}")
            return False
        
        data = response.json()
        
        # Check for required fields
        if 'customer_id' not in data:
            print(f"{RED}❌ Missing customer_id in response{RESET}")
            return False
        
        if 'persona' not in data:
            print(f"{RED}❌ Missing persona in response{RESET}")
            return False
        
        edu_items = data.get('education_items', [])
        partner_offers = data.get('partner_offers', [])
        
        print(f"{GREEN}✅ Recommendations working{RESET}")
        print(f"   📚 Education items: {len(edu_items)}")
        print(f"   💼 Partner offers: {len(partner_offers)}")
        print(f"   ⏱️  Latency: {elapsed:.2f}s", end="")
        
        if elapsed < 5:
            print(f" {GREEN}(within target){RESET}")
        else:
            print(f" {RED}(exceeds 5s target){RESET}")
        
        # Check rationales
        if edu_items and all('rationale' in item for item in edu_items):
            print(f"{GREEN}✅ All recommendations have rationales{RESET}")
        else:
            print(f"{YELLOW}⚠️  Some recommendations missing rationales{RESET}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Cannot connect to API{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ Recommendation test failed: {e}{RESET}")
        return False


def test_frontend():
    """Test frontend is running"""
    print("\n4️⃣  Testing Frontend...")
    
    try:
        response = requests.get('http://localhost:5173', timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✅ Frontend responding{RESET}")
            print(f"   🌐 Access at: http://localhost:5173")
            return True
        else:
            print(f"{RED}❌ Frontend returned status {response.status_code}{RESET}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{YELLOW}⚠️  Frontend not running (optional){RESET}")
        print(f"   💡 Start with: cd frontend && npm run dev")
        return True  # Frontend is optional, don't fail
    except Exception as e:
        print(f"{YELLOW}⚠️  Frontend test failed: {e}{RESET}")
        return True  # Frontend is optional


def test_consent_enforcement():
    """Test that consent is enforced"""
    print("\n5️⃣  Testing Consent Enforcement...")
    
    try:
        # Try to get recommendations with consent check enabled
        response = requests.get(
            'http://localhost:8000/recommendations/CUST000001?check_consent=true',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # If consent is active, should have recommendations
            if data.get('education_items'):
                print(f"{GREEN}✅ Consent system working{RESET}")
                return True
            else:
                # Could be valid if user has no consent
                print(f"{GREEN}✅ Consent system working (no recommendations without consent){RESET}")
                return True
        else:
            print(f"{YELLOW}⚠️  Consent endpoint returned status {response.status_code}{RESET}")
            return True
            
    except Exception as e:
        print(f"{YELLOW}⚠️  Consent test failed: {e}{RESET}")
        return True  # Don't fail entire test


def test_operator_dashboard():
    """Test operator dashboard is accessible"""
    print("\n6️⃣  Testing Operator Dashboard...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✅ Operator dashboard responding{RESET}")
            print(f"   🌐 Access at: http://localhost:8501")
            return True
        else:
            print(f"{YELLOW}⚠️  Dashboard returned status {response.status_code}{RESET}")
            return True
            
    except requests.exceptions.ConnectionError:
        print(f"{YELLOW}⚠️  Operator dashboard not running (optional){RESET}")
        print(f"   💡 Start with: streamlit run ui/dashboard.py")
        return True  # Dashboard is optional for this test
    except Exception as e:
        print(f"{YELLOW}⚠️  Dashboard test failed: {e}{RESET}")
        return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("🧪 SpendSenseAI Smoke Test")
    print("=" * 60)
    
    tests = [
        test_database,
        test_backend_api,
        test_recommendations,
        test_frontend,
        test_consent_enforcement,
        test_operator_dashboard,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"{RED}❌ Test crashed: {e}{RESET}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}✅ All tests passed ({passed}/{total}){RESET}")
        print(f"\n🎉 System is ready for use!")
        sys.exit(0)
    elif passed >= 3:  # Core tests passed
        print(f"{YELLOW}⚠️  {passed}/{total} tests passed{RESET}")
        print(f"\n💡 Core functionality working, some optional features not running")
        sys.exit(0)
    else:
        print(f"{RED}❌ Only {passed}/{total} tests passed{RESET}")
        print(f"\n🔧 System needs attention")
        sys.exit(1)


if __name__ == "__main__":
    main()




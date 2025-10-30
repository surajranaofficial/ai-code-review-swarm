#!/usr/bin/env python3
"""
Test script for AI Code Review Swarm API
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_result(title: str, data: Any):
    """Pretty print results"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    print(json.dumps(data, indent=2))


def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✅ Health check passed!")
        print_result("Health Status", response.json())
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False


def test_review(code: str, language: str = "python") -> str:
    """Submit code for review"""
    print(f"\n🔍 Submitting code review...")
    
    payload = {
        "submission": {
            "code": code,
            "language": language,
            "filename": f"test.{language}"
        },
        "agents": ["security", "performance", "quality"],
        "use_hybrid_search": True
    }
    
    response = requests.post(
        f"{BASE_URL}/review",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        review_id = data.get("review_id")
        print(f"✅ Review created: {review_id}")
        print_result("Review Created", data)
        return review_id
    else:
        print(f"❌ Review submission failed: {response.status_code}")
        print(response.text)
        return None


def get_review_status(review_id: str, wait: bool = True) -> Dict:
    """Get review results"""
    print(f"\n📊 Getting review results for {review_id}...")
    
    if wait:
        print("⏳ Waiting for agents to complete (15 seconds)...")
        time.sleep(15)
    
    response = requests.get(f"{BASE_URL}/review/{review_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        total_issues = data.get("total_issues", 0)
        
        print(f"Status: {status}")
        print(f"Issues found: {total_issues}")
        
        if status == "completed":
            print("\n✅ Review completed!")
            
            # Show agent results
            for result in data.get("results", []):
                agent_type = result.get("agent_type")
                agent_status = result.get("status")
                issues_count = len(result.get("issues", []))
                exec_time = result.get("execution_time", 0)
                
                print(f"\n  🤖 {agent_type.upper()} Agent:")
                print(f"     Status: {agent_status}")
                print(f"     Issues: {issues_count}")
                print(f"     Time: {exec_time:.2f}s")
                
                # Show issues
                for i, issue in enumerate(result.get("issues", [])[:3], 1):
                    print(f"\n     Issue #{i}:")
                    print(f"       Severity: {issue.get('severity')}")
                    print(f"       Title: {issue.get('title')}")
                    print(f"       Description: {issue.get('description')[:100]}...")
        
        print_result("Full Results", data)
        return data
    else:
        print(f"❌ Failed to get review: {response.status_code}")
        return None


def test_stats():
    """Get system statistics"""
    print("\n📈 Getting system statistics...")
    
    response = requests.get(f"{BASE_URL}/stats")
    
    if response.status_code == 200:
        print("✅ Stats retrieved!")
        print_result("System Statistics", response.json())
    else:
        print(f"❌ Failed to get stats: {response.status_code}")


# Test cases
TEST_CASES = {
    "sql_injection": {
        "code": """
def get_user(username):
    query = "SELECT * FROM users WHERE username='" + username + "'"
    return db.execute(query)
        """,
        "language": "python"
    },
    
    "performance_issue": {
        "code": """
def process_users(user_ids):
    results = []
    for user_id in user_ids:
        user = db.query("SELECT * FROM users WHERE id=" + str(user_id))
        results.append(user)
    return results
        """,
        "language": "python"
    },
    
    "quality_issue": {
        "code": """
def x(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
            else:
                return a + b
        else:
            return a
    return 0
        """,
        "language": "python"
    }
}


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  🐅 AI Code Review Swarm - API Test Suite")
    print("="*60)
    
    # Test health
    if not test_health():
        print("\n❌ Server not healthy. Exiting.")
        return
    
    # Test each case
    for name, test_case in TEST_CASES.items():
        print(f"\n\n{'#'*60}")
        print(f"  Testing: {name.upper()}")
        print('#'*60)
        
        review_id = test_review(
            code=test_case["code"],
            language=test_case["language"]
        )
        
        if review_id:
            get_review_status(review_id, wait=True)
        
        # Small delay between tests
        time.sleep(2)
    
    # Get final stats
    test_stats()
    
    print("\n\n" + "="*60)
    print("  ✅ All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Is it running?")
        print("   Start with: python app/main.py")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

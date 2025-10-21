import requests
import time
import sys

# Give the container a moment to start up
time.sleep(10)

# The base URL for our canary service
BASE_URL = "http://localhost:8080"

# --- Golden Set of Queries ---


# Test 1: Health Check
def test_health_check():
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {
        "status": "ok"
    }, f"Expected {{'status': 'ok'}}, got {response.json()}"
    print("Health check PASSED.")


# Test 2: Root endpoint
def test_root_endpoint():
    print("Testing / endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert (
        "message" in response.json()
    ), "Root endpoint response should contain a message"
    print("Root endpoint PASSED.")


# --- Run All Tests ---
try:
    test_health_check()
    test_root_endpoint()
    # Add 3+ more simple tests here if you create more endpoints
    print("\n✅ All acceptance tests passed!")
    sys.exit(0)
except AssertionError as e:
    print(f"\n❌ Acceptance test FAILED: {e}")
    sys.exit(1)

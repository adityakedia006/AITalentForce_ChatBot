"""
Test script to verify frontend-backend connectivity
Run this to diagnose connection issues
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🔍 Testing Backend Connection")
print("=" * 60)

# Test 1: Health Check
print("\n1️⃣ Testing /health endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("   ✅ Health check passed")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ❌ Connection Error - Backend is not running!")
    print("\n💡 Solution: Start the backend with:")
    print("   python main.py")
    exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: API Info
print("\n2️⃣ Testing /api/info endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/api/info", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("   ✅ API info retrieved")
        print(f"   Available endpoints: {list(data.get('endpoints', {}).keys())}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check if /api/assist exists
print("\n3️⃣ Testing /api/assist endpoint...")
try:
    response = requests.post(
        f"{API_BASE_URL}/api/assist",
        data={"message": "test"},
        timeout=10
    )
    if response.status_code == 200:
        print("   ✅ /api/assist endpoint is working!")
        result = response.json()
        print(f"   Response type: {result.get('input_type')}")
        print(f"   AI Response: {result.get('response')[:100]}...")
    elif response.status_code == 404:
        print("   ❌ /api/assist endpoint NOT FOUND")
        print("   💡 The endpoint is not registered. Check main.py")
    else:
        print(f"   ⚠️  Endpoint exists but returned status {response.status_code}")
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Chat endpoint (fallback)
print("\n4️⃣ Testing /api/chat endpoint (fallback)...")
try:
    response = requests.post(
        f"{API_BASE_URL}/api/chat",
        json={"message": "test", "conversation_history": []},
        timeout=10
    )
    if response.status_code == 200:
        print("   ✅ /api/chat endpoint is working!")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("📊 Summary")
print("=" * 60)

# Final check
try:
    health = requests.get(f"{API_BASE_URL}/health", timeout=5)
    assist = requests.post(f"{API_BASE_URL}/api/assist", data={"message": "test"}, timeout=10)
    
    if health.status_code == 200 and assist.status_code == 200:
        print("✅ All systems operational!")
        print("✅ Frontend should connect successfully")
        print("\n💡 If Streamlit still shows errors:")
        print("   1. Refresh the Streamlit page (Ctrl+R)")
        print("   2. Click 'Rerun' button in Streamlit")
        print("   3. Check browser console for errors (F12)")
    elif health.status_code == 200 and assist.status_code == 404:
        print("⚠️  Backend is running but /api/assist is missing")
        print("\n💡 Fix:")
        print("   1. Stop the backend (Ctrl+C)")
        print("   2. Make sure main.py has the @app.post('/api/assist') endpoint")
        print("   3. Restart: python main.py")
    else:
        print("⚠️  Some endpoints are not working correctly")
        print("   Check the errors above for details")
except Exception as e:
    print(f"❌ Connection test failed: {e}")

print("=" * 60)

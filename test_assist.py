"""Quick test for /api/assist endpoint"""
import requests

try:
    # Test text input
    response = requests.post(
        "http://localhost:8000/api/assist",
        data={"message": "Hello, how are you?"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

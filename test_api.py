"""
Test script for Voice-Enabled Chatbot API endpoints
Run this while the FastAPI server is running on http://localhost:8000
"""

import requests
import json


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("\n" + "="*50)
    print("Testing Health Check Endpoint")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_api_info():
    """Test API info endpoint"""
    print("\n" + "="*50)
    print("Testing API Info Endpoint")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/api/info")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_weather(location="London"):
    """Test weather endpoint"""
    print("\n" + "="*50)
    print(f"Testing Weather Endpoint - Location: {location}")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/api/weather", params={"location": location})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_chat(message="Hello, how are you?"):
    """Test chat endpoint"""
    print("\n" + "="*50)
    print(f"Testing Chat Endpoint - Message: {message}")
    print("="*50)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": message,
            "conversation_history": []
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_chat_with_weather():
    """Test chat endpoint with weather query"""
    print("\n" + "="*50)
    print("Testing Chat with Weather Query")
    print("="*50)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "What's the weather like in Jodhpur, India?",
            "conversation_history": []
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_chat_conversation():
    """Test chat endpoint with conversation history"""
    print("\n" + "="*50)
    print("Testing Chat with Conversation History")
    print("="*50)
    
    # First message
    response1 = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "My name is Alex",
            "conversation_history": []
        }
    )
    
    if response1.status_code != 200:
        print(f"❌ First request failed: {response1.json()}")
        return False
        
    history = response1.json()["conversation_history"]
    print(f"First Response: {response1.json()['response']}")
    
    # Second message with history
    response2 = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "What's my name?",
            "conversation_history": history
        }
    )
    
    if response2.status_code == 200:
        print(f"Second Response: {response2.json()['response']}")
    print(f"Status Code: {response2.status_code}")
    return response2.status_code == 200


def test_speech_to_text(audio_file_path=None):
    """Test speech-to-text endpoint (requires audio file)"""
    print("\n" + "="*50)
    print("Testing Speech-to-Text Endpoint")
    print("="*50)
    
    if not audio_file_path:
        print("⚠️  Skipped: No audio file provided")
        print("To test this endpoint, run:")
        print("  test_speech_to_text('path/to/your/audio.wav')")
        return False


def test_text_to_speech(text: str = "This is a test of ElevenLabs text to speech."):
    print("\n" + "="*50)
    print("Testing Text-to-Speech Endpoint")
    print("="*50)

    try:
        response = requests.post(
            f"{BASE_URL}/api/text-to-speech",
            headers={"Content-Type": "application/json"},
            json={"text": text}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            try:
                print(f"Response: {response.json()}")
            except Exception:
                print(f"Response (raw): {response.text}")
            return False

        content_type = response.headers.get("Content-Type", "")
        print(f"Content-Type: {content_type}")
        audio_path = "D:/chat/tts_test.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        print(f"Saved audio to {audio_path}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio_file': audio_file}
            response = requests.post(f"{BASE_URL}/api/speech-to-text", files=files)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code == 200
    except FileNotFoundError:
        print(f"❌ Error: Audio file not found at {audio_file_path}")
        return False


def run_all_tests():
    """Run all API tests"""
    print("\n" + "🚀 "*25)
    print("Starting API Tests")
    print("🚀 "*25)
    
    results = {
        "Health Check": test_health(),
        "Weather Query Chat": test_chat_with_weather(),
        "Conversation History": test_chat_conversation(),
        "Speech-to-Text": test_speech_to_text("D:\\chat\\japan.wav"),
        "Text-to-Speech": test_text_to_speech()
    }
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "⚠️  SKIPPED/FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len([k for k, v in results.items() if k not in ("Speech-to-Text", "Text-to-Speech")])
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print("\n" + "="*50)


if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("\nStart the server with:")
        print("  python main.py")
        print("  or")
        print("  uvicorn main:app --reload")

"""Test script for Groq tool use implementation."""
import asyncio
from services.llm_service import LLMService
from services.weather_service import WeatherService


async def test_tool_use():
    """Test the LLM's ability to use weather tools."""
    
    # Initialize services
    weather_service = WeatherService()
    llm_service = LLMService(weather_service=weather_service)
    
    # Test cases
    test_queries = [
        "What should I wear in Tokyo today?",
        "I'm going to New York. What's the weather like?",
        "こんにちは。東京の天気はどうですか？",  # Japanese: Hello. How's the weather in Tokyo?
        "What outfit would you recommend for Delhi right now?",
        "Tell me a joke about programming"  # Non-weather query
    ]
    
    print("🧪 Testing Groq Tool Use Implementation\n")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 70)
        
        try:
            result = await llm_service.chat_completion(
                user_message=query,
                conversation_history=[]
            )
            
            print(f"✅ Response: {result['response']}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 70)
    
    print("\n✨ Testing complete!")


if __name__ == "__main__":
    asyncio.run(test_tool_use())

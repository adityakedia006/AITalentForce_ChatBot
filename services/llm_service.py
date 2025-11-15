from groq import Groq
from typing import List, Dict, Optional
import json
from config import get_settings
from models import ChatMessage


class LLMService:
    """Service for LLM chat completions using Groq API."""
    
    def __init__(self, weather_service=None):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.GROQ_API_KEY)
        self.model = self.settings.LLM_MODEL
        self.system_prompt = self.settings.LLM_SYSTEM_PROMPT
        self.weather_service = weather_service
    
    def _get_weather_tool_definition(self) -> Dict:
        """Get the weather tool definition for Groq API."""
        return {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for any location. Use this when users ask about weather, temperature, or climate conditions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city or location name (e.g., 'Tokyo', 'New York', 'London', 'Delhi')"
                        }
                    },
                    "required": ["location"]
                }
            }
        }

    async def chat_completion(
        self,
        user_message: str,
        conversation_history: List[ChatMessage] = None,
        weather_context: str = None,
        system_prompt_override: str = None
    ) -> Dict[str, any]:
        """
        Generate a chat completion using Groq API with tool use support.
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            weather_context: Optional weather information (deprecated, tools are used instead)
            system_prompt_override: Optional system prompt override
            
        Returns:
            Dictionary with response and updated conversation history
            
        Raises:
            Exception: If chat completion fails
        """
        try:
            # Initialize conversation history if not provided
            if conversation_history is None:
                conversation_history = []
            
            # Build messages array
            active_system_prompt = (system_prompt_override or self.system_prompt).strip()

            # Language behavior: restrict outputs to English/Japanese only
            if getattr(self.settings, "LLM_FORCE_ENGLISH", False):
                if "always respond in english" not in active_system_prompt.lower():
                    active_system_prompt += (
                        "\n\nIMPORTANT: Always respond in English with proper grammar and complete sentences."
                    )
            else:
                policy_hint = (
                    "Use the same language as the user. "
                    "If they write in Japanese, respond in Japanese. "
                    "If they write in English, respond in English. "
                    "Use proper grammar, complete sentences, and natural formatting."
                )
                # Avoid duplicating policy if user provided override already contains it
                if "use the same language" not in active_system_prompt.lower():
                    active_system_prompt += f"\n\n{policy_hint}"
            
            messages = [{"role": "system", "content": active_system_prompt}]
            
            # Add conversation history
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Define tools (only if weather_service is available)
            tools = None
            if self.weather_service:
                tools = [self._get_weather_tool_definition()]
            
            # Call Groq API with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Handle tool calls if any
            if tool_calls and self.weather_service:
                # Add the assistant's response with tool calls to messages
                messages.append(response_message)
                
                # Process each tool call
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "get_weather":
                        try:
                            # Call the weather service
                            location = function_args.get("location")
                            weather_data = await self.weather_service.get_weather(location)
                            tool_response = self.weather_service.format_weather_for_llm(weather_data)
                        except Exception as e:
                            tool_response = f"Error fetching weather: {str(e)}"
                        
                        # Add tool response to messages
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_response
                        })
                
                # Make second API call with tool results
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=1,
                    stream=False
                )
                
                assistant_message = second_response.choices[0].message.content
            else:
                # No tool calls, use direct response
                assistant_message = response_message.content
            
            # Update conversation history
            updated_history = conversation_history + [
                ChatMessage(role="user", content=user_message),
                ChatMessage(role="assistant", content=assistant_message)
            ]
            
            # Keep only last 10 messages to manage context length
            if len(updated_history) > 10:
                updated_history = updated_history[-10:]
            
            return {
                "response": assistant_message,
                "conversation_history": updated_history
            }
            
        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")

    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language ('en' or 'ja') using Groq.
        Returns only the translated text.
        """
        try:
            if target_lang not in ("en", "ja"):
                raise ValueError("target_lang must be 'en' or 'ja'")

            system = (
                "You are a precise translator. Translate the user's text to "
                + ("English" if target_lang == "en" else "Japanese")
                + ". Preserve meaning and tone. Return only the translated text without explanations."
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=1024,
                top_p=1,
                stream=False,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Groq models.
        
        Returns:
            List of model names
        """
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"  # deprecated
        ]

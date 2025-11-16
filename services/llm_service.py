from groq import Groq
from typing import List, Dict, Optional
import json
from config import get_settings
from models import ChatMessage


class LLMService:
    
    def __init__(self, weather_service=None):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.GROQ_API_KEY)
        self.model = self.settings.LLM_MODEL
        self.system_prompt = self.settings.LLM_SYSTEM_PROMPT
        self.weather_service = weather_service
    
    def _get_weather_tool_definition(self) -> Dict:
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
        system_prompt_override: str = None,
        per_turn_instruction: Optional[str] = None
    ) -> Dict[str, any]:
        try:
            if conversation_history is None:
                conversation_history = []
            
            active_system_prompt = (system_prompt_override or self.system_prompt).strip()

            if getattr(self.settings, "LLM_FORCE_ENGLISH", False):
                if "always respond in english" not in active_system_prompt.lower():
                    active_system_prompt += (
                        "\n\nIMPORTANT: Always respond in English with proper grammar and complete sentences."
                    )
            else:
                policy_hint = (
                    "Use same language as the user."
                    "If user write in Japanese, respond in Japanese. "
                    "If user write in English then respond in English. "
                    "Use proper grammar, complete sentences, and natural formatting."
                )
                if "use the same language" not in active_system_prompt.lower():
                    active_system_prompt += f"\n\n{policy_hint}"
            
            messages = [{"role": "system", "content": active_system_prompt}]

            if per_turn_instruction and per_turn_instruction.strip():
                messages.append({"role": "system", "content": per_turn_instruction.strip()})
            
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            tools = None
            if self.weather_service:
                tools = [self._get_weather_tool_definition()]
            
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
            
            if tool_calls and self.weather_service:
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "get_weather":
                        try:
                            location = function_args.get("location")
                            weather_data = await self.weather_service.get_weather(location)
                            tool_response = self.weather_service.format_weather_for_llm(weather_data)
                        except Exception as e:
                            tool_response = f"Error fetching weather: {str(e)}"
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_response
                        })
                
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
                assistant_message = response_message.content
            
            updated_history = conversation_history + [
                ChatMessage(role="user", content=user_message),
                ChatMessage(role="assistant", content=assistant_message)
            ]
            
            if len(updated_history) > 11:
                updated_history = updated_history[-11:]
            
            return {
                "response": assistant_message,
                "conversation_history": updated_history
            }
            
        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")

    async def translate_text(self, text: str, target_lang: str) -> str:
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
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]

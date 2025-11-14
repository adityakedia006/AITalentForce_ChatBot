from groq import Groq
from typing import List, Dict
from config import get_settings
from models import ChatMessage


class LLMService:
    """Service for LLM chat completions using Groq API."""
    
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
        self.system_prompt = settings.LLM_SYSTEM_PROMPT
    
    async def chat_completion(
        self,
        user_message: str,
        conversation_history: List[ChatMessage] = None,
        weather_context: str = None,
        system_prompt_override: str = None
    ) -> Dict[str, any]:
        """
        Generate a chat completion using Groq API.
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            weather_context: Optional weather information to include in context
            
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
            active_system_prompt = system_prompt_override or self.system_prompt
            messages = [{"role": "system", "content": active_system_prompt}]
            
            # Add conversation history
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add weather context if provided
            current_user_message = user_message
            if weather_context:
                current_user_message = f"{user_message}\n\n[Weather Information: {weather_context}]"
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": current_user_message
            })
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False
            )
            
            # Extract assistant's response
            assistant_message = response.choices[0].message.content
            
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

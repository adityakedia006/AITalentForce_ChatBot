from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Role of the message sender (user/assistant/system)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message")
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Override default system prompt/context for this request"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Assistant's response")
    conversation_history: List[ChatMessage] = Field(..., description="Updated conversation history")


class VoiceChatResponse(BaseModel):
    """Response model for voice chat endpoint."""
    transcribed_text: str = Field(..., description="Transcribed user speech")
    response: str = Field(..., description="Assistant's response")
    conversation_history: List[ChatMessage] = Field(..., description="Updated conversation history")


class AssistResponse(BaseModel):
    """Unified assist response for either text or audio input."""
    input_type: str = Field(..., description="Type of user input: 'text' or 'audio'")
    transcribed_text: Optional[str] = Field(None, description="Transcribed text if audio was provided")
    response: str = Field(..., description="Assistant's response")
    conversation_history: List[ChatMessage] = Field(..., description="Updated conversation history")


class WeatherRequest(BaseModel):
    """Request model for weather endpoint."""
    location: str = Field(..., description="Location name (city, country)")


class WeatherResponse(BaseModel):
    """Response model for weather endpoint."""
    location: str = Field(..., description="Location name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    temperature: float = Field(..., description="Current temperature in Celsius")
    weather_code: int = Field(..., description="WMO weather code")
    weather_description: str = Field(..., description="Human-readable weather description")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    humidity: Optional[float] = Field(None, description="Relative humidity percentage")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")


class TranslateRequest(BaseModel):
    """Request model for translate endpoint."""
    text: str = Field(..., description="Text to translate")
    target_lang: str = Field(..., description="Target language code: 'en' or 'ja'")


class TranslateResponse(BaseModel):
    """Response model for translate endpoint."""
    translated_text: str = Field(..., description="Translated text output")

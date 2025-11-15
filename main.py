from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import json
from typing import Optional

from config import get_settings
from models import (
    ChatRequest, ChatResponse, SpeechToTextResponse,
    VoiceChatResponse, WeatherResponse, HealthResponse,
    ChatMessage, AssistResponse, TranslateRequest, TranslateResponse
)
from services import SpeechService, LLMService, WeatherService


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Voice-Enabled Chatbot Backend...")
    print(f"📊 LLM Model: {settings.LLM_MODEL}")
    print(f"🎤 Speech Model: {settings.ELEVENLABS_MODEL}")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title="Voice-Enabled Chatbot API",
    description="FastAPI backend for multilingual voice chatbot with Groq LLM and ElevenLabs",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
speech_service = SpeechService()
llm_service = LLMService()
weather_service = WeatherService()


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - returns API status."""
    return {
        "status": "online",
        "message": "Voice-Enabled Chatbot API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "All systems operational"
    }


@app.post("/api/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Convert speech to text using ElevenLabs API.
    
    Args:
        audio_file: Audio file upload (supports multiple formats)
        
    Returns:
        Transcribed text
    """
    try:
        # Read audio file
        print(f"/api/speech-to-text: received file name={audio_file.filename}, content_type={audio_file.content_type}")
        audio_data = await audio_file.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Transcribe audio (preserve original content type and filename)
        transcribed_text = await speech_service.transcribe_audio(
            audio_data,
            mime_type=getattr(audio_file, "content_type", None),
            filename=getattr(audio_file, "filename", None)
        )
        
        return {"text": transcribed_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI assistant.
    
    Args:
        request: Chat request with message and optional conversation history
        
    Returns:
        Assistant's response and updated conversation history
    """
    try:
        # Check if message contains weather-related query
        weather_context = None
        weather_keywords = ["weather", "temperature", "forecast", "climate", "rain", "sunny", "cloudy"]
        
        if any(keyword in request.message.lower() for keyword in weather_keywords):
            # Try to extract location from message
            # Simple approach - you can enhance this with NER
            try:
                # For demo, attempt to get weather if location seems present
                # This is a simple heuristic - in production, use NLP/NER
                words = request.message.split()
                
                # Look for "in [location]" or "at [location]" patterns
                for i, word in enumerate(words):
                    if word.lower() in ["in", "at", "for"] and i + 1 < len(words):
                        potential_location = " ".join(words[i+1:i+3])  # Get next 1-2 words
                        potential_location = potential_location.rstrip("?.,!;")
                        
                        try:
                            weather_data = await weather_service.get_weather(potential_location)
                            weather_context = weather_service.format_weather_for_llm(weather_data)
                            break
                        except:
                            continue
            except:
                pass
        
        # Generate chat completion
        result = await llm_service.chat_completion(
            user_message=request.message,
            conversation_history=request.conversation_history,
            weather_context=weather_context,
            system_prompt_override=request.system_prompt
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@app.get("/api/weather", response_model=WeatherResponse)
async def get_weather(location: str = Query(..., description="Location name (e.g., 'London', 'New York')")):
    """
    Get current weather for a location.
    
    Args:
        location: Location name (city, country)
        
    Returns:
        Current weather data
    """
    try:
        weather_data = await weather_service.get_weather(location)
        return weather_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {str(e)}")


@app.post("/api/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio_file: UploadFile = File(...),
    conversation_history: Optional[str] = None,
    system_prompt: Optional[str] = Form(None)
):
    """
    Complete voice chat flow: speech-to-text → chat completion.
    
    Args:
        audio_file: Audio file upload
        conversation_history: JSON string of previous messages (optional)
        
    Returns:
        Transcribed text, assistant's response, and updated history
    """
    try:
        # Parse conversation history if provided
        history = []
        if conversation_history:
            try:
                history_data = json.loads(conversation_history)
                history = [ChatMessage(**msg) for msg in history_data]
            except:
                pass  # Use empty history if parsing fails
        
        # Step 1: Transcribe audio
        print(f"/api/voice-chat: received file name={audio_file.filename}, content_type={audio_file.content_type}")
        audio_data = await audio_file.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        transcribed_text = await speech_service.transcribe_audio(
            audio_data,
            mime_type=getattr(audio_file, "content_type", None),
            filename=getattr(audio_file, "filename", None)
        )
        
        # Step 2: Get chat response
        result = await llm_service.chat_completion(
            user_message=transcribed_text,
            conversation_history=history,
            system_prompt_override=system_prompt
        )
        
        return {
            "transcribed_text": transcribed_text,
            "response": result["response"],
            "conversation_history": result["conversation_history"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")


@app.post("/api/assist", response_model=AssistResponse)
async def assist(
    message: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    conversation_history: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None)
):
    """Unified endpoint: accepts either text message or audio file and returns LLM response.
    If both are provided, audio is transcribed and appended after the text message.
    """
    try:
        history = []
        if conversation_history:
            try:
                history_data = json.loads(conversation_history)
                history = [ChatMessage(**msg) for msg in history_data]
            except:
                pass

        transcribed_text = None
        combined_message = message or ""

        if audio_file:
            print(f"/api/assist: received file name={audio_file.filename}, content_type={audio_file.content_type}")
            audio_data = await audio_file.read()
            if not audio_data:
                raise HTTPException(status_code=400, detail="Empty audio file")
            transcribed_text = await speech_service.transcribe_audio(
                audio_data,
                mime_type=getattr(audio_file, "content_type", None),
                filename=getattr(audio_file, "filename", None)
            )
            if combined_message:
                combined_message = f"{combined_message}\n\n[Audio: {transcribed_text}]"
            else:
                combined_message = transcribed_text

        if not combined_message:
            raise HTTPException(status_code=400, detail="Provide either 'message' or 'audio_file'")

        result = await llm_service.chat_completion(
            user_message=combined_message,
            conversation_history=history,
            system_prompt_override=system_prompt
        )

        return {
            "input_type": "audio" if audio_file else "text",
            "transcribed_text": transcribed_text,
            "response": result["response"],
            "conversation_history": result["conversation_history"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assist pipeline failed: {str(e)}")


@app.get("/api/info")
async def get_info():
    """Get API information and supported features."""
    return {
        "name": "Voice-Enabled Chatbot API",
        "version": "1.0.0",
        "features": {
            "speech_to_text": {
                "provider": "ElevenLabs",
                "model": settings.ELEVENLABS_MODEL,
                "supported_languages": speech_service.get_supported_languages()
            },
            "llm": {
                "provider": "Groq",
                "model": settings.LLM_MODEL,
                "available_models": llm_service.get_available_models()
            },
            "weather": {
                "provider": "Open-Meteo",
                "features": ["current weather", "geocoding"]
            }
        },
        "endpoints": {
            "/api/speech-to-text": "Convert audio to text",
            "/api/chat": "Chat with AI assistant",
            "/api/weather": "Get weather information",
            "/api/voice-chat": "Complete voice chat flow",
            "/api/assist": "Unified text or audio input pipeline",
            "/api/translate": "Translate arbitrary text between English and Japanese"
        }
    }


@app.post("/api/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """Translate text between English and Japanese using LLMService."""
    try:
        translated = await llm_service.translate_text(request.text, request.target_lang)
        return {"translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

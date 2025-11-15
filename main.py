from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import io
import uvicorn
import json
from typing import Optional
import re

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
    print(f"🔊 TTS Model (ElevenLabs): {settings.ELEVENLABS_TTS_MODEL}")
    print(f"🔊 TTS Voice (ElevenLabs): {settings.ELEVENLABS_VOICE_ID}")
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


# --- Weather intent and location extraction (EN + JA) ---
JP_LOC_CHARS = r"[A-Za-z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFFー]+"
WEATHER_KEYWORDS_EN = [
    "weather", "temperature", "temp", "forecast", "climate", "rain", "sunny", "cloudy",
    "degree", "degrees", "wind", "windy", "snow", "snowy", "humidity", "hot", "cold"
]
WEATHER_KEYWORDS_JA = [
    "天気", "気温", "温度", "予報", "雨", "晴れ", "曇り", "風", "風速", "湿度", "暑い", "寒い", "雪"
]

def _maybe_extract_location(msg: str) -> Optional[str]:
    text = msg.strip()
    lowered = text.lower()
    # Quick intent check to avoid unnecessary regex/geocoding calls
    if not (any(k in lowered for k in WEATHER_KEYWORDS_EN) or any(k in text for k in WEATHER_KEYWORDS_JA)):
        return None

    # 1) English pattern: in/at/for <one|two words>
    m_en = re.search(rf"\b(?:in|at|for)\s+({JP_LOC_CHARS}(?:\s+{JP_LOC_CHARS})?)", text, flags=re.IGNORECASE)
    if m_en:
        return m_en.group(1).strip().rstrip("?.!,;")

    # 2) Japanese pattern: <LOC>(の|で|は)?(天気|気温|予報|雨|晴れ|曇り)
    m_ja1 = re.search(rf"({JP_LOC_CHARS})\s*(?:の|で|は)?\s*(?:天気|気温|予報|雨|晴れ|曇り)", text)
    if m_ja1:
        return m_ja1.group(1).strip().rstrip("？?。．.,!;」』])")

    # 3) Japanese pattern: (天気|...) は/って? <LOC>
    m_ja2 = re.search(rf"(?:天気|気温|予報|雨|晴れ|曇り)\s*(?:は|って)?\s*({JP_LOC_CHARS})", text)
    if m_ja2:
        return m_ja2.group(1).strip().rstrip("？?。．.,!;」』])")

    return None

async def build_weather_context(message: str) -> Optional[str]:
    try:
        loc = _maybe_extract_location(message)
        if not loc:
            return None
        weather_data = await weather_service.get_weather(loc)
        return weather_service.format_weather_for_llm(weather_data)
    except Exception:
        return None


# --- Simple language detection and normalization helpers ---
def _detect_lang_simple(text: str) -> str:
    """Very lightweight language detection for EN/JA vs other.
    - Returns 'ja' if any Japanese scripts are present (Hiragana/Katakana/Kanji)
    - Returns 'en' if ASCII letters are present and no Japanese scripts
    - Returns 'other' otherwise (e.g., Devanagari, Cyrillic, etc.)
    """
    if not text:
        return "en"

    has_ja = any(
        ('\u3040' <= ch <= '\u309F')  # Hiragana
        or ('\u30A0' <= ch <= '\u30FF')  # Katakana
        or ('\u4E00' <= ch <= '\u9FFF')  # CJK Unified Ideographs (Kanji)
        for ch in text
    )
    if has_ja:
        return "ja"

    has_en = any(('a' <= ch.lower() <= 'z') for ch in text)
    if has_en:
        return "en"

    return "other"


async def _normalize_to_allowed_langs(text: str) -> str:
    """Ensure text is in EN or JA only. If it's another language, translate to EN.
    Uses LLMService.translate_text for normalization when needed.
    """
    lang = _detect_lang_simple(text)
    if lang in ("en", "ja"):
        return text
    try:
        # Default normalization target: English
        translated = await llm_service.translate_text(text, "en")
        return translated or text
    except Exception:
        # On failure, return original text to avoid breaking the flow
        return text


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
        # Try to build weather context from message (EN/JA)
        weather_context = await build_weather_context(request.message)

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


@app.post("/api/text-to-speech")
async def text_to_speech(request: Request, text: str = Form(None)):
    """
    Convert text to speech using Deepgram TTS.

    Accepts either JSON body {"text": "...", "model": "...", "encoding": "mp3", "container": "mp3"}
    or form field 'text'.
    Returns audio bytes with appropriate content-type.
    """
    try:
        payload = None
        # Try JSON body first
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                payload = await request.json()
        except Exception:
            payload = None
        if not payload:
            # Use 'text' form field as fallback
            if not text:
                raise HTTPException(status_code=400, detail="Provide text in JSON body or form field 'text'")
            payload = {"text": text}

        t = payload.get("text") if isinstance(payload, dict) else None
        if not t or not str(t).strip():
            raise HTTPException(status_code=400, detail="Text is required for TTS")

        model_override = payload.get("model") if isinstance(payload, dict) else None
        voice_id = payload.get("voice_id") if isinstance(payload, dict) else None

        audio_bytes, content_type = await speech_service.synthesize_speech(
            t,
            model=model_override,
            voice_id=voice_id,
        )

        headers = {
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            # Hint filename; still served inline
            "Content-Disposition": "inline; filename=tts-output",
        }

        return StreamingResponse(io.BytesIO(audio_bytes), media_type=content_type, headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


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
        # Normalize transcription to allowed languages (EN/JA)
        transcribed_text = await _normalize_to_allowed_langs(transcribed_text)
        
        # Step 2: Get chat response
        # Try to add weather context from Japanese/English speech
        weather_context = await build_weather_context(transcribed_text)
        result = await llm_service.chat_completion(
            user_message=transcribed_text,
            conversation_history=history,
            weather_context=weather_context,
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
            # Normalize transcription to allowed languages (EN/JA)
            transcribed_text = await _normalize_to_allowed_langs(transcribed_text)
            if combined_message:
                combined_message = f"{combined_message}\n\n[Audio: {transcribed_text}]"
            else:
                combined_message = transcribed_text

        if not combined_message:
            raise HTTPException(status_code=400, detail="Provide either 'message' or 'audio_file'")

        # Weather context for text or transcribed audio (EN/JA)
        weather_context = await build_weather_context(combined_message)
        result = await llm_service.chat_completion(
            user_message=combined_message,
            conversation_history=history,
            weather_context=weather_context,
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
            },
            "tts": {
                "provider": "ElevenLabs",
                "model": getattr(settings, "ELEVENLABS_TTS_MODEL", None),
                "voice_id": getattr(settings, "ELEVENLABS_VOICE_ID", None),
                "enabled": True  # enabled as long as ELEVENLABS_API_KEY is set (required)
            }
        },
        "endpoints": {
            "/api/speech-to-text": "Convert audio to text",
            "/api/chat": "Chat with AI assistant",
            "/api/weather": "Get weather information",
            "/api/voice-chat": "Complete voice chat flow",
            "/api/assist": "Unified text or audio input pipeline",
            "/api/text-to-speech": "Convert text to audio (Deepgram)",
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

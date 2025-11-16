from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import io
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
    print("🚀 Starting Voice-Enabled Chatbot Backend...")
    print(f"📊 LLM Model: {settings.LLM_MODEL}")
    print(f"🎤 Speech Model: {settings.ELEVENLABS_MODEL}")
    print(f"🔊 TTS Model (ElevenLabs): {settings.ELEVENLABS_TTS_MODEL}")
    print(f"🔊 TTS Voice (ElevenLabs): {settings.ELEVENLABS_VOICE_ID}")
    yield
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
speech_service = SpeechService()
weather_service = WeatherService()
llm_service = LLMService(weather_service=weather_service)


def _detect_lang_simple(text: str) -> str:
    if not text:
        return "en"

    has_ja = any(
        ('\u3040' <= ch <= '\u309F')
        or ('\u30A0' <= ch <= '\u30FF')
        or ('\u4E00' <= ch <= '\u9FFF')
        for ch in text
    )
    if has_ja:
        return "ja"

    has_en = any(('a' <= ch.lower() <= 'z') for ch in text)
    if has_en:
        return "en"

    return "other"


async def _normalize_to_allowed_langs(text: str) -> str:
    lang = _detect_lang_simple(text)
    if lang in ("en", "ja"):
        return text
    try:
        translated = await llm_service.translate_text(text, "en")
        return translated or text
    except Exception:
        return text


@app.get("/", response_model=HealthResponse)
async def root():
    return {
        "status": "online",
        "message": "Voice-Enabled Chatbot API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "message": "All systems operational"
    }


@app.post("/api/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio_file: UploadFile = File(...)):
    try:
        print(f"/api/speech-to-text: received file name={audio_file.filename}, content_type={audio_file.content_type}")
        audio_data = await audio_file.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
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
    try:
        result = await llm_service.chat_completion(
            user_message=request.message,
            conversation_history=request.conversation_history,
            system_prompt_override=request.system_prompt
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@app.post("/api/text-to-speech")
async def text_to_speech(request: Request, text: str = Form(None)):
    try:
        payload = None
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                payload = await request.json()
        except Exception:
            payload = None
        if not payload:
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
            "Content-Disposition": "inline; filename=tts-output",
        }

        return StreamingResponse(io.BytesIO(audio_bytes), media_type=content_type, headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


@app.post("/api/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio_file: UploadFile = File(...),
    conversation_history: Optional[str] = None,
    system_prompt: Optional[str] = Form(None)
):
    try:
        history = []
        if conversation_history:
            try:
                history_data = json.loads(conversation_history)
                history = [ChatMessage(**msg) for msg in history_data]
            except:
                pass
        
        print(f"/api/voice-chat: received file name={audio_file.filename}, content_type={audio_file.content_type}")
        audio_data = await audio_file.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        transcribed_text = await speech_service.transcribe_audio(
            audio_data,
            mime_type=getattr(audio_file, "content_type", None),
            filename=getattr(audio_file, "filename", None)
        )
        transcribed_text = await _normalize_to_allowed_langs(transcribed_text)
        
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
            transcribed_text = await _normalize_to_allowed_langs(transcribed_text)
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


@app.post("/api/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
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

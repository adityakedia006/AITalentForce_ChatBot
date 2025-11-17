# Anya - Weather & Fashion Chatbot (Backend codebase)

FastAPI backend for a multilingual voice and text chatbot powered by Groq LLM, Deepgram speech-to-text, and ElevenLabs text-to-speech. Includes optional weather-awareness for better, context-driven responses.

## Features

- Voice input: Speech-to-text via Deepgram
- Text-to-speech: Natural voices via ElevenLabs
- AI chat: Groq LLM with fallback across supported models
- Weather tool: Uses Open‑Meteo APIs under the hood (called by the LLM when needed)
- Async and fast: Powered by FastAPI and httpx

## Tech Stack

- Backend: FastAPI (Python)
- LLM: Groq API (Llama/Gemma family)
- STT: Deepgram API
- TTS: ElevenLabs API

## Quickstart

Prerequisites: Python 3.10+ and pip

1) Create a virtual environment and install dependencies

```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

2) Configure environment variables

```powershell
Copy-Item .env.example .env
# Then edit .env and provide your keys
```

3) Run the server

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# or
python main.py
```

Open http://localhost:8000 to verify. API docs are at `/docs` (Swagger) and `/redoc`.

## Environment Variables

- GROQ_API_KEY: Groq API key (required)
- DEEPGRAM_API_KEY: Deepgram API key for STT (required for voice input)
- ELEVENLABS_API_KEY: ElevenLabs API key for TTS (required for audio output)
- HOST: Server host (default `0.0.0.0`)
- PORT: Server port (default `8000`)
- DEBUG: Enables reload/logging (default `True`)
- LLM_MODEL: Default Groq model (default `llama-3.3-70b-versatile`)
- LLM_FORCE_ENGLISH: Force English responses (`True`/`False`, default `False`)
- LLM_SYSTEM_PROMPT: System prompt override (optional)
- ELEVENLABS_TTS_MODEL: ElevenLabs TTS model (default `eleven_multilingual_v2`)
- ELEVENLABS_VOICE_ID: ElevenLabs voice id (default `21m00Tcm4TlvDq8ikWAM`)

See `config.py` and `.env.example` for the authoritative list and defaults.

## API Endpoints

- GET `/health`: Service status
- POST `/api/chat`: Text chat
  - Body (JSON): `{ "message": "...", "conversation_history": [ {"role":"user","content":"..."} ], "system_prompt": "..." }`
- POST `/api/voice-chat`: Upload audio; returns transcript and reply
  - Multipart form fields: `audio_file` (file), `conversation_history` (JSON string, optional), `system_prompt` (string, optional)
- POST `/api/text-to-speech`: Convert text to audio and stream back
  - JSON or form field: `text` (required), optional `model`, `voice_id`
- POST `/api/assist`: Unified endpoint that accepts either text and/or audio and returns a response
- POST `/api/translate`: Translate short text between English and Japanese
  - JSON: `{ "text": "こんにちは", "target_lang": "en" }`

### Curl Examples

Text chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","conversation_history":[]}'
```

Voice chat
```bash
curl -X POST http://localhost:8000/api/voice-chat \
  -F "audio_file=@sample.wav" \
  -F "conversation_history=[]"
```

Text to Speech
```bash
curl -X POST http://localhost:8000/api/text-to-speech \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello there"}' \
  --output tts-output.mp3
```

Assist (audio)
```bash
curl -X POST http://localhost:8000/api/assist \
  -F "audio_file=@sample.wav"
```

Translate
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは","target_lang":"en"}'
```

## LLM Models

Default model is controlled by `LLM_MODEL` in `.env`. Supported/known-good models include:

- meta-llama/llama-4-maverick-17b-128e-instruct
- llama-3.3-70b-versatile
- llama-3.1-8b-instant
- mixtral-8x7b-32768
- gemma2-9b-it

The service uses a fallback strategy: it tries your configured model first, then additional models if the first attempt fails (e.g., rate limits or temporary unavailability). See `services/llm_service.py` for the exact order.

## Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── config.py               # Settings and environment variables
├── models.py               # Pydantic request/response models
├── services/
│   ├── __init__.py
│   ├── speech_service.py   # Deepgram STT + ElevenLabs TTS
│   ├── llm_service.py      # Groq LLM integration + tool calling
│   └── weather_service.py  # Open‑Meteo client used by the LLM tool
├── requirements.txt        # Python dependencies
├── .env.example            # Env template
└── README.md               # This file
```

## Notes

- To change the assistant’s behavior and tone, edit `LLM_SYSTEM_PROMPT` in `.env` or update the default in `config.py`.
- For production, restrict CORS in `main.py` and disable `DEBUG`.
- Ensure both `DEEPGRAM_API_KEY` and `ELEVENLABS_API_KEY` are set if you plan to use voice input/output.

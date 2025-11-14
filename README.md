# Voice-Enabled Chatbot Backend

A FastAPI-based backend for a voice-enabled chatbot with multilingual support, powered by Groq LLM, ElevenLabs speech-to-text, and Meteo weather API.

## Features

- 🎤 **Voice Input**: Multilingual speech-to-text using ElevenLabs API
- 🤖 **AI Chat**: Powered by Groq API (Gemma 2 9B / Llama 3)
- 🌦️ **Weather Integration**: Real-time weather data via Meteo API
- 🚀 **Fast & Async**: Built with FastAPI for high performance
- 🌍 **Multilingual**: Supports multiple languages through ElevenLabs

## Tech Stack

- **Backend**: FastAPI (Python)
- **LLM**: Groq API (Gemma 2 9B / Llama 3.1)
- **Speech-to-Text**: ElevenLabs API
- **Weather**: Open-Meteo API
- **Frontend**: Streamlit (separate)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **GROQ_API_KEY**: Get from [Groq Console](https://console.groq.com/)
- **ELEVENLABS_API_KEY**: Get from [ElevenLabs](https://elevenlabs.io/)

### 3. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```

### Speech to Text
```
POST /api/speech-to-text
Content-Type: multipart/form-data

Body:
- audio_file: Audio file (any format supported by ElevenLabs)
```

### Chat Completion
```
POST /api/chat
Content-Type: application/json

Body:
{
  "message": "Your message here",
  "conversation_history": []  // Optional
}
```

### Weather
```
GET /api/weather?location=London
```

### Voice Chat (Combined)
```
POST /api/voice-chat
Content-Type: multipart/form-data

Body:
- audio_file: Audio file
- conversation_history: JSON string (optional)
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration and settings
├── models.py              # Pydantic models/schemas
├── services/
│   ├── __init__.py
│   ├── speech_service.py  # ElevenLabs integration
│   ├── llm_service.py     # Groq LLM integration
│   └── weather_service.py # Meteo API integration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GROQ_API_KEY | Groq API key | Required |
| ELEVENLABS_API_KEY | ElevenLabs API key | Required |
| HOST | Server host | 0.0.0.0 |
| PORT | Server port | 8000 |
| DEBUG | Debug mode | True |
| LLM_MODEL | Groq model name | gemma2-9b-it |
| ELEVENLABS_MODEL | ElevenLabs model | eleven_multilingual_v2 |

## Available LLM Models

- `gemma2-9b-it` (default)
- `llama-3.1-70b-versatile`
- `llama-3.1-8b-instant`
- `llama3-70b-8192`
- `mixtral-8x7b-32768`

## License

MIT

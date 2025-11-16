import io
import httpx
from config import get_settings
from typing import Tuple, Optional
import os
import mimetypes

class SpeechService:
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = settings.ELEVENLABS_API_KEY
        self.model = "scribe_v1"
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id: str = getattr(settings, "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.tts_output_mime: str = getattr(settings, "ELEVENLABS_TTS_OUTPUT_MIME", "audio/mpeg")
        # Deepgram config
        self.deepgram_api_key: Optional[str] = api_key or getattr(settings, "DEEPGRAM_API_KEY", None) or os.getenv("DEEPGRAM_API_KEY")
     
    async def transcribe_audio_deepgram(self, audio_bytes: bytes, *, audio_format: Optional[str] = None, mime_type: Optional[str] = None) -> str:
        if not self.deepgram_api_key:
            raise Exception("Deepgram API key not configured. Set DEEPGRAM_API_KEY.")

        url = "https://api.deepgram.com/v1/listen"

        # Map common formats to content-types
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
            "opus": "audio/opus",
            "webm": "audio/webm",
        }

        content_type = None
        if mime_type and isinstance(mime_type, str):
            content_type = mime_type
        elif audio_format:
            content_type = content_type_map.get(audio_format.lower())
        if not content_type:
            content_type = "audio/wav"

        headers = {
            "Authorization": f"Token {self.deepgram_api_key}",
            "Content-Type": content_type,
        }

        params = {
            "model": "nova-3",
            "detect_language": "true",
            "smart_format": "true",
            "punctuate": "true",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, params=params, content=audio_bytes)
            if resp.status_code != 200:
                raise Exception(f"Deepgram API Error {resp.status_code}: {resp.text}")
            data = resp.json()
            transcript = (
                data.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
                .get("transcript", "")
            )
            if not transcript:
                raise Exception(f"No transcript found in Deepgram response: {data}")
            return transcript
    
    async def synthesize_speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice_id: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        if not text or not text.strip():
            raise ValueError("Text is required for TTS")

        url = f"{self.base_url}/text-to-speech/{(voice_id or self.voice_id)}"

        headers = {
            "xi-api-key": self.api_key,
            "accept": self.tts_output_mime,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "model_id": (model or self.tts_model),
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    try:
                        err = response.json()
                    except Exception:
                        err = {"raw": response.text}
                    raise Exception(f"ElevenLabs TTS error {response.status_code}: {err}")

                audio_bytes = response.content
                content_type = response.headers.get("Content-Type", self.tts_output_mime)
                return audio_bytes, content_type

        except httpx.HTTPError as e:
            detail = ""
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = f" | Body: {e.response.text}"
                except Exception:
                    pass
            raise Exception(f"TTS request failed: HTTP error - {str(e)}{detail}")
        except Exception as e:
            raise Exception(f"TTS request failed: {str(e)}")

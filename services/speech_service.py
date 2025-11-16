import io
import httpx
from config import get_settings
from typing import Tuple, Optional


class SpeechService:
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ELEVENLABS_API_KEY
        self.model = "scribe_v1"
        self.base_url = "https://api.elevenlabs.io/v1"
        self.tts_model: str = getattr(settings, "ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")
        self.voice_id: str = getattr(settings, "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.tts_output_mime: str = getattr(settings, "ELEVENLABS_TTS_OUTPUT_MIME", "audio/mpeg")
    
    async def transcribe_audio(self, audio_data: bytes, mime_type: str | None = None, filename: str | None = None) -> str:
        try:
            url = f"{self.base_url}/speech-to-text"
            
            headers = {
                "xi-api-key": self.api_key,
                "accept": "application/json"
            }
            
            safe_filename = filename or "recording.webm"
            safe_mime = mime_type or "audio/webm"
            files = {
                "file": (safe_filename, audio_data, safe_mime)
            }
            
            data = {
                "model_id": self.model
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, files=files, data=data)

                if response.status_code != 200:
                    try:
                        err_payload = response.json()
                    except Exception:
                        err_payload = {"raw": response.text}
                    raise Exception(f"ElevenLabs API error {response.status_code}: {err_payload}")

                result = response.json()
                transcribed_text = result.get("text") or result.get("transcription") or ""

                if not transcribed_text:
                    raise ValueError(f"No text field in response: {result}")

                return transcribed_text
            
        except httpx.HTTPError as e:
            detail = ""
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = f" | Body: {e.response.text}"
                except Exception:
                    pass
            raise Exception(f"Speech-to-text transcription failed: HTTP error - {str(e)}{detail}")
        except Exception as e:
            raise Exception(f"Speech-to-text transcription failed: {str(e)}")
    
    def get_supported_languages(self) -> list:
        return [
            "en", "es", "fr", "de", "it", "pt", "pl", "nl",
            "hi", "ja", "zh", "ko", "ar", "ru", "tr", "sv",
            "id", "fil", "uk", "cs", "el", "fi", "hr", "ms",
            "ro", "sk", "bg", "bn", "ta", "te"
        ]

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

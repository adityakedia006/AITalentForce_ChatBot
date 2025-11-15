import io
import httpx
from config import get_settings


class SpeechService:
    """Service for speech-to-text conversion using ElevenLabs Scribe API."""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ELEVENLABS_API_KEY
        self.model = "scribe_v1"  # ElevenLabs Scribe model
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def transcribe_audio(self, audio_data: bytes, mime_type: str | None = None, filename: str | None = None) -> str:
        """
        Transcribe audio to text using ElevenLabs Scribe API.
        
        Args:
            audio_data: Audio file bytes
            
        Returns:
            Transcribed text
            
        Raises:
            Exception: If transcription fails
        """
        try:
            # Use ElevenLabs REST API directly for speech-to-text
            url = f"{self.base_url}/speech-to-text"
            
            headers = {
                "xi-api-key": self.api_key,
                "accept": "application/json"
            }
            
            # Prepare the file for upload
            # ElevenLabs expects the multipart field name to be 'file'
            safe_filename = filename or "recording.webm"
            safe_mime = mime_type or "audio/webm"
            files = {
                "file": (safe_filename, audio_data, safe_mime)
            }
            
            # Optional: specify model
            data = {
                "model_id": self.model
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, files=files, data=data)

                if response.status_code != 200:
                    # Try to surface API-provided error details
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
            # Provide more detail if response available
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
        """
        Get list of supported languages.
        
        Returns:
            List of supported language codes
        """
        # ElevenLabs multilingual model supports many languages
        return [
            "en", "es", "fr", "de", "it", "pt", "pl", "nl",
            "hi", "ja", "zh", "ko", "ar", "ru", "tr", "sv",
            "id", "fil", "uk", "cs", "el", "fi", "hr", "ms",
            "ro", "sk", "bg", "bn", "ta", "te"
        ]

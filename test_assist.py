"""Comprehensive tester for /api/assist endpoint.

Supports:
- Text-only request
- Audio-only request (multipart upload field name: audio_file)
- Text + Audio combined

Usage examples (PowerShell):
  # Text only
  python .\test_assist.py --message "Hello!"

  # Audio only (WEBM)
  python .\test_assist.py --audio "D:\\chat\\sample.webm"

  # Both
  python .\test_assist.py --message "Transcribe this" --audio "D:\\chat\\sample.webm"
"""

import os
import sys
import json
import argparse
import mimetypes
import requests
from typing import Optional


def guess_mime(path: str) -> str:
    ext_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".opus": "audio/opus",
        ".webm": "audio/webm",
    }
    _, ext = os.path.splitext(path.lower())
    return ext_map.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"


def post_assist(
    base_url: str,
    *,
    message: Optional[str] = None,
    audio_path: Optional[str] = None,
    history_json: Optional[str] = None,
    system_prompt: Optional[str] = None,
    timeout: int = 60,
):
    url = f"{base_url.rstrip('/')}/api/assist"
    data = {}
    files = None

    if message:
        data["message"] = message

    if history_json:
        data["conversation_history"] = history_json

    if system_prompt:
        data["system_prompt"] = system_prompt

    if audio_path:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        mime = guess_mime(audio_path)
        files = {
            "audio_file": (os.path.basename(audio_path), open(audio_path, "rb"), mime)
        }

    resp = requests.post(url, data=data, files=files, timeout=timeout)
    # Close any open file handles
    if files:
        try:
            files["audio_file"][1].close()
        except Exception:
            pass
    return resp


def main():
    parser = argparse.ArgumentParser(description="Test /api/assist endpoint")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://localhost:8000"), help="API base URL")
    parser.add_argument("--message", default=None, help="Text message to send")
    parser.add_argument("--audio", default=None, help="Path to audio file to upload")
    parser.add_argument("--history-file", default=None, help="Path to JSON file with conversation_history array")
    parser.add_argument("--system-prompt", default=None, help="Optional system prompt override")
    parser.add_argument(
        "--mode",
        choices=["auto", "text", "audio", "both"],
        default="auto",
        help="auto: text if no audio else both",
    )
    args = parser.parse_args()

    history_json = None
    if args.history_file:
        with open(args.history_file, "r", encoding="utf-8") as f:
            history_json = f.read()

    # Decide mode
    mode = args.mode
    if mode == "auto":
        mode = "both" if args.audio and args.message else ("audio" if args.audio else "text")

    if mode == "text" and not args.message:
        print("--message is required for text mode", file=sys.stderr)
        sys.exit(2)
    if mode == "audio" and not args.audio:
        print("--audio is required for audio mode", file=sys.stderr)
        sys.exit(2)

    combos = []
    if mode == "text":
        combos = [(args.message, None)]
    elif mode == "audio":
        combos = [(None, args.audio)]
    elif mode == "both":
        combos = [(args.message, args.audio)]

    success = True
    for idx, (msg, audio) in enumerate(combos, start=1):
        print("\n" + "=" * 60)
        print(f"Test #{idx} -> message={'yes' if msg else 'no'}, audio={'yes' if audio else 'no'}")
        print("=" * 60)
        try:
            resp = post_assist(
                args.base_url,
                message=msg,
                audio_path=audio,
                history_json=history_json,
                system_prompt=args.system_prompt,
            )
            print(f"Status: {resp.status_code}")
            ct = resp.headers.get("Content-Type", "")
            if "application/json" in ct:
                try:
                    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
                except Exception:
                    print(resp.text[:1000])
            else:
                print(resp.text[:1000])
            if resp.status_code != 200:
                success = False
        except Exception as e:
            success = False
            print(f"Error: {e}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

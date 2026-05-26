"""
services/whisper_service.py

Transcribes audio files to text using OpenAI Whisper (local model).
No API key required — runs entirely on-device.

Supported formats: .mp3, .wav, .m4a, .ogg, .flac, .mp4
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config

# Cache loaded model to avoid reloading on every call
_whisper_model_cache = None


def _get_model():
    """Load Whisper model (cached after first load)."""
    global _whisper_model_cache
    if _whisper_model_cache is None:
        try:
            import whisper
        except ImportError:
            raise ImportError(
                "openai-whisper not installed. Run: pip install openai-whisper"
            )
        print(f"  [Whisper] Loading model: {config.WHISPER_MODEL}...", flush=True)
        _whisper_model_cache = whisper.load_model(config.WHISPER_MODEL)
        print(f"  [Whisper] Model loaded.", flush=True)
    return _whisper_model_cache


def transcribe(audio_path: str) -> dict:
    """
    Transcribe an audio file using Whisper.

    Args:
        audio_path: Path to audio file (.mp3, .wav, .m4a etc.)

    Returns:
        dict with keys:
            text        — full transcript as plain string
            segments    — list of {id, start, end, text} dicts
            language    — detected language code e.g. "en"
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _get_model()

    print(f"  [Whisper] Transcribing: {os.path.basename(audio_path)}", flush=True)
    result = model.transcribe(
        audio_path,
        language="en",           # force English — banking calls
        verbose=False,
        word_timestamps=False,
    )

    print(f"  [Whisper] Transcription complete — {len(result['segments'])} segments", flush=True)

    # Save raw transcript to data/transcripts/
    transcript_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "transcripts"
    )
    os.makedirs(transcript_dir, exist_ok=True)

    base_name = Path(audio_path).stem
    transcript_path = os.path.join(transcript_dir, f"{base_name}_transcript.json")
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump({
            "audio_file": audio_path,
            "text": result["text"],
            "language": result.get("language", "en"),
            "segments": result["segments"],
        }, f, indent=2)

    print(f"  [Whisper] Saved to: {transcript_path}", flush=True)
    return result


def transcribe_to_text(audio_path: str) -> str:
    """
    Convenience function — returns plain text transcript only.
    """
    result = transcribe(audio_path)
    return result["text"].strip()


def get_segments(audio_path: str) -> list[dict]:
    """
    Returns Whisper segments with timing info.
    Each segment: {id, start, end, text}
    These are passed to the diarisation service for speaker assignment.
    """
    result = transcribe(audio_path)
    return result["segments"]

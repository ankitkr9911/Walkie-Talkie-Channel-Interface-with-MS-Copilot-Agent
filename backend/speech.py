"""
speech.py — Speech Processing Layer
=====================================
STT: Faster-Whisper (offline, open-source, MIT license)
TTS: edge-tts (Microsoft Edge TTS — high quality, no model downloads)

Note: edge-tts is used instead of Piper for Windows compatibility.
For production Linux deployment, swap synthesize_speech() to use Piper.
"""

import os
import tempfile
import edge_tts
from faster_whisper import WhisperModel

# ---------- Configuration ----------
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")     # tiny | base | small | medium | large-v2
TTS_VOICE = os.getenv("TTS_VOICE", "en-IN-NeerjaNeural")   # Indian English female voice

# Lazy-loaded Whisper model (downloaded on first use, ~150MB for 'base')
_whisper_model = None


def _get_whisper_model() -> WhisperModel:
    """Load Whisper model lazily on first call. Runs on CPU with int8 quantization."""
    global _whisper_model
    if _whisper_model is None:
        print(f"[*] Loading Faster-Whisper model '{WHISPER_MODEL_SIZE}'...")
        _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        print("[OK] Whisper model loaded")
    return _whisper_model


def transcribe_audio(audio_path: str) -> str:
    """
    Convert speech audio file to text using Faster-Whisper.
    Accepts any audio format (wav, webm, mp3, ogg, etc.).
    Returns the transcribed text string.
    """
    model = _get_whisper_model()
    segments, _info = model.transcribe(audio_path, beam_size=5, language="en")

    # Join all segments into a single transcript
    transcript = " ".join(segment.text.strip() for segment in segments)
    return transcript.strip()


async def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech audio (MP3) using Microsoft Edge TTS.
    Returns raw MP3 bytes that can be played directly in the browser.
    """
    communicate = edge_tts.Communicate(text, TTS_VOICE)

    # Collect all audio chunks into a single bytes object
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    return b"".join(audio_chunks)

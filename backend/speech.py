"""
speech.py — Speech Processing Layer
=====================================
STT: Faster-Whisper (offline, open-source, MIT license)
TTS: edge-tts (Microsoft Edge TTS — high quality, no model downloads)

Note: edge-tts is used instead of Piper for Windows compatibility.
For production Linux deployment, swap synthesize_speech() to use Piper.
"""

import os
import io
import tempfile
import numpy as np
import av
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


def _load_audio_array(audio_path: str, sample_rate: int = 16000) -> np.ndarray:
    """
    Load any audio file (including webm/opus from browser MediaRecorder) into
    a float32 numpy array at the given sample rate.

    KEY: Reads the file bytes into a BytesIO buffer first, then opens
    with av.open(buffer). This bypasses the Windows 8.3 short-name path
    issue (e.g. AAQ~1.KUM) that caused PyAV's ffmpeg to fail when
    opening the temp file by path.

    If the audio content is genuinely undecodable, returns a silent
    numpy array so the empty-transcript handler fires ("didn't catch that")
    instead of propagating a 500 error.
    """
    try:
        # Read file bytes into memory — no more file path passed to PyAV
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()

        if len(audio_bytes) < 500:
            print("[WARN] Audio too small, treating as silence")
            return np.zeros(sample_rate, dtype=np.float32)

        buf = io.BytesIO(audio_bytes)
        resampler = av.AudioResampler(format="s16", layout="mono", rate=sample_rate)
        audio_chunks = []

        with av.open(buf) as container:
            for frame in container.decode(audio=0):
                resampled = resampler.resample(frame)
                if isinstance(resampled, list):
                    for rf in resampled:
                        audio_chunks.append(rf.to_ndarray())
                else:
                    audio_chunks.append(resampled.to_ndarray())

        if not audio_chunks:
            print("[WARN] Audio decoded but no frames found, treating as silence")
            return np.zeros(sample_rate, dtype=np.float32)

        raw = np.concatenate(audio_chunks, axis=1).flatten()
        return raw.astype(np.float32) / 32768.0

    except Exception as e:
        # Do NOT re-raise — return silence so we get "didn't catch that" not 500
        print(f"[WARN] Audio decode failed ({type(e).__name__}: {e}), returning silence")
        return np.zeros(sample_rate, dtype=np.float32)


def transcribe_audio(audio_path: str) -> str:
    """
    Convert speech audio file to text using Faster-Whisper.
    Accepts any audio format (wav, webm, mp3, ogg, etc.).

    Decodes audio via PyAV into a numpy array first to avoid Windows
    codec detection issues with browser-recorded webm/opus files.
    Returns the transcribed text string.
    """
    model = _get_whisper_model()
    audio_input = _load_audio_array(audio_path)
    segments, _info = model.transcribe(audio_input, beam_size=5, language="en")

    # Join all segments into a single transcript
    transcript = " ".join(segment.text.strip() for segment in segments)
    return transcript.strip()


async def synthesize_speech(text: str, retries: int = 3) -> bytes:
    """
    Convert text to speech audio (MP3) using Microsoft Edge TTS.
    Returns raw MP3 bytes that can be played directly in the browser.

    Retries on failure because edge-tts intermittently gets 403 from
    Microsoft's WebSocket endpoint (rate limiting / token rotation).
    """
    import asyncio

    last_err = None
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, TTS_VOICE)
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            if audio_chunks:
                return b"".join(audio_chunks)
        except Exception as e:
            last_err = e
            print(f"[WARN] TTS attempt {attempt + 1}/{retries} failed: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)  # Brief pause before retry

    raise last_err or RuntimeError("TTS failed after all retries")

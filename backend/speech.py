"""
speech.py — Speech Processing Layer
=====================================
STT: Faster-Whisper (offline, open-source, MIT license)
TTS: Piper TTS (offline, no network — avoids corporate proxy blocks)
     Falls back to edge-tts if PIPER_MODEL_PATH is not set.
"""

import os
import io
import re
import wave
import asyncio
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


# ---------- Piper TTS (offline) ----------
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "")   # Full path to .onnx model file
_piper_voice = None


def _get_piper_voice():
    """Lazy-load Piper TTS model on first call. Returns None if not configured."""
    global _piper_voice
    if _piper_voice is not None:
        return _piper_voice
    if not PIPER_MODEL_PATH or not os.path.exists(PIPER_MODEL_PATH):
        return None
    try:
        from piper import PiperVoice
        print(f"[*] Loading Piper TTS model '{PIPER_MODEL_PATH}'...")
        _piper_voice = PiperVoice.load(PIPER_MODEL_PATH)
        print("[OK] Piper TTS model loaded")
        return _piper_voice
    except Exception as e:
        print(f"[WARN] Piper TTS load failed: {e}")
        return None


def _piper_synth_sync(text: str) -> bytes:
    """
    Synthesize speech using Piper — synchronous, runs in a thread executor.
    Returns raw WAV bytes ready for base64 encoding and browser playback.
    Audio extraction logic adapted from the user's tested Piper script.
    """
    voice = _get_piper_voice()
    if voice is None:
        raise RuntimeError("Piper model not available")

    # Clean text (same logic as the tested Piper script)
    text = re.sub(r'([.?!,])\1+', r'\1', text)          # collapse repeated punctuation
    text = re.sub(r'([.?!,])(?=[^\s])', r'\1 ', text)   # ensure space after punctuation
    text = re.sub(r'[^a-zA-Z0-9\s.,?!\'-]', '', text)   # strip unsupported characters
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return b""

    audio_chunks = []
    for chunk in voice.synthesize(text):
        # Try each known attribute name across piper-tts versions
        for attr in ["audio_int16_bytes", "audio_int16_array", "audio", "audio_float_array"]:
            if hasattr(chunk, attr):
                val = getattr(chunk, attr)
                if attr == "audio_int16_bytes":
                    audio_chunks.append(val)
                elif attr in ("audio_int16_array", "audio"):
                    arr = np.asarray(val, dtype=np.int16)
                    audio_chunks.append(arr.tobytes())
                elif attr == "audio_float_array":
                    arr = np.asarray(val, dtype=np.float32)
                    audio_chunks.append((arr * 32767).astype(np.int16).tobytes())
                break

    if not audio_chunks:
        return b""

    pcm_bytes = b"".join(audio_chunks)

    # Pack raw PCM into a proper WAV container
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)                        # mono
        wav_file.setsampwidth(2)                        # 16-bit
        wav_file.setframerate(voice.config.sample_rate) # e.g. 22050 Hz
        wav_file.writeframes(pcm_bytes)
    return buf.getvalue()


async def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech audio.

    Primary:  Piper TTS (fully offline, no network calls — immune to corporate proxy blocks).
              Requires PIPER_MODEL_PATH set in .env pointing to .onnx model file.
              Returns WAV bytes.

    Fallback: edge-tts (requires internet — blocked on Accenture network).
              Returns MP3 bytes.
    """
    # --- Primary: Piper (offline) ---
    if _get_piper_voice() is not None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _piper_synth_sync, text)

    # --- Fallback: edge-tts (network required) ---
    print("[INFO] Piper model not configured — trying edge-tts (may fail on corporate networks)")
    last_err = None
    for attempt in range(3):
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
            print(f"[WARN] edge-tts attempt {attempt + 1}/3 failed: {type(e).__name__}: {e}")
            if attempt < 2:
                await asyncio.sleep(1)

    raise last_err or RuntimeError("All TTS methods failed")

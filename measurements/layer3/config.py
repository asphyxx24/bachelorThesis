"""
Layer 3 — gemeinsame Konfiguration.

Single Source of Truth für alle Layer-3-Caller (llm/tts/stt): Endpunkte, gepinnte
Modelle, feste Inputs, Timeouts, Erfolgskriterien und API-Keys (aus .env).
Werte/Begründung: setup/api_endpunkte.md (Endpunkte, Modell-Pinning A2) +
setup/messprotokoll.md (Metriken, Timeouts/Erfolgskriterien A7).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Pfade unabhängig vom Arbeitsverzeichnis ableiten (robust für cron/systemd auf der EC2):
ROOT = Path(__file__).resolve().parents[2]      # measurements/layer3/config.py -> Repo-Wurzel
DATA_DIR = ROOT / "data" / "layer3"

load_dotenv(ROOT / ".env")   # .env aus der Repo-Wurzel laden (unabhängig vom Arbeitsverzeichnis)


def get_key(env_name):
    """API-Key aus der Umgebung. Gibt None zurück (kein Crash), wenn nicht gesetzt."""
    return os.environ.get(env_name) or None


# --- Feste Inputs je Kategorie (identisch je Kategorie -> fairer Vergleich) ---
LLM_PROMPT = "Reply in one short sentence: What is the capital of Germany?"
TTS_TEXT = "Good morning! How can I assist you today?"
STT_WAV = "data/inputs/sample.wav"      # ~5 s, PCM linear16, 16 kHz, mono (für STT-Slice)

MAX_TOKENS = 50

# --- Timeouts & Erfolgskriterien (A7) ---
CONNECT_TIMEOUT_S = 10
RESPONSE_TIMEOUT_S = 30
LLM_MIN_CHUNKS = 3          # >= 3 SSE-Content-Chunks (fängt Degeneration, A10)
TTS_MIN_BYTES = 1000        # >= 1000 Bytes Audio

# --- LLM-Endpunkte (OpenAI-kompatibles /chat/completions, SSE) ---
LLM = {
    "openai":  {"url": "https://api.openai.com/v1/chat/completions",
                "host": "api.openai.com", "model": "gpt-4o-mini-2024-07-18",
                "key_env": "OPENAI_API_KEY"},
    "groq":    {"url": "https://api.groq.com/openai/v1/chat/completions",
                "host": "api.groq.com", "model": "llama-3.1-8b-instant",
                "key_env": "GROQ_API_KEY"},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions",
                "host": "api.mistral.ai", "model": "mistral-small-2603",
                "key_env": "MISTRAL_API_KEY"},
}

# --- TTS-Endpunkte (HTTPS-Streaming) — für den späteren TTS-Caller ---
TTS = {
    "deepgram": {"url": "https://api.deepgram.com/v1/speak?model=aura-2-asteria-en&encoding=mp3",
                 "host": "api.deepgram.com", "model": "aura-2-asteria-en",
                 "key_env": "DEEPGRAM_API_KEY", "auth": "token"},
    "openai":   {"url": "https://api.openai.com/v1/audio/speech",
                 "host": "api.openai.com", "model": "tts-1", "voice": "alloy", "format": "mp3",
                 "key_env": "OPENAI_API_KEY", "auth": "bearer"},
    "azure":    {"url": "https://italynorth.tts.speech.microsoft.com/cognitiveservices/v1",
                 "host": "italynorth.tts.speech.microsoft.com", "model": "en-US-JennyNeural",
                 "voice": "en-US-JennyNeural", "key_env": "AZURE_SPEECH_KEY", "auth": "azure"},
}

# --- STT-Endpunkte (WebSocket) — für den späteren STT-Caller ---
STT = {
    "deepgram": {"url": ("wss://api.deepgram.com/v1/listen?model=nova-3&language=en"
                         "&encoding=linear16&sample_rate=16000&punctuate=true&interim_results=false"),
                 "host": "api.deepgram.com", "model": "nova-3", "key_env": "DEEPGRAM_API_KEY"},
    "revai":    {"url": ("wss://api.rev.ai/speechtotext/v1/stream"
                         "?content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1"),
                 "host": "api.rev.ai", "model": "english", "key_env": "REVAI_ACCESS_TOKEN"},
    "azure":    {"url": ("wss://italynorth.stt.speech.microsoft.com/speech/recognition/"
                         "conversation/cognitiveservices/v1"),
                 "host": "italynorth.stt.speech.microsoft.com", "model": "standard-neural",
                 "key_env": "AZURE_SPEECH_KEY"},
}

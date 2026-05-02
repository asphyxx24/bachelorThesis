"""Zentrale Konfiguration: Endpoints, Metriken, Konstanten.

9 Cloud-AI-API-Endpoints, 3 pro Kategorie (STT, LLM, TTS).
Alle Endpoints werden in Layer 1 (Infrastruktur) gemessen.
Layer 3 (Latenz) nutzt die provider-spezifischen Module.
"""

# ── STT-Endpoints ────────────────────────────────────────────────────────────

STT_ENDPOINTS = [
    {
        "name": "deepgram",
        "host": "api.deepgram.com",
        "url": "https://api.deepgram.com",
        "protocol": "WebSocket",
    },
    {
        "name": "assemblyai",
        "host": "api.assemblyai.com",
        "url": "https://api.assemblyai.com",
        "protocol": "WebSocket",
    },
    {
        "name": "azure_stt",
        "host": "germanywestcentral.stt.speech.microsoft.com",
        "url": "https://germanywestcentral.stt.speech.microsoft.com",
        "protocol": "WebSocket",
    },
]

# ── LLM-Endpoints ────────────────────────────────────────────────────────────

LLM_ENDPOINTS = [
    {
        "name": "openai",
        "host": "api.openai.com",
        "url": "https://api.openai.com",
        "protocol": "HTTPS + SSE",
    },
    {
        "name": "groq",
        "host": "api.groq.com",
        "url": "https://api.groq.com",
        "protocol": "HTTPS + SSE",
    },
    {
        "name": "mistral",
        "host": "api.mistral.ai",
        "url": "https://api.mistral.ai",
        "protocol": "HTTPS + SSE",
    },
]

# ── TTS-Endpoints ────────────────────────────────────────────────────────────

TTS_ENDPOINTS = [
    {
        "name": "deepgram_tts",
        "host": "api.deepgram.com",
        "url": "https://api.deepgram.com",
        "protocol": "HTTPS Streaming",
    },
    {
        "name": "openai_tts",
        "host": "api.openai.com",
        "url": "https://api.openai.com",
        "protocol": "HTTPS Streaming",
    },
    {
        "name": "azure_tts",
        "host": "germanywestcentral.tts.speech.microsoft.com",
        "url": "https://germanywestcentral.tts.speech.microsoft.com",
        "protocol": "HTTPS Streaming",
    },
]

# ── Alle Endpoints (fuer Layer 1: Infrastruktur-Messungen) ───────────────────

ENDPOINTS = STT_ENDPOINTS + LLM_ENDPOINTS + TTS_ENDPOINTS

# DNS-Resolver fuer Multi-Resolver-Vergleich (Layer 1)
DNS_RESOLVERS = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]

# Delay zwischen einzelnen Messungen in Layer 3 (Rate-Limit-Schutz)
MEASUREMENT_DELAY_S = 1.5

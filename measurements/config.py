"""Zentrale Konfiguration: Endpoints, Metriken, Konstanten.

9 Cloud-AI-API-Endpoints, 3 pro Kategorie (STT, LLM, TTS).
Alle Endpoints werden in Schicht 1 (Infrastruktur) gemessen.
Schicht 3 (Latenz) nutzt die provider-spezifischen Module.
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
        "name": "speechmatics",
        "host": "eu2.rt.speechmatics.com",
        "url": "https://eu2.rt.speechmatics.com",
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
        "name": "anthropic",
        "host": "api.anthropic.com",
        "url": "https://api.anthropic.com",
        "protocol": "HTTPS + SSE",
    },
]

# ── TTS-Endpoints ────────────────────────────────────────────────────────────

TTS_ENDPOINTS = [
    {
        "name": "elevenlabs",
        "host": "api.elevenlabs.io",
        "url": "https://api.elevenlabs.io",
        "protocol": "HTTPS Streaming",
    },
    {
        "name": "cartesia",
        "host": "api.cartesia.ai",
        "url": "https://api.cartesia.ai",
        "protocol": "WebSocket",
    },
    {
        "name": "polly",
        "host": "polly.eu-central-1.amazonaws.com",
        "url": "https://polly.eu-central-1.amazonaws.com",
        "protocol": "AWS SDK (HTTPS)",
    },
]

# ── Alle Endpoints (fuer Schicht 1: Infrastruktur-Messungen) ─────────────────

ENDPOINTS = STT_ENDPOINTS + LLM_ENDPOINTS + TTS_ENDPOINTS

# DNS-Resolver fuer Multi-Resolver-Vergleich (Schicht 1)
DNS_RESOLVERS = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]

# Delay zwischen einzelnen Messungen in Schicht 3 (Rate-Limit-Schutz)
MEASUREMENT_DELAY_S = 1.5

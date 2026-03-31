"""Zentrale Konfiguration: Endpoints, Metriken, Konstanten.

Die 3 Cloud-AI-API-Endpoints die in allen 3 Schichten gemessen werden.
"""

ENDPOINTS = [
    {
        "name": "deepgram",
        "host": "api.deepgram.com",
        "url": "https://api.deepgram.com",
        "service": "STT",
        "protocol": "WebSocket",
    },
    {
        "name": "requesty",
        "host": "router.requesty.ai",
        "url": "https://router.requesty.ai",
        "service": "LLM",
        "protocol": "HTTPS + SSE",
    },
    {
        "name": "elevenlabs",
        "host": "api.elevenlabs.io",
        "url": "https://api.elevenlabs.io",
        "service": "TTS",
        "protocol": "HTTPS Streaming",
    },
]

# DNS-Resolver fuer Multi-Resolver-Vergleich (Schicht 1)
DNS_RESOLVERS = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]

# Delay zwischen einzelnen Messungen in Schicht 3 (Rate-Limit-Schutz)
MEASUREMENT_DELAY_S = 1.5

"""
Die 7 eindeutigen API-Hosts der Provider-Matrix (s. setup/api_endpunkte.md).

Einmal hier definiert, damit alle Layer-1-Skripte dieselbe Liste benutzen
(eine einzige Quelle der Wahrheit). Deepgram und OpenAI tauchen in der 9er-Matrix
je zweimal auf, sind aber derselbe Host -> nur einmal gelistet.
"""

HOSTS = [
    "api.deepgram.com",                     # STT Deepgram + TTS Deepgram
    "api.rev.ai",                           # STT Rev.ai
    "italynorth.stt.speech.microsoft.com",  # STT Azure
    "api.openai.com",                       # LLM OpenAI + TTS OpenAI
    "api.groq.com",                         # LLM Groq
    "api.mistral.ai",                       # LLM Mistral
    "italynorth.tts.speech.microsoft.com",  # TTS Azure
]

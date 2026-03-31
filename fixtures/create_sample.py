"""Erstellt die sample.wav Fixture via ElevenLabs TTS.

Generiert eine 5-Sekunden WAV-Datei (PCM 16-bit, Mono, 16kHz)
mit deutschem Sprachinhalt fuer die STT-Messungen.

Verwendung:
  python fixtures/create_sample.py

Voraussetzung: ELEVENLABS_API_KEY in .env
"""

import io
import os
import struct
import sys
import wave
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

OUTPUT = Path(__file__).parent / "sample.wav"
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "P7vsEyTOpZ6YUTulin8m")
TEXT = (
    "Guten Tag, ich rufe an wegen einer Anfrage zu Ihrem Produkt. "
    "Koennten Sie mir bitte mehr Informationen dazu geben?"
)


def main() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("FEHLER: ELEVENLABS_API_KEY nicht gesetzt")
        sys.exit(1)

    print(f"Generiere sample.wav via ElevenLabs ({VOICE_ID})...")

    # MP3 von ElevenLabs holen
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "text": TEXT,
        "model_id": "eleven_flash_v2_5",
        "output_format": "pcm_16000",  # Raw PCM 16-bit 16kHz
    }

    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    pcm_data = resp.content

    # Als WAV speichern (Header hinzufuegen)
    with wave.open(str(OUTPUT), "wb") as wf:
        wf.setnchannels(1)       # Mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(16000)   # 16kHz
        wf.writeframes(pcm_data)

    duration_s = len(pcm_data) / (16000 * 2)
    print(f"Gespeichert: {OUTPUT} ({len(pcm_data)} Bytes, {duration_s:.1f}s)")


if __name__ == "__main__":
    main()

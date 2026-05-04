"""Layer-2 Captures: tcpdump + Layer-3-Call fuer jeden Provider.

Fuer jeden der 9 Provider:
1. tcpdump starten (filtert auf Provider-Host)
2. Einen einzelnen Layer-3-API-Call ausfuehren
3. tcpdump stoppen
4. .pcap-Datei in data/layer2/ speichern

Erfordert sudo (fuer tcpdump) und aktiviertes venv.

Verwendung auf EC2:
  sudo -E $(which python) measurements/layer2/capture_all.py
"""

import asyncio
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

OUTDIR = Path(__file__).parent.parent.parent / "data" / "layer2"
SAMPLE_WAV = Path(__file__).parent.parent / "layer3" / "sample.wav"
DATE = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

PROVIDERS = [
    ("deepgram_stt",  "api.deepgram.com",                       "stt"),
    ("revai_stt",     "api.rev.ai",                             "stt"),
    ("azure_stt",     "italynorth.stt.speech.microsoft.com",    "stt"),
    ("openai_llm",    "api.openai.com",                         "llm"),
    ("groq_llm",      "api.groq.com",                           "llm"),
    ("mistral_llm",   "api.mistral.ai",                         "llm"),
    ("deepgram_tts",  "api.deepgram.com",                       "tts"),
    ("openai_tts",    "api.openai.com",                         "tts"),
    ("azure_tts",     "italynorth.tts.speech.microsoft.com",    "tts"),
]


async def run_one_call(name: str, category: str) -> dict:
    if category == "stt":
        if "deepgram" in name:
            from measurements.layer3.stt_deepgram import load_pcm, measure_once
            pcm = load_pcm(SAMPLE_WAV)
            return await measure_once(os.environ["DEEPGRAM_API_KEY"], pcm)
        elif "revai" in name:
            from measurements.layer3.stt_revai import load_pcm, measure_once
            pcm = load_pcm(SAMPLE_WAV)
            return await measure_once(os.environ["REVAI_API_KEY"], pcm)
        elif "azure" in name:
            from measurements.layer3.stt_azure import load_pcm, measure_once
            pcm = load_pcm(SAMPLE_WAV)
            return await measure_once(os.environ["AZURE_SPEECH_KEY"], pcm)
    elif category == "llm":
        if "openai" in name:
            from measurements.layer3.llm_openai import measure_once
            return await measure_once(os.environ["OPENAI_API_KEY"])
        elif "groq" in name:
            from measurements.layer3.llm_groq import measure_once
            return await measure_once(os.environ["GROQ_API_KEY"])
        elif "mistral" in name:
            from measurements.layer3.llm_mistral import measure_once
            return await measure_once(os.environ["MISTRAL_API_KEY"])
    elif category == "tts":
        if "deepgram" in name:
            from measurements.layer3.tts_deepgram import measure_once
            return await measure_once(os.environ["DEEPGRAM_API_KEY"])
        elif "openai" in name:
            from measurements.layer3.tts_openai import measure_once
            return await measure_once(os.environ["OPENAI_API_KEY"])
        elif "azure" in name:
            from measurements.layer3.tts_azure import measure_once
            return await measure_once(os.environ["AZURE_SPEECH_KEY"])
    return {"error": "unknown provider"}


def capture_one(name: str, host: str, category: str) -> None:
    pcap = OUTDIR / f"capture_{name}_{DATE}.pcap"
    print(f"\n=== {name} (host: {host}) ===")

    print(f"  tcpdump starten...")
    tcpdump = subprocess.Popen(
        ["tcpdump", "-i", "ens5", "-w", str(pcap), "host", host, "-s", "0", "-c", "10000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1)

    print(f"  Layer-3 Call (n=1)...")
    try:
        result = asyncio.run(run_one_call(name, category))
        print(f"  Ergebnis: {result}")
    except Exception as e:
        print(f"  FEHLER: {e}")

    time.sleep(2)
    print(f"  tcpdump stoppen...")
    tcpdump.send_signal(signal.SIGTERM)
    tcpdump.wait(timeout=5)

    size = pcap.stat().st_size if pcap.exists() else 0
    print(f"  Gespeichert: {pcap.name} ({size:,} bytes)")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f"=== Layer-2 Captures: {DATE} ===")
    print(f"Output: {OUTDIR}/")

    for name, host, category in PROVIDERS:
        capture_one(name, host, category)

    print(f"\n=== Alle Captures fertig ===")
    for f in sorted(OUTDIR.glob(f"capture_*_{DATE}.pcap")):
        size = f.stat().st_size
        print(f"  {f.name}: {size:,} bytes")


if __name__ == "__main__":
    main()

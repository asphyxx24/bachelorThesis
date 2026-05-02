"""E2E-Ketten-Messung: STT -> LLM -> TTS sequenziell.

Misst die Gesamtlatenz einer sequenziellen Voice-Pipeline.
Prueft ob das Echtzeit-Budget (<1s) eingehalten wird.

Verwendet standardisierte Inputs (nicht gekettet), um Reproduzierbarkeit
zu gewaehrleisten und variable Textlaenge als Confounding Variable auszuschliessen.
"""

import time

from measurements.layer3 import stt_deepgram as stt, llm_openai as llm, tts_deepgram as tts


async def measure_once(
    stt_key: str,
    llm_key: str,
    llm_base: str,
    tts_key: str,
    voice_id: str,
    pcm_data: bytes,
) -> dict:
    """Fuehrt eine einzelne E2E-Kettenmessung durch: STT -> LLM -> TTS.

    Returns:
        {"stt_ms", "llm_ttft_ms", "llm_ttl_ms", "tts_ttfa_ms", "tts_total_ms",
         "chain_ms", "budget_ok"}
        Bei Fehler: {"error": "..."}
    """
    r_stt = await stt.measure_once(stt_key, pcm_data)
    r_llm = await llm.measure_once(llm_key, llm_base)
    r_tts = await tts.measure_once(tts_key, voice_id)

    has_error = any("error" in r for r in [r_stt, r_llm, r_tts])
    if has_error:
        return {
            "error": (
                f"stt={r_stt.get('error', '-')} "
                f"llm={r_llm.get('error', '-')} "
                f"tts={r_tts.get('error', '-')}"
            ),
        }

    stt_ms = r_stt["total_ms"]
    llm_ttl = r_llm["ttl_ms"]
    tts_total = r_tts["total_ms"]
    chain_ms = stt_ms + llm_ttl + tts_total

    return {
        "stt_ms": round(stt_ms, 1),
        "llm_ttft_ms": round(r_llm["ttft_ms"], 1),
        "llm_ttl_ms": round(llm_ttl, 1),
        "tts_ttfa_ms": round(r_tts["ttfa_ms"], 1),
        "tts_total_ms": round(tts_total, 1),
        "chain_ms": round(chain_ms, 1),
        "budget_ok": chain_ms < 1000,
    }

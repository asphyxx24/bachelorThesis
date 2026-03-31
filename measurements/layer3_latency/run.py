"""Schicht 3 Runner: Tail-Latency-Messungen.

Fuehrt Batch-Messungen fuer STT, LLM, TTS und die E2E-Kette durch.

Verwendung:
  python measurements/layer3_latency/run.py [--n 100] [--tag 09h] [--api stt|llm|tts|e2e|all] [--dry-run]

  --n       Anzahl Messungen pro API (default: 100)
  --tag     Tageszeit-Label fuer Dateiname (z.B. 09h, 12h)
  --api     Nur bestimmte API messen (default: all)
  --dry-run n=3, keine Datei schreiben, Ergebnis auf stdout
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Repo-Root zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from measurements.config import MEASUREMENT_DELAY_S
from measurements.layer3_latency import stt, llm, tts, chain
from measurements.lib.output import now_iso, output_path, write_jsonl
from measurements.lib.stats import compute_stats

# .env aus Repo-Root laden
load_dotenv(Path(__file__).parent.parent.parent / ".env")

FIXTURE_WAV = Path(__file__).parent.parent.parent / "fixtures" / "sample.wav"


# ── Batch-Runner pro API ─────────────────────────────────────────────────────

async def run_stt_batch(n: int, tag: str, dry_run: bool, out_path: Path) -> None:
    api_key = os.environ["DEEPGRAM_API_KEY"]
    pcm_data = stt.load_pcm(FIXTURE_WAV)
    print(f"  STT: n={n}, fixture={FIXTURE_WAV.name} ({len(pcm_data) // 1000} KB)")

    results: list[float] = []
    errors = 0

    for i in range(n):
        result = await stt.measure_once(api_key, pcm_data)
        ts = now_iso()

        if "error" in result:
            errors += 1
            print(f"  STT [{i + 1}/{n}] Fehler: {result['error']}")
        else:
            results.append(result["ttft_ms"])
            if i % 10 == 0:
                print(f"  STT [{i + 1}/{n}] ttft={result['ttft_ms']:.0f} ms")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "stt_ttft", "api": "deepgram", **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    _write_summary("deepgram", "stt_ttft", results, errors, tag, dry_run, out_path)


async def run_llm_batch(n: int, tag: str, dry_run: bool, out_path: Path) -> None:
    api_key = os.environ["REQUESTY_API_KEY"]
    base_url = os.environ.get("REQUESTY_BASE_URL", "https://router.requesty.ai/v1")
    print(f"  LLM: n={n}, endpoint={base_url}")

    ttft_results: list[float] = []
    ttl_results: list[float] = []
    errors = 0

    for i in range(n):
        result = await llm.measure_once(api_key, base_url)
        ts = now_iso()

        if "error" in result:
            errors += 1
            print(f"  LLM [{i + 1}/{n}] Fehler: {result['error']}")
        else:
            ttft_results.append(result["ttft_ms"])
            ttl_results.append(result["ttl_ms"])
            if i % 10 == 0:
                print(f"  LLM [{i + 1}/{n}] ttft={result['ttft_ms']:.0f} ms, ttl={result['ttl_ms']:.0f} ms")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "llm", "api": "requesty", **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    _write_summary("requesty", "llm_ttft", ttft_results, errors, tag, dry_run, out_path)
    _write_summary("requesty", "llm_ttl", ttl_results, errors, tag, dry_run, out_path)


async def run_tts_batch(n: int, tag: str, dry_run: bool, out_path: Path) -> None:
    api_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "P7vsEyTOpZ6YUTulin8m")
    print(f"  TTS: n={n}, voice={voice_id}")

    results: list[float] = []
    errors = 0

    for i in range(n):
        result = await tts.measure_once(api_key, voice_id)
        ts = now_iso()

        if "error" in result:
            errors += 1
            print(f"  TTS [{i + 1}/{n}] Fehler: {result['error']}")
        else:
            results.append(result["ttfa_ms"])
            if i % 10 == 0:
                print(f"  TTS [{i + 1}/{n}] ttfa={result['ttfa_ms']:.0f} ms")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "tts_ttfa", "api": "elevenlabs", **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    _write_summary("elevenlabs", "tts_ttfa", results, errors, tag, dry_run, out_path)


async def run_e2e_batch(n: int, tag: str, dry_run: bool, out_path: Path) -> None:
    stt_key = os.environ["DEEPGRAM_API_KEY"]
    llm_key = os.environ["REQUESTY_API_KEY"]
    llm_base = os.environ.get("REQUESTY_BASE_URL", "https://router.requesty.ai/v1")
    tts_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "P7vsEyTOpZ6YUTulin8m")
    pcm_data = stt.load_pcm(FIXTURE_WAV)
    print(f"  E2E: n={n}, STT -> LLM -> TTS sequenziell")

    chain_results: list[float] = []
    errors = 0
    budget_ok_count = 0

    for i in range(n):
        result = await chain.measure_once(stt_key, llm_key, llm_base, tts_key, voice_id, pcm_data)
        ts = now_iso()

        if "error" in result:
            errors += 1
        else:
            chain_results.append(result["chain_ms"])
            if result["budget_ok"]:
                budget_ok_count += 1
            if i % 10 == 0:
                status = "OK" if result["budget_ok"] else "FAIL"
                print(f"  E2E [{i + 1}/{n}] chain={result['chain_ms']:.0f} ms (budget={status})")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "e2e", **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    if chain_results:
        stats = compute_stats(chain_results)
        budget_compliance = round(budget_ok_count / len(chain_results), 3)
        summary = {
            "ts": now_iso(), "tag": tag, "api": "chain", "metric": "e2e",
            "n": len(chain_results), "errors": errors, "stats": stats,
            "budget_compliance": budget_compliance,
        }
        _output(summary, dry_run, out_path)
        print(f"  E2E: p50={stats['p50']} ms, budget_ok={budget_compliance:.0%}, errors={errors}")


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _output(record: dict, dry_run: bool, out_path: Path) -> None:
    if dry_run:
        print(json.dumps(record, ensure_ascii=False))
    else:
        write_jsonl(out_path, record)


def _write_summary(
    api: str, metric: str, values: list[float], errors: int,
    tag: str, dry_run: bool, out_path: Path,
) -> None:
    if not values:
        return
    stats = compute_stats(values)
    summary = {
        "ts": now_iso(), "tag": tag, "api": api, "metric": metric,
        "n": len(values), "errors": errors, "stats": stats,
    }
    _output(summary, dry_run, out_path)
    print(f"  {metric}: p50={stats['p50']} ms, p95={stats['p95']} ms, errors={errors}")


# ── Main ─────────────────────────────────────────────────────────────────────

async def main_async(args: argparse.Namespace) -> None:
    n = 3 if args.dry_run else args.n
    tag = args.tag or "manual"

    # API-Keys pruefen
    missing = [k for k in ["DEEPGRAM_API_KEY", "REQUESTY_API_KEY", "ELEVENLABS_API_KEY"]
               if not os.environ.get(k)]
    if missing:
        print(f"FEHLER: Fehlende ENV-Variablen: {', '.join(missing)}")
        print("Bitte .env im Repo-Root befuellen (siehe .env.example)")
        sys.exit(1)

    if not FIXTURE_WAV.exists() and args.api in ("stt", "e2e", "all"):
        print(f"FEHLER: {FIXTURE_WAV} fehlt")
        print("Bitte fixtures/create_sample.py ausfuehren oder sample.wav manuell bereitstellen")
        sys.exit(1)

    out_path = output_path("layer3", tag=tag)
    print(f"=== Schicht 3: Tail-Latency === n={n}, tag={tag}, api={args.api}")
    if not args.dry_run:
        print(f"Output: {out_path}")

    if args.api in ("stt", "all"):
        print("\n[STT — Deepgram nova-3]")
        await run_stt_batch(n, tag, args.dry_run, out_path)

    if args.api in ("llm", "all"):
        print("\n[LLM — Requesty / Gemini 2.5 Flash]")
        await run_llm_batch(n, tag, args.dry_run, out_path)

    if args.api in ("tts", "all"):
        print("\n[TTS — ElevenLabs flash_v2_5]")
        await run_tts_batch(n, tag, args.dry_run, out_path)

    if args.api in ("e2e", "all"):
        print("\n[E2E — STT -> LLM -> TTS]")
        await run_e2e_batch(n, tag, args.dry_run, out_path)

    print("\nFertig.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Schicht 3: Tail-Latency-Messungen")
    parser.add_argument("--n", type=int, default=100,
                        help="Anzahl Messungen pro API (default: 100)")
    parser.add_argument("--tag", type=str, default="",
                        help="Tageszeit-Label z.B. 09h, 12h")
    parser.add_argument("--api", type=str, default="all",
                        choices=["stt", "llm", "tts", "e2e", "all"],
                        help="Nur bestimmte API messen (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="n=3, keine Datei schreiben, Ergebnis auf stdout")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

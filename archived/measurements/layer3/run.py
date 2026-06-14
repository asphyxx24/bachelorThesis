"""Schicht 3 Runner: Latenz-Messungen fuer 9 Provider.

Fuehrt Batch-Messungen fuer STT, LLM, TTS und die E2E-Kette durch.

Verwendung:
  python measurements/layer3/run.py [--n 100] [--tag 09h] [--api stt|llm|tts|e2e|all] [--dry-run]

  --n       Anzahl Messungen pro API (default: 100)
  --tag     Tageszeit-Label fuer Dateiname (z.B. 09h, 12h)
  --api     Nur bestimmte Kategorie messen (default: all)
  --dry-run n=3, keine Datei schreiben, Ergebnis auf stdout
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from measurements.config import MEASUREMENT_DELAY_S
from measurements.lib.output import now_iso, output_path, write_jsonl
from measurements.lib.stats import compute_stats

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SAMPLE_WAV = Path(__file__).parent / "sample.wav"

# Provider-Definitionen: (modul_name, api_label, env_keys)
STT_PROVIDERS = [
    ("stt_deepgram",   "deepgram",   ["DEEPGRAM_API_KEY"]),
    ("stt_revai",      "revai",      ["REVAI_API_KEY"]),
    ("stt_azure",      "azure_stt",  ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]),
]

LLM_PROVIDERS = [
    ("llm_openai",  "openai",  ["OPENAI_API_KEY"]),
    ("llm_groq",    "groq",    ["GROQ_API_KEY"]),
    ("llm_mistral", "mistral", ["MISTRAL_API_KEY"]),
]

TTS_PROVIDERS = [
    ("tts_deepgram", "deepgram_tts", ["DEEPGRAM_API_KEY"]),
    ("tts_openai",   "openai_tts",   ["OPENAI_API_KEY"]),
    ("tts_azure",    "azure_tts",    ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]),
]


def _load_module(name: str):
    """Importiert ein Provider-Modul dynamisch."""
    import importlib
    return importlib.import_module(f"measurements.layer3.{name}")


def _check_env(keys: list[str]) -> list[str]:
    return [k for k in keys if not os.environ.get(k)]


# ── Generischer Batch-Runner ────────────────────────────────────────────────

async def run_stt_batch(
    module_name: str, api: str, env_keys: list[str],
    n: int, tag: str, dry_run: bool, out_path: Path,
) -> None:
    missing = _check_env(env_keys)
    if missing:
        print(f"  SKIP {api}: fehlende ENV {missing}")
        return

    mod = _load_module(module_name)
    pcm_data = mod.load_pcm(SAMPLE_WAV)
    print(f"  STT [{api}]: n={n}, sample={SAMPLE_WAV.name} ({len(pcm_data) // 1000} KB)")

    results: list[float] = []
    errors = 0

    for i in range(n):
        result = await mod.measure_once(os.environ[env_keys[0]], pcm_data)
        ts = now_iso()

        if "error" in result:
            errors += 1
            print(f"    [{i + 1}/{n}] Fehler: {result['error']}")
        else:
            results.append(result["ttft_ms"])
            if i % 10 == 0:
                print(f"    [{i + 1}/{n}] ttft={result['ttft_ms']:.0f} ms, connect={result['connect_ms']:.0f} ms")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "stt_ttft", "api": api, **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    _write_summary(api, "stt_ttft", results, errors, tag, dry_run, out_path)


async def run_llm_batch(
    module_name: str, api: str, env_keys: list[str],
    n: int, tag: str, dry_run: bool, out_path: Path,
) -> None:
    missing = _check_env(env_keys)
    if missing:
        print(f"  SKIP {api}: fehlende ENV {missing}")
        return

    mod = _load_module(module_name)
    print(f"  LLM [{api}]: n={n}")

    ttft_results: list[float] = []
    ttl_results: list[float] = []
    errors = 0

    for i in range(n):
        result = await mod.measure_once(os.environ[env_keys[0]])
        ts = now_iso()

        if "error" in result:
            errors += 1
            print(f"    [{i + 1}/{n}] Fehler: {result['error']}")
        else:
            ttft_results.append(result["ttft_ms"])
            ttl_results.append(result["ttl_ms"])
            if i % 10 == 0:
                print(f"    [{i + 1}/{n}] ttft={result['ttft_ms']:.0f} ms, ttl={result['ttl_ms']:.0f} ms")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "llm", "api": api, **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    _write_summary(api, "llm_ttft", ttft_results, errors, tag, dry_run, out_path)
    _write_summary(api, "llm_ttl", ttl_results, errors, tag, dry_run, out_path)


async def run_tts_batch(
    module_name: str, api: str, env_keys: list[str],
    n: int, tag: str, dry_run: bool, out_path: Path,
) -> None:
    missing = _check_env(env_keys)
    if missing:
        print(f"  SKIP {api}: fehlende ENV {missing}")
        return

    mod = _load_module(module_name)
    print(f"  TTS [{api}]: n={n}")

    results: list[float] = []
    errors = 0

    for i in range(n):
        result = await mod.measure_once(os.environ[env_keys[0]])
        ts = now_iso()

        if "error" in result:
            errors += 1
            print(f"    [{i + 1}/{n}] Fehler: {result['error']}")
        else:
            results.append(result["ttfa_ms"])
            if i % 10 == 0:
                print(f"    [{i + 1}/{n}] ttfa={result['ttfa_ms']:.0f} ms, connect={result.get('connect_ms', 0):.0f} ms")

        record = {"ts": ts, "tag": tag, "run": i, "metric": "tts_ttfa", "api": api, **result}
        _output(record, dry_run, out_path)

        if i < n - 1:
            await asyncio.sleep(MEASUREMENT_DELAY_S)

    _write_summary(api, "tts_ttfa", results, errors, tag, dry_run, out_path)


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
    print(f"    {metric}: p50={stats['p50']} ms, p95={stats['p95']} ms, errors={errors}")


# ── Main ─────────────────────────────────────────────────────────────────────

async def main_async(args: argparse.Namespace) -> None:
    n = 3 if args.dry_run else args.n
    tag = args.tag or "manual"

    if not SAMPLE_WAV.exists() and args.api in ("stt", "e2e", "all"):
        print(f"FEHLER: {SAMPLE_WAV} fehlt")
        print("Siehe measurements/layer3/SAMPLE_WAV.md")
        sys.exit(1)

    out_path = output_path("layer3", tag=tag)
    print(f"=== Schicht 3: Latenz-Messungen === n={n}, tag={tag}, api={args.api}")
    if not args.dry_run:
        print(f"Output: {out_path}")

    if args.api in ("stt", "all"):
        for module_name, api, env_keys in STT_PROVIDERS:
            print(f"\n[STT — {api}]")
            await run_stt_batch(module_name, api, env_keys, n, tag, args.dry_run, out_path)

    if args.api in ("llm", "all"):
        for module_name, api, env_keys in LLM_PROVIDERS:
            print(f"\n[LLM — {api}]")
            await run_llm_batch(module_name, api, env_keys, n, tag, args.dry_run, out_path)

    if args.api in ("tts", "all"):
        for module_name, api, env_keys in TTS_PROVIDERS:
            print(f"\n[TTS — {api}]")
            await run_tts_batch(module_name, api, env_keys, n, tag, args.dry_run, out_path)

    print("\nFertig.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Schicht 3: Latenz-Messungen (9 Provider)")
    parser.add_argument("--n", type=int, default=100,
                        help="Anzahl Messungen pro Provider (default: 100)")
    parser.add_argument("--tag", type=str, default="",
                        help="Tageszeit-Label z.B. 09h, 12h")
    parser.add_argument("--api", type=str, default="all",
                        choices=["stt", "llm", "tts", "all"],
                        help="Nur bestimmte Kategorie messen (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="n=3, keine Datei schreiben, Ergebnis auf stdout")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

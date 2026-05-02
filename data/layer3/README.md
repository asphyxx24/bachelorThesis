# Layer 3 — Latency Data

## Datenstruktur

Jede JSONL-Datei (`YYYY-MM-DD_HHh.jsonl`) enthält Records **mehrerer Provider** gemischt.
Das `api`-Feld im Record identifiziert den Provider.

Beispiel:
```json
{"ts": "...", "api": "deepgram",   "metric": "stt_ttft", "connect_ms": 472.0, ...}
{"ts": "...", "api": "elevenlabs", "metric": "tts_ttfa", ...}
{"ts": "...", "api": "requesty",   "metric": "llm",      ...}  ← DEPRECATED
{"ts": "...", "api": "chain",      "metric": "e2e",      ...}
```

## ⚠️ Deprecated: `api="requesty"`

**Records mit `api="requesty"` sind für die finale Thesis NICHT zu verwenden.**

- Requesty ist ein API-Proxy (→ Gemini 2.5 Flash), nicht der tatsächlich gemessene Provider.
- Die LLM-Provider-Matrix wurde auf OpenAI / Groq / Anthropic umgestellt (siehe `CLAUDE.md`).
- Die Requesty-Records (≈17.446 Stück) bleiben im Datensatz als historischer Kontext,
  müssen aber in jeder Analyse ausgefiltert werden:

```python
df = df[df["api"] != "requesty"]
```

## Aktuell valide Provider (Stand 2026-04-23)

| `api`        | Kategorie | Status                      |
|--------------|-----------|-----------------------------|
| `deepgram`   | STT       | valide (29 Tage, ~17k Records) |
| `elevenlabs` | TTS       | valide (29 Tage, ~17k Records) |
| `chain`      | E2E       | valide (sequenzielle Pipeline)  |
| `requesty`   | LLM       | **DEPRECATED** — nicht nutzen   |

## TODO (Phase 1 Roadmap)

- [ ] `run.py`: Requesty-Measurement deaktivieren
- [ ] Messcode für OpenAI / Groq / Anthropic hinzufügen
- [ ] Messcode für AssemblyAI / Speechmatics / Cartesia / Polly hinzufügen

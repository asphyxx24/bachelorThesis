# Befunde & Argumente — Sammlung (Arbeitsdokument)

> Stichpunkte + Belege, **kein Fließtext**. Wird am Ende zur Thesis ausformuliert.
> Datenbasis: Juni-Kampagne (`data/`, 01.–07.06.2026). Zahlen aus dem **Notebook-Re-Run vom 2026-06-08** (7/8 NB auf Juni gerechnet; NB02 PCAP noch in Reparatur).
> **Status:** ✅ belegt (Juni) · 🔄 offen/in Arbeit · 💡 Hypothese

## Übersicht

| # | Befund (Kurz) | Schicht | Beleg | Status |
|---|---------------|---------|-------|--------|
| V1 | Daten cross-vantage reproduzierbar (8/9 RTT <1 ms) | Validierung | `data/validation_2026-06-08/` | ✅ |
| V2 | TLS-Versionen 7/7 exakt (Rev.ai TLS 1.2, Rest 1.3) | Validierung | `layer1_extra/tls.csv` | ✅ |
| V3 | Keine 1:1-Kopie; interne RTT-Struktur konsistent | Validierung | this session | ✅ |
| F1 | Drei RTT-Klassen (CF ~1 / Azure-IT ~10 / US ~140 ms) | L1 | 01_ping_rtt_boxplot | ✅ |
| F2 | Rev.ai TLS 1.2 → +1-RTT-Penalty (+153 ms) | L1 | 06_tls12_penalty | ✅ |
| F3 | DNSSEC 0/6 Zonen signiert (7 Endpoints, microsoft.com doppelt) | L1 | `dnssec.csv` | ✅ |
| F4 | Cloudflare-Fronting 4/9 (groq/mistral/openai) ~1 ms Edge | L2 | 02_communication_matrix | ✅ |
| F5 | Keine Nebenkommunikation (1 Call = 1 Backend-ASN) | L2 | 02_communication_matrix | ✅ |
| F6 | **Engine > Netzwerk**: Deepgram(US) schlägt Azure(EU) bei STT | L3 | 03_stt_connect_anteil | ✅ |
| F7 | Groq LPU schnellster LLM (TTFT 68 ms) | L3 | 04_llm_ttft_cdf | ✅ |
| F8 | TTS-Inversion: Azure(EU) gewinnt (TTFA 67 ms) | L3 | 05_tts_ttfa_cdf | ✅ |
| F9 | Cross-Layer-Modell `connect ≈ N_RTT × ping` (r=0.999) | L1+L3 | 06_cross_layer_scatter | ✅ |
| F10 | Cold-Start-Pipeline verfehlt 1 s (0/27 Kombis) | E2E | 07_e2e_budget | ✅ |

---

## Detail (Juni-Zahlen)

### V1 — Daten unabhängig validiert (Kern-Antwort auf Prof-Punkt „validieren")
- Frische Messung von EC2 i-045 (eu-central-1, 2026-06-08) reproduziert 8/9 Provider-RTTs auf <1 ms; `connect_ms` (L3) bei allen reproduziert; Verteilungen ±3 % zur Mai-Kampagne.
- **Caveat:** Deepgram (Anycast) weicht ab — Routing-Eigenschaft, kein Mess-Fehler.

### F1 — Drei RTT-Klassen (Juni-Median ICMP)
- Cloudflare (openai 1.2 / groq 1.4 / mistral 1.0 ms) · Azure Italy North (STT 10.3 / TTS 10.4 ms) · US (Deepgram 137.8; Rev.ai 144.2 ms TCP, ICMP geblockt).

### F2 — TLS-1.2-Penalty Rev.ai
- Rev.ai TLS-1.2-Handshake 293.7 ms ≈ 2 RTT; TLS-1.3-Provider ~1 RTT. **Gemessene Penalty +153.3 ms** (≈ 1 RTT = 144.2 ms). Vantage-unabhängig (PCAP bestätigt).

### F6 — Engine schlägt Netzwerknähe (STT) ← **stärkster, kontraintuitiver Befund**
- **Juni-Median:** Deepgram (US, RTT 138) **TTFT 574.6 ms** vs. Azure (EU, RTT 10) **TTFT 1715.2 ms**.
- Connect-Anteil am Cold-Start: Deepgram 42.5 % (Netzwerk-dominiert) vs. Azure 2.8 % (Server-dominiert, 97 %).
- **→ FF/C3:** Nicht die Region entscheidet, sondern die Backend-Engine.

### F7 — Groq LPU schnellster LLM
- **Juni-Median TTFT:** Groq **68.2 ms** · Mistral 230.6 ms · OpenAI 541.5 ms (Groq ~3.4× schneller als Mistral, ~7.9× als OpenAI).
- **gen_ms (reine Generierung):** Groq 6.8 ms vs OpenAI 89.2 ms — LPU-Vorteil.
- **Caveat:** Groq 32,9 % Rate-Limit-Errors (Free Tier, ~67 Runs/Slot) — Befund, kein Datenfehler.

### F8 — TTS-Inversion: EU gewinnt
- **Juni-Median TTFA:** Azure (EU) **66.6 ms** · Deepgram (US) 556.5 ms · OpenAI 954.2 ms (Azure ~8.4× / ~14.3× schneller).
- Azure-Vorteil ist **kombiniert**: niedriger connect (EU, 33 ms) UND schnelle Engine (proc 33 ms). OpenAI: niedrigster connect (9 ms) durch langsamste Engine (944 ms) aufgezehrt.

### F9 — Cross-Layer-Modell ✅ (Juni bestätigt)
- **Juni-Fit (4 direkte TLS-1.3-Punkte):** `connect_ms ≈ N_RTTs × ping + k`, **slope=1.006, intercept=10.7 ms, r=0.999** (Mai: 1.013 / 8.5 / 0.9992 → stabil).
- **N_RTTs:** HTTPS TLS 1.3 = 2 · WebSocket TLS 1.3 = 3 · WebSocket TLS 1.2 = 4.
- **overhead_k pro Provider (Juni):** Deepgram STT +11.5 · Azure STT +18.7 · Rev.ai +20.5 ms.
- **Caveat:** bricht bei Cloudflare-fronted Providern (effektives N_RTTs 7–180 = Unsinn → Edge-RTT ~1 ms misst nicht den Backend).

### F10 — E2E Cold-Start verfehlt 1 s ✅ (Juni bestätigt)
- **0/27 Kombinationen < 1000 ms** (Cold-Start Streaming).
- **Beste Streaming-Kombi:** Deepgram + Groq + Azure = **1134 ms** (stt_conn 425 + stt_ttft 575 + llm 68 + tts 67).
- **Batch-Szenario gestrichen (A7):** Der frühere „Streaming spart 3350 ms"-Vergleich war ein Mess-Artefakt — Deepgrams `total_ms` enthält einen ~3,4 s WS-Close-Leerlauf-Tail (kein Audio-Transfer, `send_ms`≈137 ms), Azure/Rev.ai brechen beim ersten Final ab. `total_ms` daher nur provider-intern, E2E nur Streaming.
- **STT dominiert** im Schnitt **67,4 %** der E2E-Latenz (27/27 Kombis STT-dominiert).
- **Warm-Schätzung** (ohne stt_connect): Deepgram+Groq+Azure ≈ **666 ms** → unter 1 s nur mit persistenten Verbindungen möglich (Future Work).

---

## Anomalien/Caveats (→ `data/processed/known_anomalies.md`)
- Fehlerraten Juni: **Groq 32,9 %** · **Rev.ai 10,2 %** · Mistral 4,0 % · Rest ≤0,05 %.
- Vantage Point: Kampagne aus anderem AWS-Account (eu-central-1); validiert.
- `processed/layer1_tls.csv` leer → TLS-Daten aus `layer1_extra/tls.csv`.
- Warm-up-Effekt: keiner (alle slopes ~0, nicht signifikant) → Cold-Start-Methodik sauber.

---

## Stand & was noch fehlt
- [x] Notebooks auf **Juni** neu gerechnet — **7/8** (00,01,03,04,05,06,07). 🔄 **NB02 (PCAP) noch reparieren** (Mai-Glob, tshark lokal fehlt, Rev.ai-Capture-Error).
- [x] F5, F9, F10 mit Juni-Zahlen belegt.
- [ ] **106 stale Mai-Referenzen** in Notebook-Markdown fixen (Audit-Liste liegt vor: Datum, Slot-Zahlen, alte Ergebniszahlen).
- [ ] Figures schärfen: jede macht **eine** Aussage zur FF (Titel = Botschaft).
- [ ] Statistische Absicherung: CIs/Streuung statt nur Punktschätzer.

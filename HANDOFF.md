# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-26 (Session: NB 07 E2E-Pipeline, Commit, Prof-Meeting-Vorbereitung)

## TL;DR

**Analyse-Phase vollständig abgeschlossen.** Alle 8 Notebooks (NB 00–07) fertig, 35 Figures, 7 Statistik-Tabellen. Nächste Phase: **Thesis schreiben (Phase 12)**. Phase 11 (E2E-Validierung auf EC2) wird übersprungen — Median-Addition ist methodisch ausreichend, Limitation wird in der Thesis benannt.

---

## Drei Kernbefunde (das Wichtigste für Prof und Thesis)

### 1. Cross-Layer-Modell (NB 06) — Kernbefund der Arbeit
```
connect_ms ≈ N_RTTs × ping_median + k
slope = 1.013, intercept = 8.5 ms, r = 0.9992
```
Gilt für die 4 direkt-gehosteten Provider (Deepgram STT/TTS, Azure STT/TTS).  
N_RTTs: HTTPS TLS 1.3 = 2, WebSocket TLS 1.3 = 3, WebSocket TLS 1.2 = 4 (+1 RTT Penalty).  
**Bei Cloudflare-fronted Providern (4/9) bricht das Modell** — Edge-RTT ~1 ms, Backend nicht messbar.

### 2. Engine-Speed schlägt Netzwerknähe (NB 03 + NB 05)
- **STT:** Deepgram (USA, RTT 140 ms) schlägt Azure (EU, RTT 11 ms) — 587 ms vs 1 719 ms TTFT.  
  Azure spart 130 ms Netzwerk, verliert aber 1 130 ms durch langsamere Engine.
- **TTS (Inversion):** Azure (EU) gewinnt mit 65 ms TTFA. Deepgram 551 ms, OpenAI 938 ms.  
  → Welcher Layer "gewinnt", hängt allein von der Backend-Engine ab, nicht vom Standort.

### 3. Cold-Start-Voice-Pipeline verfehlt 1-Sekunde (NB 07)
```
Beste Kombination (Streaming):  deepgram + groq + azure = 1 157 ms
Beste Kombination (Batch):      azure + groq + azure   = 1 901 ms
0/27 Kombinationen unter 1 000 ms (Cold-Start)
```
Mit persistenten Verbindungen (Warm): ~676 ms → **unter 1 s möglich, aber kein Cold-Start**.

---

## Stand der Notebooks

| NB | Status | Hauptbefund | Figures |
|----|--------|-------------|---------|
| 00 Data Quality | FERTIG | 0 % NaN, Rev.ai 10 % Error-Rate | — |
| 01 Layer-1 | FERTIG | 3 RTT-Klassen, Rev.ai TLS 1.2, 0/6 DNSSEC | 3 |
| 02 PCAP | FERTIG | Cloudflare 4/9, Null Nebenkommunikation | 2 |
| 03 STT | FERTIG | Deepgram schnellster trotz USA | 6 |
| 04 LLM | FERTIG | Groq 13× schneller (LPU), 35 % Groq-Errors | 8 |
| 05 TTS | FERTIG | Azure TTFA 65 ms gewinnt klar | 7 |
| 06 Cross-Layer | FERTIG | r=0.9992, TLS-1.2-Penalty +142 ms | 5 |
| 07 E2E-Pipeline | FERTIG | 0/27 unter 1 s, STT dominiert (Ø 68 %) | 4 |

---

## Offene Phasen

| Phase | Was | Empfehlung |
|-------|-----|------------|
| ~~Phase 10 (Analyse)~~ | ~~NB 00–07~~ | **Fertig** |
| Phase 11 (E2E-Validierung) | Echte Pipeline-Runs auf EC2 | **Überspringen** — Limitation in Thesis benennen |
| **Phase 12 (Thesis schreiben)** | ~3–4 Wochen Schreibarbeit | **Nächster Schritt** |

---

## Prof-Meeting-Vorbereitung (2026-05-26)

### Empfohlene Figures zum Zeigen (Priorität hoch → niedrig)

1. **`06_cross_layer_scatter.png`** — DER Kernbefund. Scatter ping × N_RTTs vs connect_ms, r=0.999. Klar, überzeugend, direkt antwort auf "Was ist die Contribution?".
2. **`07_e2e_budget.png`** — 1-Sekunden-Budget-Plot. Alle 27 Kombinationen, 0/27 unter 1 s. Praktische Relevanz sofort sichtbar.
3. **`03_stt_connect_anteil.png`** — Engine > Netzwerk bei STT. Deepgram (USA) schlägt Azure (EU). Überraschendster Befund.
4. **`02_communication_matrix.png`** — Cloudflare-Fronting bei 4/9 Providern. Erklärt warum das Modell dort bricht.
5. **`06_tls12_penalty.png`** — Rev.ai TLS 1.2 Penalty, +142 ms exakt quantifiziert.

### Antworten auf erwartete Prof-Fragen

**"Warum Cold-Start?"**  
→ Cold-Start misst den Overhead einer neuen Gesprächssession. Relevant für: jeder Kaltstart einer Voice-App, nach Inaktivität, bei Serverless-Deployments. Warm-Connection-Verhalten ist Future Work.

**"Was ist die Contribution?"**  
→ Drei Beiträge: (1) Cross-Layer-Modell empirisch validiert (r=0.999), (2) Cloudflare-Fronting-Effekt quantifiziert, (3) Engine-Speed > EU-Region als nachgewiesener Gegensatz zur intuitiven Erwartung.

**"Warum nur 9 Provider?"**  
→ Kostenlimit + methodische Konsistenz (alle mit identischen Inputs, alle Cold-Start, alle Raw-WebSocket bei STT). Rev.ai ersetzte AssemblyAI wegen inkompatibler Streaming-Semantik.

**"Validierung?"**  
→ Layer-2-PCAP als unabhängige Cross-Validierung der Layer-3-Messungen. TLS-Versionen und Submetriken stimmen über beide Methoden überein.

---

## Kerndaten (Thesis-Referenz)

### Provider-Matrix mit Messwerten

| Provider | Kategorie | RTT | Hosting | connect_ms | Hauptmetrik |
|----------|-----------|-----|---------|-----------|-------------|
| Deepgram | STT | 140 ms | USA (Anycast, AS 12129) | 437 ms | ttft = 587 ms |
| Rev.ai | STT | 142 ms | USA (AWS, AS 16509) | 593 ms | ttft = 1 404 ms |
| Azure | STT | 11 ms | Italy North (AS 8075) | 48 ms | ttft = 1 719 ms |
| Groq | LLM | 1 ms | Cloudflare FRA (AS 13335) | 9 ms | ttft = 67 ms |
| Mistral | LLM | 1 ms | Cloudflare FRA (AS 13335) | 9 ms | ttft = 232 ms |
| OpenAI | LLM | 1 ms | Cloudflare FRA (AS 13335) | 9 ms | ttft = 526 ms |
| Azure | TTS | 11 ms | Italy North (AS 8075) | 34 ms | ttfa = 65 ms |
| Deepgram | TTS | 140 ms | USA (Anycast, AS 12129) | 284 ms | ttfa = 551 ms |
| OpenAI | TTS | 1 ms | Cloudflare FRA (AS 13335) | 9 ms | ttfa = 938 ms |

### E2E Top-5 (Streaming Cold-Start, Median)

| Rang | Kombination | E2E (ms) |
|------|-------------|----------|
| 1 | deepgram + groq + azure | 1 157 |
| 2 | deepgram + mistral + azure | 1 322 |
| 3 | deepgram + openai + azure | 1 616 |
| 4 | deepgram + groq + deepgram | 1 642 |
| 5 | deepgram + mistral + deepgram | 1 807 |

---

## Wichtige Konventionen (für Phase 12)

- **Metriken STT:** `ttft_ms` ist POST-connect. Gesamt-Cold-Start = `connect_ms + ttft_ms`.
- **Metriken LLM/TTS:** `ttft_ms` und `ttfa_ms` sind connect-inklusiv (separate `_measure_connect()`).
- **Figures einbetten:** immer PDF-Version aus `analysis/figures/NN_topic/pdf/`.
- **Tabellen:** `analysis/tables/` — CSV-Dateien, direkt als LaTeX-Input nutzbar.
- **Figures-Naming:** `NN_name.pdf` — NN = Notebook-Nummer, name = Beschreibung.

---

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Provider-Matrix, Metrik-Definitionen |
| `HANDOFF.md` | **Diese Datei** |
| `analysis/README.md` | Quick-Reference aller Notebooks + Befunde |
| `data/processed/known_anomalies.md` | Bekannte Anomalien (Rev.ai Errors, Groq Rate-Limit, Mistral Stress-Slots) |
| `notes/literature.md` | Literatursammlung |
| `notes/briefing_prof.md` | Briefing für Prof. Wählisch |
| `analysis/tables/` | Alle Statistik-CSVs (03–07) |
| `analysis/figures/` | Alle Plots (PNG + PDF, nach Notebook geordnet) |

---

## AWS EC2 (nur bei Bedarf für Phase 11)

| | Wert |
|-|------|
| Instance ID | `i-045a2d0eeb338b290` |
| Status | **STOPPED** (seit 2026-05-24) |
| Start | `aws ec2 start-instances --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |
| SSH | `ssh -i ~/.ssh/thesis-key.pem ubuntu@<IP-nach-Start>` |

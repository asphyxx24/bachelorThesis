# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-06-09 (Session: **Welle 1 komplett — A7 Batch gestrichen + A6 Monte-Carlo + A8 Verfügbarkeit, alles in NB07**)

## TL;DR

**Welle 1 der Audit-Punkte abgeschlossen (alle in NB07, fehlerfrei neu gerendert):** **A7** Batch-Szenario gestrichen (war ein `total_ms`-Tail-Artefakt) → nur noch Streaming-E2E. **A6** Monte-Carlo-Faltung validiert die Median-Addition (Δ<1,4 %) und zeigt p90/p95 + „nur ~24 % der Einzel-Runs <1 s". **A8** Verfügbarkeit/Joint-Completion → Latenz-vs-Zuverlässigkeit-Pareto-Front (LLM ist der Hebel: groq 67 % → mistral 96 % → openai 99,9 %). Vorgeschichte: großer Prüfer-Audit + Reframe auf **„Engine schlägt Geografie"**. **Nächster Schritt: Welle 2 (A10 Mistral-Degen, A12 Phantom-Slot), dann schreiben.**

---

## ⭐ HIER MORGEN WEITERMACHEN

**Welle 1 (E2E-Robustheit) ✅ KOMPLETT (2026-06-09) — A7 + A6 + A8 alle erledigt:**
1. ✅ **A7: Batch-Szenario gestrichen.** NB07 nur noch Streaming-E2E (`batch_e2e`/`stt_total_ms` raus, `07_e2e_stream_vs_batch`-Figure gelöscht); `total_ms`-Tail-Artefakt dokumentiert in `known_anomalies.md §5.1` + `findings.md F10`.
2. ✅ **A6: Monte-Carlo statt Median-Addition.** NB07 §6 (N=20 000, seed=42). median-of-sum weicht <1,4 % ab (validiert), aber p90/p95 = 1273/1350 ms & nur ~24 % der Einzel-Runs < 1 s. `07_pipeline_montecarlo.csv` + `07_e2e_montecarlo` + Befund 8.6.
3. ✅ **A8: Verfügbarkeit/Joint-Completion.** NB07 §7 — Verfügbarkeit je Provider (Groq 67,1 %, Rev.ai 89,8 %, Mistral 96,0 %, Rest ≥99,96 %). Latenz-vs-Zuverlässigkeit-Pareto-Front (LLM ist der Hebel): groq 1134 ms/67 % → mistral 1297/96 % → openai 1608/99,9 %. `07_pipeline_availability.csv` + `07_e2e_availability` + Befund 8.7.

**→ JETZT: Welle 2** — **A10** (Mistral-Degeneration aus Roh-JSONL — `token_count` nicht im Parquet) + **A12** (Phantom-57.-Slot: nach `tag` statt Timestamp gruppieren). Danach **Welle 3** (A4 STT-Pacing-Sensitivität, analytisch). Dann **Schreiben** (Methodik-Kapitel zuerst).

> ⚠️ Vor NB07/NB04-Edits: sicherstellen, dass der **parallele Chat** nicht mitten in `analysis/` steckt (Kollisionsgefahr).
> ⚠️ Uncommitted: diese Session hat viele Dateien geändert, **noch nicht committet** — ggf. `git status` / committen.

---

## Der Reframe (das Wichtigste — Details: `STANDORTBESTIMMUNG_2026-06-08.md`)

**Neue Contribution-Reihenfolge** (im `notes/thesis_outline.md` schon umgesetzt):
- **C1 (Kern) — „Engine schlägt Geografie":** Aus EU-Sicht dominiert die Backend-Engine, nicht die Netzwerknähe. Schärfster Beleg: **STT/TTS-Inversion** desselben Providers (Azure verliert bei STT, gewinnt bei TTS).
- **C2 — Drei-Schichten-Methodik + Cloudflare-Grenze** (4/9).
- **C3 (Baustein, NICHT Headline) — Ping-basierte connect-Klassen-Heuristik** (n=4, r bewusst nicht als Gütemaß).
- **Neuer Arbeitstitel:** „Engine schlägt Geografie: Netzwerk-, Protokoll- und Latenzanalyse kommerzieller Cloud-AI-APIs einer Echtzeit-Voice-Pipeline aus EU-Perspektive" (noch nicht angemeldet → frei änderbar).
- **Geschärfte Forschungsfrage:** „In welchem Maße erklären Netzwerkeigenschaften *im Vergleich zur Engine* die Latenz…" (in beide Richtungen beantwortbar).

## Audit-Punkte-Status (Triage der 14 Findings)

| Bucket | Punkte | Stand |
|---|---|---|
| ✅ **Erledigt** | A1-Zahlen · A3-Doku · connect_ms-Submetrik · 13 Stale-Werte · NB07 „14→7 Tage" · **Welle 1: A7 Batch · A6 Monte-Carlo · A8 Verfügbarkeit** (09.06.) | Welle 1 komplett 2026-06-09 |
| 🔧 **Analyse — NÄCHSTER SCHRITT** | **A10** Mistral-Degen · **A12** Phantom-Slot (Welle 2) · **A4** STT-Pacing (Welle 3) | Welle 2 / 3 |
| ✍️ **Schreibphase** | A2 Limitations · A5 1s-Budget vs Jacoby · A9 Layer-2 nur Struktur · A11 token=Chunk · A13 TTS-Playback | beim Schreiben |
| ❌ **Nicht machbar → Limitation** | A14 WER | keine Transkript-Texte gespeichert (nur Längen) |

Vollständige Findings + Belege: **`PRUEFER_AUDIT_2026-06-08.md`** (§4 Angriffsfläche, §7 To-Do, §8 Verständnis-Checkliste).

## Was diese Session gemacht wurde

- **Audit** (`PRUEFER_AUDIT_2026-06-08.md`) + **Strategie-Urteil** (`STANDORTBESTIMMUNG_2026-06-08.md`) erstellt.
- **Spickzettel fürs Prof-Gespräch** (`notes/spickzettel_prof.md`) — komplette BA in Stichpunkten, inkl. erwartete Prof-Fragen.
- **Reframe** in `notes/thesis_outline.md` (Contribution-Reihenfolge, Titel, geschärfte RQ, Methodik-Härtung).
- **13 Stale-Mai-Werte** auf Juni synchronisiert (CLAUDE/README/analysis-README/findings/literature/cost/known_anomalies).
- **CLAUDE.md Submetrik-Tabelle** aus Juni-PCAP neu gerechnet (Azure-„265 ms Server" war Fehlinterpretation → korrekt ~49 ms).
- **NB07** „14 Tage"→„7 Tage" im Figure-Untertitel, Notebook neu ausgeführt, Figure verifiziert.

## Drei Kernbefunde (Juni-Zahlen, NEUE Reihenfolge)

1. **Engine schlägt Netzwerknähe (Kern):** Deepgram (US, RTT 138) STT-TTFT **575 ms** < Azure (EU, RTT 10) **1715 ms** (56/56 Slots). TTS-Inversion: Azure gewinnt TTFA **67 ms** vs Deepgram 557 vs OpenAI 954.
2. **Cross-Layer-Modell (Baustein):** `connect_ms ≈ N_RTTs × ping + k`, slope 1.006, k 10.7 ms (4 direkte Provider, n=4). Bricht bei Cloudflare (4/9).
3. **Cold-Start-Pipeline verfehlt 1 s:** beste Streaming-Kombi deepgram+groq+azure **1134 ms**, 0/27 < 1000 ms. Warm ~666 ms. *(A6 erledigt: Monte-Carlo bestätigt Median-Addition <1,4 %; p90/p95 = 1273/1350 ms, nur ~24 % Einzel-Runs < 1 s.)*

## Datenstand

- **Maßgeblich:** `data/` — Juni-Kampagne, 7 Tage × 8 Slots = 56 Slots, n=100/Provider/Slot, 0 % NaN.
- **Mai-Kampagne:** archiviert/gelöscht — nur in git-Historie (`e380b80`).
- **Validierung (2026-06-08, EC2 i-045):** L1 8/9 Provider <1 ms reproduziert, TLS 7/7 exakt, L2 PCAP-Struktur bestätigt, L3 connect_ms reproduziert.
- **Vantage-Point-Caveat:** Juni-L3-Kampagne lief auf **anderem AWS-Account** (eu-central-1). Nur Deepgram (Anycast) weicht ab. Siehe `known_anomalies.md` Abschnitt 4.

## Figures-Status

- Alle Figures (NB 00–07) sind **auf Juni-Daten** — aber **01–06 aus früheren Sessions**, **nicht heute** neu gerendert.
- **Heute neu gerendert: nur NB07** (3 Figures, wegen „14→7 Tage").
- **Morgen optional:** NB 01–06 zur Sicherheit frisch neu rendern (sind aber inhaltlich korrekt).
- Reframe-Folge: beim Schreiben „r=0.999" aus den Cross-Layer-Plot-Titeln nehmen (A1).

## Offene Entscheidungen

- ✅ **A7 entschieden (09.06.):** Batch gestrichen (nur noch Streaming-E2E).
- **Scope:** Welle 1 zuerst *(Empfehlung)* vs. alle drei Wellen am Stück.

## Cleanup-Erinnerungen (extern, nur du)

- **AWS Access Key** (User `claude`, Account 365916940756) **löschen**.
- **AWS Console-Passwort ändern.**
- **Andere-Account-Instanz** prüfen/stoppen (falls Juni-Mess-Instanz noch läuft → Kosten).

## AWS EC2 (Validierungs-Instanz)

| | Wert |
|-|------|
| Instance ID | `i-045a2d0eeb338b290` (thesis-measurement, eu-central-1b) |
| Status | **STOPPED** (nach Validierung 2026-06-08) |
| Zugang | AWS CLI (`.venv/bin/aws`) + SSH-Key `~/.ssh/thesis-ec2` |
| Start | `.venv/bin/aws ec2 start-instances --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `PRUEFER_AUDIT_2026-06-08.md` | **Technischer Audit** — 14 Findings, To-Do, Verständnis-Checkliste |
| `STANDORTBESTIMMUNG_2026-06-08.md` | **Strategie-Urteil** — Contribution, Framing, Go/Pivot |
| `notes/spickzettel_prof.md` | **Prof-Gespräch-Spickzettel** (BA in Stichpunkten) |
| `notes/thesis_outline.md` | Kapitelgerüst (gerafmt) |
| `notes/findings.md` | Befunde mit Juni-Zahlen |
| `CLAUDE.md` | Projektkontext, Provider-Matrix, Metrik-Definitionen |
| `data/processed/known_anomalies.md` | Juni-Anomalien + Vantage-Point-Caveat |
| `measurements/` | Mess-Skripte (Methodik, Reproduzierbarkeit) |

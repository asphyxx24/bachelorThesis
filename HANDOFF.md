# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-06-08 (Session: **Multi-Agent-Audit + strategischer Reframe + Doku-Sync + Submetrik/Figure-Fix**)

## TL;DR

Großer **Prüfer-Audit** (49 Agenten, read-only) + **Strategie-Urteil** gelaufen. Ergebnis: Substanz tragfähig, aber **falsch gerahmt** → **Contribution umgedreht** (Reframe): **„Engine schlägt Geografie" ist jetzt der Kernbefund**, das Cross-Layer-Modell (r=0.999, n=4) wird zum Methoden-Baustein. Doku-Zahlen auf Juni synchronisiert, Submetrik-Tabelle + NB07-Figure gefixt. **Nächster Schritt: die inhaltlichen Audit-Punkte abarbeiten (Welle 1), dann schreiben.**

---

## ⭐ HIER MORGEN WEITERMACHEN

**Audit-Analyse-Punkte, Welle 1 (E2E-Robustheit — höchster Hebel):**
1. **Zuerst A7 entscheiden** (offen, AskUserQuestion gestern abgebrochen): Batch-Szenario **streichen** (Empfehlung — der „spart 3350 ms" ist ein Deepgram-Schleifen-Artefakt) ODER Deepgram-Tail bereinigen.
2. **A6 — Monte-Carlo statt Median-Addition:** in NB07 die empirischen Verteilungen falten → median-of-sum + p90/p95 (entschärft „Mediane sind nicht additiv").
3. **A8 — Verfügbarkeits-Spalte:** neben jeden E2E-Latenz-Median die Joint-Completion-Probability (Groq nur ~67 % erfolgreich).

Danach **Welle 2** (A10 Mistral-Degeneration aus Roh-JSONL, A12 Phantom-57.-Slot) und **Welle 3** (A4 STT-Pacing-Sensitivität). Dann **Schreiben** (Methodik-Kapitel zuerst).

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
| ✅ **Erledigt** | A1-Zahlen · A3-Doku · connect_ms-Submetrik (Juni-PCAP) · 13 Stale-Werte · NB07 „14→7 Tage" | fertig diese Session |
| 🔧 **Analyse — NÄCHSTER SCHRITT** | **A6** Monte-Carlo · **A8** Verfügbarkeit · **A7** Batch · **A10** Mistral-Degen · **A12** Phantom-Slot · **A4** STT-Pacing | Welle 1/2/3 (s.o.) |
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
3. **Cold-Start-Pipeline verfehlt 1 s:** beste Streaming-Kombi deepgram+groq+azure **1134 ms**, 0/27 < 1000 ms. Warm ~666 ms. *(Caveat: Median-Addition — A6 fixt das.)*

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

## Offene Entscheidungen (gestern abgebrochen)

- **A7:** Batch streichen *(Empfehlung)* vs. Deepgram-Tail bereinigen.
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

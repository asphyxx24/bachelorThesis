# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-06-08 (Session: Juni-Daten validiert + Analyse migriert + Figures geschärft + Repo aufgeräumt)

## TL;DR

Die **Juni-Kampagne (01.–07.06.2026)** ist die maßgebliche Datengrundlage (`data/`), unabhängig **validiert**, und die komplette Analyse läuft darauf. Alle drei Kernbefunde reproduzieren. Figures von 35 auf **19 starke** reduziert (Befund-Titel). Nächster Schritt: **Figure-Feinschliff + Prof-Aufbereitung**, dann Schreiben.

---

## Datenstand

- **Maßgeblich:** `data/` — Juni-Kampagne, 7 Tage × 8 Slots = 56 Slots, n=100/Provider/Slot, 0 % NaN.
- **Mai-Kampagne:** archiviert/gelöscht — nur noch in git-Historie (`e380b80` auf origin) abrufbar.
- **Validierung (2026-06-08, EC2 i-045):** Layer 1 reproduziert 8/9 Provider <1 ms, TLS-Versionen 7/7 exakt; Layer 2 PCAP-Struktur bestätigt; Layer 3 Spot-Check connect_ms reproduziert. → Daten unabhängig bestätigt.
- **Vantage-Point-Caveat:** Die Juni-L3-Kampagne lief auf einem **anderen AWS-Account** (nicht i-045), ebenfalls eu-central-1/Frankfurt. Nur Deepgram (Anycast) weicht ab. Siehe `data/processed/known_anomalies.md` Abschnitt 4.

## Drei Kernbefunde (Juni)

1. **Cross-Layer-Modell:** `connect_ms ≈ N_RTTs × ping + k` — slope 1.006, k 10.7 ms, **r=0.999** (4 direkte Provider). Bricht bei Cloudflare-fronted (4/9).
2. **Engine schlägt Netzwerknähe:** Deepgram (US) STT-TTFT 575 ms < Azure (EU) 1715 ms — Azure verliert durch 97 % Server-Processing. Bei TTS dreht es sich um (Azure gewinnt, TTFA 67 ms).
3. **Cold-Start-Pipeline verfehlt 1 s:** 0/27 Kombinationen < 1000 ms; beste Streaming-Kombi deepgram+groq+azure = 1134 ms. Warm-Schätzung ~666 ms (Future Work).

## Notebooks & Figures

- **8/8 Notebooks** (00–07) auf Juni gerechnet, lauffähig (`.venv` + `requirements.txt`).
- **19 Hauptteil-Figures** (Befund als Titel, n/CI). 16 gelöscht (Stabilitäts-Checks + redundante Violins).
- NB02 läuft lokal ohne tshark (scapy + layer1_extra + dnspython).
- Befunde: `notes/findings.md` · Gerüst: `notes/thesis_outline.md`.

## Offene Punkte

| Punkt | Status |
|-------|--------|
| Figure-Feinschliff (z.B. Cross-Layer CDN-Zoom-Inset) | offen, optional |
| `zusammenfassung_prof.pdf` (Prof-Übersichtsgrafik) | noch nicht überarbeitet |
| `findings.md`/`outline` für Prof aufbereiten | offen |
| Thesis-Text schreiben | bewusst ans Ende verschoben |

## Cleanup-Erinnerungen (extern, nur du)

- **AWS Access Key** (User `claude`, Account 365916940756) **löschen** — stand im Chat.
- **AWS Console-Passwort ändern.**
- **Andere-Account-Instanz** prüfen/stoppen (falls Juni-Mess-Instanz noch läuft → Kosten).

## AWS EC2 (Validierungs-Instanz)

| | Wert |
|-|------|
| Instance ID | `i-045a2d0eeb338b290` (thesis-measurement, eu-central-1b) |
| Status | **STOPPED** (nach Validierung 2026-06-08) |
| Zugang | AWS CLI (`.venv/bin/aws`) + SSH-Key `~/.ssh/thesis-ec2` (Public-Key liegt in authorized_keys) |
| Start | `.venv/bin/aws ec2 start-instances --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Provider-Matrix, Metrik-Definitionen |
| `HANDOFF.md` | **Diese Datei** |
| `data/processed/known_anomalies.md` | Juni-Anomalien + Vantage-Point-Caveat |
| `notes/findings.md` | 13 Befunde mit Juni-Zahlen |
| `notes/thesis_outline.md` | Kapitelgerüst |
| `notes/literature.md` | Literatursammlung |
| `measurements/` | Mess-Skripte (Methodik, Reproduzierbarkeit) |

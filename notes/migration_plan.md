# Migration & Methodik — Detailplan

> Erstellt: 2026-05-02. Basiert auf der Planungs-Session für den Neustart.

---

## Wissenschaftlicher Kern

**Messobjekt:** Cold-Start-Latenz kommerzieller Cloud-AI-APIs (STT, LLM, TTS)
von einem fixen Vantage Point (AWS EC2 eu-central-1/Frankfurt).

**Warum Cold-Start:**
Jeder neue Anruf startet mit 3 Cold-Connections: STT → LLM → TTS.
Bei 1000 Anrufen pro Tag passiert das 1000 Mal. Ab der zweiten Nachricht
innerhalb eines Gesprächs können Verbindungen warm gehalten werden —
aber das erste Mal ist immer kalt.

**Das Cross-Layer-Narrativ (alle 3 Layer zusammen):**

```
Layer 1 (Ping/DNS/TLS/Traceroute) → Wie weit ist der Provider? Welche Route?
       ↓ erklärt
Layer 2 (Paketaufzeichnung)       → Wie viele RTTs für welches Protokoll?
       ↓ validiert
Layer 3 (API-Latenz)              → Was spürt der Nutzer?
```

Kernbefund aus POC: Layer 1 Ping × 3 RTTs ≈ Layer 3 connect_ms

**Messgrößen:**
- `connect_ms`: socket.connect() bis Verbindung bereit (TCP+TLS+WS oder TCP+TLS)
- `ttft_ms` (STT/LLM): Anfrage bis erstes Antwort-Byte
- `ttfa_ms` (TTS): Anfrage bis erstes Audio-Byte
- `total_ms`: Vollständige Antwort empfangen

**Wissenschaftlicher Beitrag:**
Wie viel % des 1s-Latenzbudgets geht für Netzwerk-Infrastruktur drauf, und welche
Provider-Eigenschaften (Hosting-Region, Protokoll, AS-Pfad) erklären die Unterschiede?

---

## Provider-Matrix (FINAL, 2026-05-02)

| Kategorie | Provider 1 | Provider 2 | Provider 3 |
|-----------|-----------|-----------|-----------|
| **STT** | Deepgram Nova-3 (USA, Anycast, WebSocket) | AssemblyAI Universal-2 (USA, WebSocket) | Azure STT (Deutschland, WebSocket) |
| **LLM** | OpenAI gpt-4o-mini (USA, GPU, SSE) | Groq llama-3.1-8b-instant (USA, LPU, SSE) | Mistral mistral-small-3.2 (EU/FR, SSE) |
| **TTS** | Deepgram TTS Aura-2 (USA, Anycast, HTTPS) | OpenAI TTS tts-1 (USA, HTTPS) | Azure TTS Neural (Deutschland, HTTPS) |

Amazon Polly: Exkurs Intra-Cloud-Referenz (optional, nicht Hauptprovider).

---

## Kosten

**API-Kosten (14-Tage-Kampagne, n=100, 8×/Tag):**

| Provider | Kosten |
|----------|--------|
| Deepgram STT + TTS | $0 ($200 Startguthaben) |
| AssemblyAI STT | $0 ($50 Startguthaben) |
| Groq LLM | $0 (Free Tier) |
| Azure STT + TTS | ~$10,74 |
| OpenAI LLM + TTS | ~$9,24 |
| Mistral LLM | ~$0,31 |
| **API gesamt** | **~$20** |

**AWS-Infrastruktur:**

| Posten | Kosten/Monat |
|--------|-------------|
| EC2 t3.small | ~$14 |
| EBS 20 GB gp3 | ~$1,60 |
| **AWS gesamt (3 Monate)** | **~$47** |

**Budget: $100 → reicht.**

---

## AWS EC2 Setup

- Region: eu-central-1 (Frankfurt)
- Typ: t3.small (2 vCPU, 2 GB RAM)
- OS: Ubuntu 22.04 LTS
- Storage: 20 GB gp3
- Repo klonen von: `github.com/asphyxx24/bachelorThesis`

---

## Cron-Jobs (auf EC2)

```cron
# Layer 1: alle 6h background, täglich 05:30 full
0 */6 * * * cd ~/thesis && .venv/bin/python measurements/layer1/run.py --mode background
30 5 * * * cd ~/thesis && .venv/bin/python measurements/layer1/run.py --mode full

# Layer 3: alle 3h, alle 9 Provider, n=100
0 0,3,6,9,12,15,18,21 * * * cd ~/thesis && .venv/bin/python measurements/layer3/run.py --n 100 --api all

# Git-Sync: täglich 01:15 UTC
15 1 * * * cd ~/thesis && git add data/ && git commit -m "data: sync $(date +%Y-%m-%d_%H%M)" && git push
```

---

## Phasen-Reihenfolge (kein festes Datum, Deadline flexibel)

| Phase | Dauer (geschätzt) | Fokus |
|-------|-------------------|-------|
| Setup | ~1 Woche | EC2 aufsetzen, sample.wav aufnehmen, Keys beschaffen |
| Implementierung | ~1 Woche | Provider-Module schreiben, Cron einrichten |
| Kampagne | 14 Tage | Läuft automatisch, parallel Analyse beginnen |
| Analyse | ~2 Wochen | Alle Analyse-Notebooks, Ergebnisse auswerten |
| Schreiben | ~3–4 Wochen | Thesis-Kapitel, Review, Abgabe |

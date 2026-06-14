# Neuanfang — Referenz für den sauberen Wiederaufbau

> Angelegt: 2026-06-14 · Autor: Anton Rusik · Betreuer: Prof. Dr. Matthias Wählisch, TU Dresden
>
> Dieses Dokument ist die **einzige** Referenz für den Neuanfang. Alles Bisherige liegt in
> `archived/` (per Git wiederherstellbar) und wird **nicht** mehr als Grundlage genommen — nur als
> Nachschlagewerk. Wir bauen Skripte, Setup und **alle Messungen** von Grund auf neu auf.

---

## 1. Warum der Neuanfang (Prof-Feedback, Klartext)

Der Prof hat zwei Dinge gesagt:

1. **„Im Kern reicht das schon" / mindestens bestehen** — die Richtung stimmt.
2. **Aber er vertraut den Daten noch nicht**, weil **Methodik, Setup und Struktur nicht dargelegt** sind.
   Konkret bemängelt: kein nachvollziehbares Mess-Setup, keine erklärte Struktur, und
   **drei Anbieter mit sehr niedriger Layer-1-Latenz, die (noch) nicht erklärt sind.**

**Diagnose:** Das ist primär ein **Dokumentations- und Verständnis-Problem**, kein „die Zahlen sind
falsch"-Problem. Der Neuanfang ist trotzdem die Entscheidung — bewusst, **fürs eigene Verständnis**:
alles nochmal Schritt für Schritt selbst aufbauen, sodass jede Zahl auf eine dokumentierte,
reproduzierbare Prozedur zurückführbar ist.

**Leitprinzip diesmal:** *Erst Setup/Methodik schriftlich, dann Code, dann messen.* Nicht umgekehrt.

---

## 2. Was ERHALTEN bleibt (hart erarbeitetes Wissen, kein Datenmüll)

Diese drei Dinge sind unabhängig davon, wie die Zahlen erhoben wurden — sie werden mitgenommen:

### 2.1 Der Reframe — „Engine schlägt Geografie" (die Contribution)

- **Kernbefund (C1):** Aus EU-Sicht dominiert die **Backend-Engine** des Providers, **nicht** die
  Netzwerknähe. Schärfster Beleg: **STT/TTS-Inversion desselben Providers** (Azure verliert bei STT,
  gewinnt bei TTS).
- **C2 — Drei-Schichten-Methodik + Cloudflare-/Edge-Grenze** (bei einem Teil der Provider terminiert
  die Verbindung an einem Edge-Knoten, nicht am US-Server).
- **C3 (Methoden-Baustein, NICHT Headline):** Ping-basierte connect-Klassen-Heuristik. `r` bewusst
  **nicht** als Gütemaß verkaufen (n ist klein).

**Geschärfte Forschungsfrage (in beide Richtungen beantwortbar):**
> In welchem Maße erklären Netzwerk- und Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region)
> — *im Vergleich zur Backend-Verarbeitung der Engine* — die Latenzunterschiede zwischen kommerziellen
> Cloud-AI-APIs (STT, LLM, TTS) aus EU-Perspektive, und wie wirkt sich die Provider-Wahl auf die
> Gesamtlatenz einer sequenziellen Cold-Start-Voice-Pipeline aus?

„Netzwerk erklärt **weniger** als die Engine" ist eine gültige, sogar erwartete Antwort.

### 2.2 Die Mängelliste A1–A14 (Spezifikation für „besser machen")

Der alte Audit (`archived/PRUEFER_AUDIT_2026-06-08.md`) ist die **Checkliste dessen, was das neue
Setup besser können muss**. Die Punkte sind hier als Anforderungen umformuliert:

| # | Alter Mangel | Anforderung an den Neuaufbau |
|---|---|---|
| A1 | r=0.999 (n=4) überverkauft, Headline widerlegt | `r` nie als Gütemaß; mit Residualfehler argumentieren, nicht mit Korrelation |
| A2 | 0 % Fließtext, Limitations verschweigen die härtesten Löcher | Methodik-Kapitel + ehrliche Limitations von Anfang an mitschreiben |
| A3 | `connect_ms` ist kategorienübergreifend NICHT dieselbe Messgröße | Metrik-Definitionen **vor** dem Messen festschreiben; ttft/ttfa-Asymmetrie dokumentieren |
| A4 | STT misst Full-Utterance-Batch, keine First-Token-Streaming-Latenz | Mess-Semantik je Kategorie explizit deklarieren (Audio-Dump vs. Real-Time-Pacing) |
| A5 | 1-s-Budget willkürlich, widerspricht eigener Literatur | Schwellen aus Literatur herleiten/belegen |
| A6 | E2E = reine Median-Addition, kein echter Run, kein CI | Monte-Carlo / echte Runs + Konfidenzintervalle |
| A7 | STT `total_ms` cross-Provider unbrauchbar (Tail-Artefakt) | Nur saubere, vergleichbare Metriken; Batch-Szenario raus |
| A8 | Verfügbarkeit ignoriert (beste Pipeline = Groq mit ~33 % Ausfall) | Verfügbarkeit/Joint-Completion als eigene Dimension messen |
| A9 | Layer-2 als „unabhängige Validierung" brüchig | Layer-2 sauber als Struktur-Beleg einordnen, nicht überverkaufen |
| A10 | LLM-Output-Degeneration ungeprüft (Mistral: ~72 quasi-leere „Erfolge") | `token_count` roh speichern; Erfolg an Mindest-Output-Länge knüpfen |
| A11 | `token_count` zählt SSE-Chunks, nicht Tokens | Als „Chunk-Rate" benennen ODER gegen API-usage kalibrieren |
| A12 | Timestamp-Spillover → Phantom-57.-Slot | Nach Slot-`tag` gruppieren, nicht nach Timestamp-Stunde |
| A13 | TTS-E2E endet bei ttfa, ignoriert Playback | E2E-Endpunkt begründen; Sensitivität mit `tts_total` |
| A14 | Keine STT-Inhaltskorrektheit/WER | **Raw-Transkript-Strings speichern** (nicht nur Längen!), WER gegen Referenz |

> **Wichtigste Lehre für die neuen Skripte:** Roh-Daten **vollständig** speichern (Transkript-Texte,
> `token_count`, alle Timestamps), damit spätere Fragen (WER, Degeneration, Spillover) ohne
> Neumessung beantwortbar sind. Der alte Lauf hat Information weggeworfen → A14 war „nicht machbar".

### 2.3 Provider-Matrix (als Auswahl mit Rationale — anpassbar)

| Kategorie | Provider | Modell | Region | Protokoll |
|-----------|----------|--------|--------|-----------|
| STT | Deepgram | Nova-3 | USA (Anycast) | WebSocket |
| STT | Rev.ai | English | USA | WebSocket |
| STT | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA (GPU) | HTTPS+SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS+SSE |
| LLM | Mistral | mistral-small-2603 | EU/Frankreich | HTTPS+SSE |
| TTS | Deepgram | Aura-2 | USA (Anycast) | HTTPS Streaming |
| TTS | OpenAI | tts-1 | USA | HTTPS Streaming |
| TTS | Azure | Standard Neural | Italien (Italy North) | HTTPS Streaming |

- AssemblyAI → durch Rev.ai ersetzt (Rev.ai akzeptiert Audio-Dump wie Deepgram/Azure).
- Amazon Polly: optionaler Intra-Cloud-Exkurs.
- **Offen für den Neuanfang:** Provider-Auswahl darf neu bewertet werden (z. B. mehr EU-Provider,
  um die Anycast/Edge-Verzerrung sichtbarer zu machen).

---

## 3. Das ungelöste Rätsel, das VOR dem Neumessen verstanden werden muss

**Drei Anbieter mit sehr niedriger Layer-1-Latenz aus Frankfurt** — der Prof-Einwand.

- **Hypothese:** **Anycast / CDN-Edge** (z. B. Cloudflare) terminiert die Verbindung an einem Knoten
  *in/nahe Frankfurt*. Gemessen wird dann der Edge, **nicht** der eigentliche US-Server.
- **Das ist kein Messfehler, den Neumessen behebt** — dieselbe Zahl käme wieder. Es muss **erklärt**
  werden, pro Endpunkt: *Wo terminiert die Verbindung physisch, und woher weiß ich das?*
- **Beleg-Werkzeuge:** `traceroute`, ASN-/Whois-Lookup, TLS-SNI/Zertifikat, Reverse-DNS, ggf.
  RIPE Atlas. → Diese Endpunkt-Auflösung wird **fester Bestandteil** des neuen Layer-1-Setups.

---

## 4. Drei-Schichten-Architektur (bleibt als Rahmen)

- **Layer 1 (Infrastruktur):** DNS, Ping, TLS, Traceroute — **plus** Endpunkt-Auflösung (s. §3).
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP, je Provider.
- **Layer 3 (API-Latenz):** Cold-Start `connect_ms` / `ttft_ms` / `total_ms`.

**Messdesign-Grundsätze (überdenkbar, aber Ausgangspunkt):**
- **Cold-Start:** jede Messung neue TCP+TLS-Verbindung (kein Connection Pooling).
- **Raw-Protokoll:** STT ohne SDK, direkte WebSocket-Verbindung.
- **Feste Inputs je Kategorie** (für fairen Vergleich):
  - STT: `sample.wav` — „Good morning. I would like to know the current weather forecast for Frankfurt." (~5 s)
  - LLM: „Reply in one short sentence: What is the capital of Germany?"
  - TTS: „Good morning! How can I assist you today?"
- **Vantage Point:** AWS EC2 eu-central-1 (Frankfurt) — diesmal **dokumentiert** (Account, Instanz,
  Region, Uhrzeit, Zeitzone) und konsistent.

---

## 5. Reihenfolge des Wiederaufbaus (Methodik-first)

1. **Layer-1-Rätsel erklären** (Anycast/Edge je Provider belegen) — entscheidet über Glaubwürdigkeit.
2. **Messprotokoll-Dokument schreiben** — Setup, Vantage Point, Metrik-Definitionen, was/warum/wie oft,
   Fehlerbehandlung. *Das ist das Dokument, das der Prof eigentlich verlangt.*
3. **Skripte neu** — selbst-dokumentierend: loggen Setup, Endpunkt-Auflösung, Versionen; speichern
   **alle** Rohdaten (Transkript-Texte, token_count, Timestamps).
4. **Pilot-Messung** (1 Slot, alle Provider) → gegen das Protokoll validieren.
5. **Volle Kampagne.**
6. **Analyse** auf den neuen Daten — Framing („Engine schlägt Geografie") steht bereits.

---

## 6. Status & nächster Schritt

- **2026-06-14:** Neuanfang entschieden, Altes nach `archived/`. **`setup/`-Methodik-Docs geschrieben**
  (anbieter_auswahl, api_endpunkte, messprotokoll, mess_kommandos) inkl. aller Design-Entscheidungen
  (TCP-Ping primär, connect-Submetriken, 7×8-UTC-Slots×n=100 **interleaved**, Layer-2 N≈30).
- **ultracode-Audit gelaufen** → **`setup/AUDIT_ultracode_2026-06-14.md`** (59 Agenten, 41 bestätigte
  Findings). Urteil: **Go fürs Skript-Bauen, 0 kritische Defekte.**
- **⭐ HIER WEITERMACHEN:** Punch-Liste aus dem Audit abarbeiten, Reihenfolge:
  1. **Doku-Fixes (billig):** Deepgram = DNS-Round-Robin statt „Anycast"; rev.ai-IP-Fehlzuordnung
     (`api_endpunkte.md`); `connect_ms`-Rest in `messprotokoll.md:47`; Mistral = Cloudflare-fronted.
  2. **Doku-Ergänzungen:** Edge-Klassifikator (A3), Modell-Pinning (A2), Abschnitt „Aggregation &
     Inferenz"/CI (A4), Erfolgs-/Timeout-Kriterien (A7), Instanz-/Per-Run-Capture (A5/A6, non-burstable!).
  3. **Dann Skripte bauen** — Audit-Liste als Spezifikation; alte `archived/`-Skripte NICHT kopieren.

## 7. Externe Aufräum-Erinnerungen (aus altem HANDOFF, weiterhin offen)

- AWS Access Key (User `claude`, Account 365916940756) **löschen**.
- AWS Console-Passwort ändern.
- Andere-Account-Mess-Instanz prüfen/stoppen (Kosten).
- Validierungs-Instanz `i-045a2d0eeb338b290` (eu-central-1b) — Status zuletzt **STOPPED**.

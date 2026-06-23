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

### 2.1 Der Reframe — „Backend statt Geografie" (die Contribution)

- **Kernbefund (C1) — „Backend statt Geografie":** Aus EU-Sicht dominiert die **Backend-Verarbeitung (HW+Modell)**, **nicht** die
  Netzwerknähe. Die wasserdichte Aussage ist die **negative**: „Netznähe erklärt die Spreizung nicht." („Engine/Backend" bleibt wegen des Modellgrößen-Confounds bewusst aus dem Arbeitstitel.) **Schärfster Beleg — LLM bei identischer Edge-RTT:** OpenAI/Groq/Mistral terminieren alle bei Cloudflare Frankfurt (AS13335, ~1 ms RTT — über 2 CF-IPs je Provider ~50/50, beide AS13335, für 100 % des LLM-Traffics gemessen+ASN-belegt, s. `data/audit_20260618/{l1_rtt_per_ip.md, asn_per_ip.md}`), aber LLM-`ttft` streut über die Voll-Kampagne (56 von 56 Slots, A4) **~67 → 279 → 487 ms (~7,3×; gepoolt 8,3×; groq<mistral<openai)** → gleiches Netz, Differenz nicht EU-Edge-Nähe (per-IP invariant; EU-Mistral langsamer als US-Groq). Zweiter Beleg: Azure **schnellstes TTS** (`ttfa` ~94 ms) — „trotz US-Konkurrenz" gilt nur gegenüber Deepgram; OpenAI-TTS terminiert AUCH bei Cloudflare-FRA (zweite identical-edge → stärkt C1). STT ehrlich: auf `ttfp` ist Azure **nicht** langsamster — die alte „Azure-STT-Endpointing-Inversion" war ein Dump-Artefakt (Bulk-Compute), kein Engine-Beleg. S. `setup/messprotokoll.md` → „STT-Primärmetrik".

> **Hinweis zu den Headline-Zahlen (Audit 2026-06-18, H1):** Die früher genannten **75/268/476 ms (~6,4×)** sind der Predeploy-Pilot (n=200, 2 Slots) und reproduzieren aus keinem Kampagnen-Datensatz. Maßgeblich ist die Voll-Kampagne (56 von 56 Slots, A4): **groq 66,9 / mistral 278,9 / openai 486,6 ms; openai/groq = ~7,3× (gepoolt 8,3×)** (Bootstrap-CI noch ausstehend). C1 inhaltlich unberührt (Ordnung invariant; der finale Faktor ~7,3× ist sogar GRÖSSER als der Pilot → der Kernbefund wird dadurch STÄRKER).
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
| STT | Deepgram | Nova-3 | USA (Multi-DC, DNS-Round-Robin) | WebSocket |
| STT | Rev.ai | English | USA | WebSocket |
| STT | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA (GPU) | HTTPS+SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS+SSE |
| LLM | Mistral | mistral-small-2603 | EU/Frankreich | HTTPS+SSE |
| TTS | Deepgram | Aura-2 | USA (Multi-DC, DNS-Round-Robin) | HTTPS Streaming |
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
- **Layer 3 (API-Latenz):** Cold-Start — atomare connect-Submetriken / Erste-Ausgabe-Metrik / `total_ms`.
  Erste-Ausgabe: STT **`ttfp`** (primär, paced) bzw. `ttft`/`ttfa` (LLM/TTS). S. `setup/messprotokoll.md`.

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
6. **Analyse** auf den neuen Daten — Framing („Backend statt Geografie") steht bereits.

---

## 6. Status & nächster Schritt

- **2026-06-14:** Neuanfang entschieden, Altes nach `archived/`. **`setup/`-Methodik-Docs geschrieben**
  (anbieter_auswahl, api_endpunkte, messprotokoll, mess_kommandos) inkl. aller Design-Entscheidungen
  (TCP-Ping primär, connect-Submetriken, 7×8-UTC-Slots×n=100 **interleaved**, Layer-2 N≈30).
- **ultracode-Audit gelaufen** → **`setup/AUDIT_ultracode_2026-06-14.md`** (59 Agenten, 41 bestätigte
  Findings). Urteil: **Go fürs Skript-Bauen, 0 kritische Defekte.**
- **2026-06-15:** ✅ **A9 (billige Doku-Fixes) erledigt** — Deepgram „Anycast" → „Multi-DC, DNS-Round-Robin"
  (CLAUDE.md, NEUANFANG.md, anbieter_auswahl.md); rev.ai-/Deepgram-IP-Fehlzuordnung korrigiert
  (`api_endpunkte.md`); `connect_ms` → `connect_total_ms` (`messprotokoll.md`); `-W`-Plattformnotiz
  (`mess_kommandos.md`); rev.ai-TLS-1.2-Fußnote (`api_endpunkte.md`). Mistral=Cloudflare steht in der
  Host-Tabelle.
- **2026-06-15:** ✅ **A1 + A2 erledigt** — A1: TLS-Probe-Footgun (macOS/LibreSSL) abgesichert
  (`tls_version` nur auf EC2/OpenSSL, `ssock.version()`-Guard, `OPENSSL_VERSION`-Logging,
  `openssl s_client`-Cross-Check) in `mess_kommandos.md` + `messprotokoll.md`. A2: Modell-Pinning-Tabelle
  in `api_endpunkte.md` (OpenAI→`gpt-4o-mini-2024-07-18`, Rest als Limitation) + `effective_model`-Logging
  in `messprotokoll.md`.
- **2026-06-15:** ✅ **A3–A8 erledigt → komplette Audit-Punch-Liste (A1–A9) abgearbeitet.**
  - **A3** Edge/Host-Terminierungs-Klassifikator (Konjunktion a∧b∧c) in `messprotokoll.md` + feste
    Terminierungs-Tabelle in `api_endpunkte.md` (vorläufig: 4× Host, 3× Edge, auf EC2 zu bestätigen).
  - **A4** §Aggregation & Inferenz: Headline = **Median der Slot-Mediane** (gepoolt = Sensitivität),
    Perzentil-Ehrlichkeit (p99 nur gepoolt/Limitation), Bootstrap-95%-CI, Differenz-Bootstrap/Mann-Whitney;
    + E2E via Monte-Carlo-Faltung & Pareto-Front (Latenz↔Zuverlässigkeit).
  - **A5** Per-Run: `resolved_ip`, `http_version`, `run_meta`-Record je Slot, Lockfile-Pflicht.
  - **A6** Instanz `c6i.large` (non-burstable) + CPU-Steal-Logging.
  - **A7** Erfolgs-/Timeout-Tabelle (Connect 10 s / Response einheitl. 30 s, Mindest-Output, Fehler-Enum).
  - **A8** Erste-Ausgabe als Primärmetrik (mengen-robust): STT **`ttfp`** (paced, endpointing-frei),
    LLM/TTS `ttft`/`ttfa`; `total`/`ttl` sekundär; OpenAI-TTS auf mp3 gepinnt. (STT-`ttfp`-Verfeinerung
    2026-06-16, s. `setup/AUDIT_stt_methodik_2026-06-16.md`.)
- **2026-06-15:** ✅ **Layer-1-Skripte gebaut + ultracode-reviewt** (in `measurements/layer1/`):
  `tcp_ping.py` (primäre RTT), `icmp_ping.py` (ICMP-Cross-Check), `dns_lookup.py` (Multi-Resolver+TTL),
  `asn_lookup.py` (ASN/Netz je IP, Bedingung b), `tls_info.py` (TLS+Timing, A1-Guard),
  `traceroute_asn.py` (AS-Pfad, Bedingung c) + zentrale `hosts.py`. Alle laufen auf dem Mac, Rohdaten →
  `data/layer1/*.jsonl`. Einzelreviews (101 Agenten): bestätigte Fixes angewandt — v.a. `FileNotFoundError`
  überall gefangen (dig/traceroute fehlen auf frischem Ubuntu!), ICMP/Traceroute auf aufgelöste IP
  (Cross-Check-Konsistenz), stderr/returncode-Auswertung, ASN-MOAS-Robustheit. **Offen/zu besprechen:**
  TCP-SYN-Traceroute `-T -p 443` (braucht sudo) und cwd-fester Output-Pfad.
- **2026-06-15:** ✅ **Layer-3 gebaut + ultracode-reviewt + DEPLOYED — Kampagne läuft.**
  `measurements/layer3/`: `config.py`, `connect.py`, `llm.py`, `tts.py`, `stt.py`, `run.py` (+ `sample.wav`).
  Alle 9 Endpunkte live mit echten Keys verifiziert; je Skript einzeln ultracode-reviewt (LLM 37, TTS+STT 65,
  run.py 24 Agenten), bestätigte Fixes eingebaut. Auf **EC2 c6i.large** (eu-central-1, OpenSSL 3.0.13)
  deployed, **cron** 8 UTC-Slots × n=100, erster Slot **2026-06-15 21:00 UTC**. Pilot bestätigt die These
  live (FRA-RTTs ~1 ms Cloudflare / ~11 ms Azure / ~138 ms US, STT/TTS-Inversion, A1/A6). Doku:
  **`setup/deployment.md`** + Layer-3-Tabelle in `mess_kommandos.md`. Erinnerung: [[l3-campaign-deployed]].
- **2026-06-16:** ✅ **Methodik 3× ultracode-auditiert (23 → 62 → 85 Befunde) + alle Fixes umgesetzt; Code `f9e6dc8`.**
  - **STT auf `ttfp` + 1×-Realtime-Pacing** (paralleler Empfang via `asyncio.gather`); `ttft`=Stream-Ende-Final sekundär. **LLM F2** (`output_tokens`) **+ F3** (Erfolg inhaltlich). IPv4 bei STT gepinnt.
  - **C1 datengestützt neu verankert:** Kernbeleg = **LLM @ identischer Edge-RTT** (~1 ms Cloudflare, per-IP invariant, Geografie invertiert); 2. Beleg Azure-schnellstes-TTS; STT ehrlich (kein Engine-Beleg). Die alte „Azure-STT-Endpointing/1722 ms"-These war Dump-Bulk-Compute → **falsch, gestrichen**. (Die hier ursprünglich genannten 75/268/476 ms ≈ 6,4× wurden am 2026-06-18 als Predeploy-Pilot erkannt → s. Eintrag 2026-06-18; maßgeblich sind 67/279/487 ms ≈ 7,3× (gepoolt 8,3×).)
  - **LAYER 2 ECHT gebaut + geeicht** (`measurements/layer2/`): App-`tcp_handshake` = Wire-SYN→SYN-ACK auf **±0,1 ms** (Azure 11 ms / Deepgram 139 ms, je N=30) → Layer-3 paket-validiert (C2). Beantwortet Wählischs Datenvertrauen mit Daten.
  - **Deepgram-ASN korrigiert** (6 IPs/2 ASNs/2 RTT-Klassen). Voll-Urteil: `data/audit_20260616/VERDICT.md`.
- **⭐ HIER WEITERMACHEN: siehe `HANDOFF.md`** — Campaign-Check, **Arbeitstitel wählen** (Kandidaten fertig in
  `notes/arbeitstitel.md`), Datenaufbereitung, **Statistik gemeinsam gegenprüfen** (nächste ungeprüfte Fehlerfläche),
  erste Interpretation, LaTeX-Prof-Folien. Vollkampagne, abgeschlossen (56/56) — Instanz stoppen.
- **2026-06-17:** ✅ **Daten-Audit Tag 1** (50 Agenten, 6 Slots/5.400 Calls, Zahlen aus Rohdaten nachgerechnet):
  Datensatz **vertrauenswürdig**, 0 Wertfehler, C1 diurnal stabil, Anomalien providerseitig (Mistral-503 @03h,
  OpenAI-TTS ~30s-Hang). Nichts neu zu messen — nur Auswertungs-Disziplin (s. `data/audit_20260617/VERDICT.md`
  + Disziplin-Block in `HANDOFF.md` §4).
- **2026-06-18:** ✅ **Ultracode-Voll-Audit (72 Agenten, 85 Befunde) — Urteil GO-mit-Auflagen.** Methodik im Kern valide, C1 über alle Slots invariant, Auflagen durchweg **Doku-/Reporting-Korrekturen, keine Neumessungen.** Voll-Urteil `data/audit_20260618/VERDICT.md`. Wichtigste:
  - **H1 (in Docs gefixt):** Headline-LLM-`ttft` **75/268/476 ms** = Predeploy-Pilot, reproduziert aus keinem Kampagnen-Datensatz; Voll-Kampagne (56 von 56 Slots, A4) = **~67/279/487 ms, ~7,3× (gepoolt 8,3×)** (groq<mistral<openai). C1 unberührt. → in §2.1 korrigiert.
  - **H2:** Layer-2-Eichung validiert nur den **Connect-Timer**, nicht `ttft`/`ttfa`. **H3:** Fehler-Enum (F4) existiert nicht in Code/Daten; Filter `error=='timeout'` verfehlt 158/161 Timeouts. **H4:** `data/layer1/` im Repo = macOS-Dev-Lauf (~17-21 ms), nicht EC2 (~1 ms); nur EC2-L1 nutzen.
  - **M1:** sequenzielle E2E braucht `connect + stt_ttft` (ttfp unterschätzt STT um ~3,7 s). **M2:** OpenAI-TTS = 2. identical-edge (CF-FRA) → stärkt C1. **Fehlend:** `ttl_ms` existiert nicht → gestrichen.
- **2026-06-19:** ✅ **L1-RTT- + ASN-Lücken aus vorhandenen Daten GESCHLOSSEN (kein Neumessen).** Über `connect.resolved_ip` der 16 Slots ist 100 % des Traffics RTT-gedeckt + ASN-belegt (`data/audit_20260618/{l1_rtt_per_ip.md,asn_per_ip.md}`): alle LLM-Hosts + OpenAI-TTS = AS13335 Cloudflare @ ~1 ms; Deepgram Multi-DC Zayo AS6461 ×3 + Cogent AS174 ×3 (Slow-Mode-DC ~101 ms = Backend); rev.ai 3× AWS AS16509 ~140 ms; Azure AS8075 ~11 ms. Eingearbeitet in `api_endpunkte.md` + `messprotokoll.md`. Doku-Voll-Durchgang (alle Docs aktualisiert, `/prime` erweitert). Kampagne: EC2 `i-0f8f6d2414cecebb8`, 16+ Slots, Code `f9e6dc8`, **Stop ~23.6.**; nur Layer 3 slotweise, Layer 1 = einmalige Momentaufnahme (16.6.). C1 umbenannt „Backend statt Geografie". Arbeitstitel: 3 Kandidaten (Favorit s. `notes/arbeitstitel.md`), finale Wahl offen. Zweitprüfer-Anfrage Prof. Färber raus, Antwort offen.

## 7. Externe Aufräum-Erinnerungen (aus altem HANDOFF, weiterhin offen)

- AWS Access Key (User `claude`, Account 365916940756) **löschen**.
- AWS Console-Passwort ändern.
- Andere-Account-Mess-Instanz prüfen/stoppen (Kosten).
- Validierungs-Instanz `i-045a2d0eeb338b290` (eu-central-1b) — Status zuletzt **STOPPED**.

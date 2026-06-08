# Bekannte Anomalien & Caveats — Juni-Kampagne 2026

> Erstellt: 2026-06-08, für die maßgebliche Messkampagne **01.–07.06.2026**.
> Ersetzt die alte Mai-Doku (jetzt unter `data_archive_2026-05/processed/known_anomalies.md`).
> Alle Zahlen aus den Per-Run-Records in `data/layer3/` (nicht aus den Slot-Summary-Zeilen).

---

## 0. Kampagnen-Eckdaten

- **Zeitraum:** 01.06.–07.06.2026 = genau **1 Woche** (alle Wochentage + Wochenende).
- **Slots:** 56 = 7 Tage × 8 Zeitschlitze (alle 3 h), **lückenlos** (keine partiellen Tage).
- **n:** 100 Runs/Provider/Slot (Soll). Cold-Start (neue TCP+TLS-Verbindung je Run).
- **Datenqualität:** 0 NaN in `data/processed/layer3_{stt,llm,tts}.parquet`
  (16.227 STT / 14.729 LLM / 16.796 TTS gültige Per-Run-Zeilen).
- **Validiert am 2026-06-08** (Layer 1/2/3, siehe Abschnitt 4).

---

## 1. Provider-Fehlerraten (Juni, aus Per-Run-Records)

| Metrik | Provider | Errors / Total | Rate | Bewertung |
|--------|----------|---------------:|-----:|-----------|
| llm | **groq** | 1845 / 5600 | **32,9 %** | Rate-Limit (Free Tier), KEIN Datenproblem — s. 1.1 |
| llm | mistral | 224 / 5600 | 4,0 % | Capacity-Wellen (HTTP 429), s. 1.2 |
| llm | openai | 2 / 5600 | 0,0 % | vernachlässigbar |
| stt | **revai** | 571 / 5600 | **10,2 %** | Provider-Flakiness, s. 1.3 |
| stt | deepgram | 2 / 5600 | 0,0 % | vernachlässigbar |
| stt | azure_stt | 0 / 5600 | 0,0 % | — |
| tts | azure_tts | 2 / 5600 | 0,0 % | vernachlässigbar |
| tts | deepgram_tts | 1 / 5600 | 0,0 % | vernachlässigbar |
| tts | openai_tts | 1 / 5600 | 0,0 % | vernachlässigbar |

### 1.1 Groq LLM: 32,9 % Errors = Rate-Limit (erwartet)
Groq Free Tier hat ein RPM-Limit. Pro Slot kommen **konstant 67 erfolgreiche Runs**
durch (min 67, median 67, max 70 über alle 56 Slots), danach HTTP 429. Das Muster ist
gleichmäßig (kein systematischer Tagesausfall) → **Provider-Limit, kein Datenqualitäts-Problem.**
3.755 erfolgreiche Samples bleiben statistisch reichlich. (Mai: 34,97 % — konsistent.)

### 1.2 Mistral LLM: 3 Stress-Slots
Slots mit deutlich reduzierten Erfolgen (HTTP-429-Wellen, echte Provider-Capacity):

| Datum (UTC) | Slot | Erfolge (von 100) |
|-------------|------|------------------:|
| 2026-06-01 | 06h | 50 |
| 2026-06-04 | 15h | **15** |
| 2026-06-07 | 21h | 50 |

**Interpretation:** Echte Capacity-Wellen des EU-Providers, kein Mess-Bug. In zeitlichen
Stabilitäts-Plots einbeziehen, in deskriptiver Statistik auf Quantil-Verzerrung prüfen.

### 1.3 Rev.ai STT: 10,2 % Errors + 5 fehlende Summary-Zeilen
- **571/5600 Connection-Failures** (Server antwortet nicht; Client setzt `error=""`).
  Entspricht der Mai-Rate (10,16 %) → stabile Provider-Eigenschaft, kein neuer Effekt.
- **5 Slots ohne eingebettete Summary-Zeile**: `2026-06-01 03h`, `2026-06-02 09h`,
  `2026-06-02 12h`, `2026-06-04 03h`, `2026-06-04 21h`. Die 100 Einzel-Runs sind in diesen
  Slots **vollständig vorhanden** — nur die Aggregat-Zeile fehlt. Analyse rechnet aus
  Rohdaten → **kein Datenverlust.**

---

## 2. Aufbereitungs-Caveat: `processed/layer1_tls.csv` ist leer

- Alle 63 Zeilen in `data/processed/layer1_tls.csv` haben `handshake_ms=` und
  `tls_version=` **leer** (vorbestehender Bug in `process_raw_data.py`, war auch in
  der Mai-Aufbereitung so).
- **Die echten TLS-Daten liegen in `data/layer1_extra/tls.csv`** — vollständig befüllt,
  mit getrenntem `tcp_connect_ms` und `tls_handshake_ms`, `tls_version`, `cipher`, `alpn`.
- **Konsequenz:** Für TLS-Analysen `layer1_extra/tls.csv` nutzen, NICHT `processed/layer1_tls.csv`.
  (Fix in `process_raw_data.py` optional — die Quelle ist sauber.)

---

## 3. Layer-1: TCP/TLS jetzt getrennt & ganze Kampagne (Verbesserung ggü. Mai)

- `data/layer1_extra/` misst TCP-Handshake (`tcp_connect_ms`) und TLS-Handshake
  (`tls_handshake_ms`) **getrennt** und **über alle 7 Tage** (70 TCP- / 35 TLS-Samples
  pro Endpoint) — statt des Mai-Einmal-Snapshots (10 bzw. 5 Samples am 24.05.).
- **TLS-Versionen (7/7 bestätigt):** Rev.ai = **TLS 1.2** (ECDHE-RSA-AES128-GCM-SHA256),
  alle anderen TLS 1.3 (TLS_AES_256_GCM_SHA384). Rev.ais TLS-1.2-Handshake ≈ 2 RTT
  (~287 ms) gegen 1 RTT bei TLS 1.3 → +1-RTT-Penalty.
- **DNSSEC:** 0/6 Zonen signiert (7 Endpoints, microsoft.com doppelt; `data/layer1_extra/dnssec.csv`) — unverändert ggü. Mai.

---

## 4. Vantage-Point- & Validierungs-Caveat (WICHTIG für Methodik)

- **Die Juni-Layer-3-Kampagne wurde auf einer EC2-Instanz in einem ANDEREN AWS-Account
  gemessen** (nicht `i-045a2d0eeb338b290`). Beide eu-central-1/Frankfurt.
- **Validierung am 2026-06-08** von `i-045` (selbe Region) reproduziert **8/9 Provider
  auf <1 ms** und **alle 7 TLS-Versionen exakt**. Layer-3-`connect_ms` reproduziert bei
  allen Providern. → **Daten unabhängig bestätigt.**
- **Einzige Abweichung: Deepgram** (Anycast, AS 12129) — RTT/connect hängen vom
  konkreten Netz/AS ab (Kampagne ~134 ms, i-045 102–148 ms). **Kein Fehler**, sondern
  eine *dokumentierbare Eigenschaft* von Deepgrams Anycast-Routing.

---

## 5. Layer 2 (PCAP) — neu aufgenommen 2026-06-08

- Frische Captures aller 9 Provider in `data/layer2/` (ersetzen die Mai-Captures).
- Aufgenommen von `i-045` (eu-central-1b) — Provenance s. `data/layer2/PROVENANCE.md`.
- **Struktur bestätigt** (vantage-unabhängig): Cloudflare-Fronting (groq/mistral/openai
  terminieren bei ~1 ms Edge-RTT), TLS-Handshake = 1 RTT (TLS 1.3), TCP-RTT = SYN→SYN-ACK.
- **Rev.ai-Capture:** Call-Error (bekannte Flakiness) → Handshake erfasst, App-Daten fehlen.
- Deepgram-Absolutzeiten Anycast-behaftet (s. Abschnitt 4).

---

## 6. Befunde, die aus der Analyse re-derived werden (NICHT hier dokumentiert)

Die eigentlichen Ergebnisse (TTFT-Reihenfolge, Cross-Layer-Modell r≈0.999, E2E-Budget,
Engine-vs-Netzwerk) werden in den Notebooks 03–07 **aus den Juni-Daten neu berechnet**.
Diese Datei dokumentiert nur Daten-Caveats, keine Analyse-Resultate.

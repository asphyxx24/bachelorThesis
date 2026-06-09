# Belege zu den drei Prüfer-Fragen

Für jede der drei Fragen aus `00_GESAMT.md`: die Antwort in einem Satz und **wo der Beleg liegt**
(Datei, Zeile, Tabellen-Spalte, PCAP-Feld), damit du die Aussage im Gespräch substantiieren kannst.

---

## Frage 1 — „Zählen Sie den Connect doppelt, wenn Sie die E2E-Latenz addieren?"

**Antwort:** Nein — Metrik-Asymmetrie. STT-`ttft` ist connect-**exklusiv** (ab erstem Audio-Chunk,
also nach dem Connect), LLM/TTS-`ttft`/`ttfa` ist connect-**inklusiv**. Die Summe
`stt_connect + stt_ttft + llm_ttft + tts_ttfa` zählt den Connect genau einmal.

**Beleg — der Messcode (die zwei Definitionen nebeneinander):**

| | Datei | Zeile | Inhalt |
|---|---|---|---|
| STT, connect-exklusiv | `measurements/layer3/stt_deepgram.py` | 55 | `connect_ms = (t_ws_connected − t_ws_start)` |
| | | 62 | `t_first_chunk` wird **nach** `t_ws_connected` (Z. 54) gesetzt |
| | | 99 | `ttft_ms = (t_first_final − t_first_chunk)` → startet nach dem Connect |
| LLM, connect-inklusiv | `measurements/layer3/llm_groq.py` | 40 | `connect_ms = _measure_connect(...)` → **separate** Wegwerf-Messung |
| | | 43 | `t_req` (Request-Absenden über eine frische Verbindung) |
| | | 92 | `ttft_ms = (t_first_content − t_req)` → enthält den Verbindungsaufbau |

(Analog: `stt_azure.py` / `stt_revai.py` bzw. `llm_mistral.py` / `llm_openai.py`.)

**Beleg — die Summe selbst:** `analysis/tables/07_pipeline_combinations.csv`, Zeile
`deepgram+groq+azure`: `stt_conn_ms` 424,9 + `stt_ttft_ms` 574,6 + `llm_ttft_ms` 68,2 +
`tts_ttfa_ms` 66,6 = `stream_e2e` **1134,2**. Code: `analysis/07_e2e_pipeline.ipynb`, Zelle
„27 Kombinationen aufbauen".

**Beleg — die Definition:** `CLAUDE.md`, Abschnitt „Weitere Layer-3-Metriken" + der Hinweis-Block
„Wichtig — `ttft`/`ttfa` ist NICHT einheitlich ‚connect + Verarbeitung'".

---

## Frage 2 — „Azures ,Server'-Block ist 414 ms — ist das Backend langsam?"

**Antwort:** Nicht in `connect_ms`. Die 414 ms sind überwiegend eine **client-seitige Sendelücke**
(App bei `connect_ms` ~49 ms sendebereit, sendet Audio aber erst bei ~446 ms) — kein Server-Processing.
`app_data_start` (446 ms) ≠ `connect_ms` (49 ms). Azures echte Verarbeitung (~776 ms) ist getrennt sichtbar.

**Beleg — die Pakete direkt (am stärksten):**
- **Roh-PCAP in Wireshark:** `data/layer2/capture_azure_stt_20260608_1627.pcap`. Sichtbar: nach dem
  ACK bei **86,8 ms** kommt **kein Paket** bis **445 ms** — die leere Lücke ist der Beleg.
- **Aufbereitet:** `data/layer2/analysis_summary.json`, Eintrag `azure_stt`, Feld **`timeline`**
  (Paketliste mit ms-Zeitstempeln: SYN 0 · SYN-ACK 18,46 · ServerHello ~32 · ACK 86,81 · dann
  erstes Paket erst 445,07 · Audio-Burst).

**Beleg — die Zahlen:**
- `analysis/tables/02_pcap_communication_profile.csv`, Zeile `azure_stt`: `tcp_hs_ms` 18,46 ·
  `tls_hs_ms` 12,72 · `proto_setup_ms` 414,03 · `app_data_start_ms` 445,99.
- `analysis/tables/03_stt_statistics.csv`, Zeile `azure,connect_ms`: p50 = **49,5 ms**
  (≠ app_data_start 446 → die Differenz ist die Lücke).
- Server-Processing ~776 ms: zweiter Ausreißer im Inter-Arrival-Stem von
  `02_packet_timeline_azure_stt.png`; berechnet in `analysis/figures/02_pcap/build_packet_timeline.py`
  (`_milestones` → `g_srv`).

**Beleg — der Kontrast:** `02_packet_timeline_deepgram_stt.png` zeigt: bei hoher RTT (US) gibt es
**keine** Client-Lücke; die Vor-Audio-Zeit ist der 3-RTT-Handshake (TCP 148 / TLS 150 ms).

**Korrektur dokumentiert:** `analysis/02_pcap_communication.ipynb`, Abschnitt §7.4 (die frühere
„93 % Server-Processing"-Deutung ist dort ausdrücklich als Fehlinterpretation der Sendelücke korrigiert).

---

## Frage 3 — „Ist ,Engine schlägt Geografie' bei n=1 EU-Provider überinterpretiert?"

**Antwort:** Berechtigt — es ist eine Anteils-, keine Kausalaussage. Die Inversion **falsifiziert**
„Region erklärt die Latenz hinreichend"; sie beweist nicht „die Engine erklärt alles".

**Beleg — die Inversion in Zahlen:**
- Azure verliert bei STT: `analysis/tables/03_stt_statistics.csv`, Zeile `azure,ttft_ms` p50 = **1715,2**
  vs `deepgram,ttft_ms` **574,6**. Figur `03_stt_cdf.png`.
- Azure gewinnt bei TTS: `analysis/tables/05_tts_statistics.csv`, Zeile `azure,ttfa_ms` p50 = **66,6**
  vs Deepgram 556,5 / OpenAI 954,2. Figur `05_tts_ttfa_cdf.png`.
- Gleicher Provider/Region: `CLAUDE.md`, Provider-Matrix (Azure STT **und** TTS = Italy North).

**Beleg — die Rahmung (kein Datenpunkt, sondern Argument):** `notes/befunde_verstehen.md`, Teil 3
(Konfundierung als Limitation Nr. 1) und Befund 2 (Falsifikation, nicht Kausalbeweis).

**Offener Punkt — „56/56 Slots":** Diese präzise Slot-Median-Aussage („in allen 56 Slots liegt der
Deepgram-Slot-Median unter dem Azure-Slot-Median") ist **nicht** als fertige Zahl in einer CSV. Sie ist
aus `data/processed/layer3_stt.parquet` ableitbar (pro `date×hour`-Slot den Median je Provider berechnen,
dann vergleichen). Falls der Prof darauf besteht: einmal nachrechnen (ein kleines Skript genügt).

---

> Hinweis: Die Roh-PCAPs (`data/layer2/*.pcap`) sind die überzeugendste Live-Demonstration für Frage 2 —
> ein Blick in Wireshark zeigt die leere Lücke unmittelbar. Für Frage 1 ist der Code-Vergleich (zwei
> `ttft`-Definitionen) der direkteste Beleg.

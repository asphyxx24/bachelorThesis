# Bekannte Anomalien & Caveats im Datensatz

> Erstellt: 2026-05-24, parallel zu Notebook 00 (Data Quality)
>
> Dieses Dokument listet alle bekannten Auffaelligkeiten im aufbereiteten Datensatz auf,
> sodass nachfolgende Notebooks und die Thesis-Methodik sie konsistent beruecksichtigen.

---

## 1. Aufbereitungs-Bugs (gefixt am 2026-05-24)

Folgende Bugs in `data/process_raw_data.py` wurden behoben. Die Rohdaten in
`data/layer3/`, `data/layer1/` sind unveraendert; nur die `data/processed/`-Dateien
wurden neu erzeugt.

### 1.1 Slot-Summary-Zeilen als NaN-Erfolge verbucht
- **Was:** Jeder Slot enthaelt am Ende eine Aggregat-Zeile pro `metric` (mit `n`,
  `errors`, `stats: {mean, p50, p95, p99, ...}` statt Einzeltimings).
- **Bug-Effekt:** Diese Zeilen wurden in `layer3_*.parquet` aufgenommen mit
  `connect_ms=NaN`, `ttft_ms=NaN` — wirkten wie fehlgeschlagene Messungen.
- **Fix:** `if "stats" in d: continue` direkt nach Kategorie-Check.
- **Konsequenz:** 421 STT + 868 LLM + 435 TTS = 1.724 Zeilen aus Per-Run-Tabellen entfernt.

### 1.2 `error=""` ohne Timing nicht als Error erkannt
- **Was:** Bei Connection-Failures ohne Server-Antwort (TLS-Timeout, RST etc.) setzt
  der Messclient `error=""` (leerer String) und kein Timing.
- **Bug-Effekt:** `if d.get("error")` evaluiert leeren String als False; Zeile wurde
  als "Erfolg ohne Timing" eingeordnet.
- **Fix:** `has_error = (err_val is not None and err_val != "") or
  (err_val == "" and d.get(primary_timing) is None)`
- **Konsequenz:** 1.473 STT (alle Rev.ai) + 75 LLM + 9 TTS = 1.557 Zeilen jetzt in
  `layer3_errors.parquet`. **Wichtiger neuer Befund:** Rev.ai STT hat dadurch eine
  realistische Fehlerrate von 10,16 % statt 0 %.

### 1.3 `api`-Naming in Errors nicht normalisiert
- **Was:** Layer-3-Messclient logged Errors mit Implementierungs-Namen
  (`deepgram_tts`, `openai_tts`, `azure_tts`, `azure_stt`). Erfolge wurden bereits
  per `API_RENAME` auf `deepgram`/`openai`/`azure` normalisiert; Errors nicht.
- **Effekt vor Fix:** `api='deepgram_tts'` mit 2 Eintraegen in errors, kollidiert
  nicht mit `deepgram`-Eintraegen — Cross-Layer-Joins liefen ins Leere.
- **Fix:** `api: API_RENAME.get(api, api)` auch im `err_rows`-Block.

### 1.4 Rev.ai-Pings komplett aus `layer1_ping.csv` gefiltert
- **Was:** Bei `icmp_blocked=True` (Rev.ai) wurde die Zeile geskippt — Rev.ai
  fehlte komplett im Ping-CSV.
- **Fix:** Zeile mit `packet_loss=100`, `avg_ms=None`, `icmp_blocked=True` wird
  jetzt eingetragen — Provider bleibt in Vollstaendigkeitstabellen sichtbar.
- **Konsequenz:** 91 zusaetzliche Zeilen, Endpoint-Count 6 → 7.

---

## 2. Echte Datenauffaelligkeiten (nicht behebbar, dokumentieren)

### 2.1 Mistral LLM: 6 Stress-Slots
Slots mit <50 Runs (von 100 Soll), korreliert mit HTTP-429-Wellen:

| Datum (UTC) | Stunde | Erfolgreiche Runs | Begleitende 429-Errors |
|-------------|-------:|------------------:|------------------------:|
| 2026-05-04  | 21     | 46                | (ja, mehrere)           |
| 2026-05-08  | 21     | 49                | (ja)                    |
| 2026-05-09  | 12     | 32                | (ja)                    |
| 2026-05-18  | 21     | 10                | (ja)                    |
| 2026-05-19  | 09     | 41                | (ja)                    |
| 2026-05-19  | 18     | **2**             | 24× HTTP 429            |

**Interpretation:** Echte Provider-Capacity-Wellen, nicht Mess-Bug. **Befund fuer Thesis:**
Mistral hat in 18 Tagen 6 spuerbare Stress-Phasen — Charakterisierung des EU-Providers.

**Konsequenz fuer Analyse:** Diese Slots in zeitlichen Stabilitaets-Plots
(Heatmaps, Drift-Linien) zwar einbeziehen, in deskriptiver Statistik aber
ueberpruefen ob sie Quantile verzerren (n < 50 → schwach besetzt).

### 2.2 Deepgram TTS: 147 statt 145 Slots, 2 mit reduzierten Runs
- 2026-05-04 22h: 25 Runs; 2026-05-19 16h: 8 Runs
- Insgesamt 147 Slots statt erwartet 145 — kommt von zwei (date, hour)-Kombinationen
  in Randstunden. Kein Cron-Doppellauf (kein Slot >100 Runs).
- **Konsequenz:** Vernachlaessigbar fuer Aggregat-Statistik (98,62 % Mittelwert pro
  Slot, n_slots = 147 statt 145 macht <2 % Unterschied).

### 2.3 Rev.ai STT: 131 statt 145 Slots, min=29
- Erste vollstaendige Tagessummary erst 2026-05-04. Letzte Messung 2026-05-20 — d.h.
  nur 17 Tage (statt 19). Vermutlich ist Rev.ai-Server haeufiger ausgefallen
  (Connection-Failures, jetzt sichtbar als 10,16 % Error-Rate).
- **Konsequenz:** Quantile bleiben aussagekraeftig (n=13 027 ist riesig).

### 2.4 Groq LLM: 65-68 Runs pro Slot (konstant), 34,97 % Error-Rate
- **Erwartet und im HANDOFF dokumentiert.** Groq Free Tier hat 30 RPM Limit. Sobald
  der Slot mehr als ~67 Runs in 60 Sek versucht, liefert der Server HTTP 429.
- Verteilung der 429er ist gleichmaessig (kein systematischer Tagesausfall).
- **Konsequenz:** Befund ueber Provider-Limit, KEIN Datenqualitaets-Problem.

### 2.5 OpenAI LLM: 1 einzelner Error
Verschwindend gering, kein systematisches Muster.

### 2.6 TTS-Errors (3 azure, 3 deepgram, 5 openai)
Verschwindend, einzelne Server-5xx oder Connection-Drops. Kein Muster.

---

## 3. Layer-1-Einschraenkungen (Mess-Methodik)

### 3.1 Rev.ai blockiert ICMP
- Alle 91 Ping-Slots haben `packet_loss=100`, `avg_ms=NaN`, `icmp_blocked=True`.
- **Substitut**: TCP-SYN-Ping auf Port 443 in `data/layer1_extra/ping_tcp.csv`.
  RTT ~142 ms — sehr nahe an Deepgram (140 ms), beide vermutlich US-Hosting.

### 3.2 Azure (italynorth.\*.speech.microsoft.com) und Rev.ai blockieren UDP-Traceroute
- `destination_reached=False` zu 100 %, aber `asn_path` ist fuer 17/18 Slots verfuegbar
  (Pfad endet wenige Hops vor dem Ziel — typisch fuer Cloud-Provider mit UDP-Filter).
- **Substitut moeglich:** TCP-Traceroute mit Ziel-Port 443 — wurde nicht erhoben,
  weil der `asn_path` fuer die ASN-Analyse ausreicht. Wenn NB 02 (PCAP-Analyse) die
  Ziel-IPs identifiziert, lassen sich Routing-Charakteristika ueber andere Tools
  (BGP-Tabellen, RIPE Atlas) ergaenzen.

### 3.3 Layer-1-TLS-Daten waren komplett NaN
- Alle 162 Eintraege in `data/processed/layer1_tls.csv` hatten `handshake_ms=NaN`
  und `tls_version=NaN`. Ursache unbekannt (vermutlich Subskript-Fehler im EC2-Cron,
  da die Datei trotzdem Spaltenkopf und Zeitstempel hat).
- **Ersatzmessung** am 2026-05-24 von EC2-Frankfurt (selber Vantage Point):
  `data/layer1_extra/tls.csv`, 7 Endpoints × 5 Wiederholungen, alle erfolgreich.
- Ergebnisse siehe Abschnitt 4.

---

## 4. Neue Layer-1-Messungen am 2026-05-24 (Ersatzdaten)

### 4.1 TLS-Handshake (`data/layer1_extra/tls.csv`)

| Endpoint | TLS-Version | Cipher | ALPN | RTT | Handshake |
|----------|-------------|--------|------|----:|----------:|
| api.deepgram.com | **TLS 1.3** | AES_256_GCM_SHA384 | h2 | 140 ms | ~142 ms |
| api.rev.ai | **TLS 1.2** | ECDHE-RSA-AES128-GCM-SHA256 | h2 | 142 ms | **~287 ms** |
| italynorth.stt.speech.microsoft.com | TLS 1.3 | AES_256_GCM_SHA384 | h2 | 12 ms | ~16 ms |
| api.openai.com | TLS 1.3 | AES_256_GCM_SHA384 | h2 | 2 ms | ~6 ms |
| api.groq.com | TLS 1.3 | AES_256_GCM_SHA384 | h2 | 2 ms | ~7 ms |
| api.mistral.ai | TLS 1.3 | AES_256_GCM_SHA384 | h2 | 2 ms | ~7 ms |
| italynorth.tts.speech.microsoft.com | TLS 1.3 | AES_256_GCM_SHA384 | h2 | 16 ms | ~17 ms |

**Hauptbefund:** Rev.ai ist der einzige Provider mit TLS 1.2 — alle anderen TLS 1.3.
TLS 1.3 macht 1-RTT-Handshake, TLS 1.2 macht 2 RTTs. Bei 142 ms RTT bedeutet das
+142 ms Overhead → erklaert einen grossen Teil der hohen Rev.ai-`connect_ms`
(Kampagne: 593 ms Median).

### 4.2 TCP-SYN-Ping (`data/layer1_extra/ping_tcp.csv`)

| Endpoint | TCP-RTT median | ICMP-RTT (Kampagne) | Diff |
|----------|---------------:|--------------------:|-----:|
| api.deepgram.com | 140 ms | 140 ms | 0 |
| api.rev.ai | **142 ms** | nicht messbar | n/a |
| italynorth.stt.speech.microsoft.com | 12 ms | 10 ms | +2 ms |
| api.openai.com | 2 ms | 1 ms | +1 ms |
| api.groq.com | 2 ms | 1 ms | +1 ms |
| api.mistral.ai | 2 ms | 1 ms | +1 ms |
| italynorth.tts.speech.microsoft.com | 16 ms | 11 ms | +5 ms |

**Befund 1:** TCP- und ICMP-RTTs sind innerhalb 1-5 ms identisch — TCP-Ping ist
ein valides Substitut fuer ICMP-geblockte Endpoints.

**Befund 2:** OpenAI, Groq und Mistral haben aus AWS Frankfurt 1-2 ms RTT.
Das ist viel niedriger als die behaupteten US-Hosting-Regionen nahelegen.
Hypothese: alle drei nutzen Cloudflare-Edge in Frankfurt (selber Rechenzentrums-Komplex).
Validierung in NB 02 ueber ASN-Mapping.

### 4.3 DNSSEC (`data/layer1_extra/dnssec.csv`)

| Endpoint | Parent Zone | DS-Records | DNSSEC-Status |
|----------|-------------|-----------:|---------------|
| api.deepgram.com | deepgram.com | 0 | **NICHT signiert** |
| api.rev.ai | rev.ai | 0 | **NICHT signiert** |
| italynorth.\*.speech.microsoft.com | microsoft.com | 0 | **NICHT signiert** |
| api.openai.com | openai.com | 0 | **NICHT signiert** |
| api.groq.com | groq.com | 0 | **NICHT signiert** |
| api.mistral.ai | mistral.ai | 0 | **NICHT signiert** |

**Cross-Check** (gleicher Resolver, gleiche Methode): `cloudflare.com` und `nasa.gov`
liefern DS-Records → Methodik valide.

**Antwort auf Prof-Punkt 1:** Keiner der untersuchten Cloud-AI-API-Provider hat
seine Hauptzone DNSSEC-signiert. DNS-Antwort-Spoofing ist gegen alle 9 Endpoints
prinzipiell moeglich — eine sicherheitsrelevante Beobachtung, die in der
Diskussion erwaehnt werden sollte.

---

## 5. Befunde aus NB 02 (PCAP-Analyse), Stand 2026-05-24

### 5.1 Vier ASNs decken alle 9 Provider
- **AS 13335 Cloudflare** (4/9): openai_llm, openai_tts, groq_llm, mistral_llm
- **AS 8075 Microsoft** (2/9): azure_stt, azure_tts
- **AS 12129 123NET** (2/9): deepgram_stt, deepgram_tts (kleiner US-ISP fuer Anycast-Edges)
- **AS 16509 Amazon AWS** (1/9): revai_stt (Prefix 44.192.0.0/10 → US-West Oregon)

### 5.2 Keine Nebenkommunikation in keinem PCAP
0 von 9 Providern hat innerhalb einer Cold-Start-Messung mehr als eine ASN kontaktiert.
Keine Telemetrie-Endpoints, keine Auth-Server-Roundtrips zu Dritten, keine
CDN-Asset-Loads. Ein API-Aufruf erzeugt genau eine TCP/TLS-Verbindung.

**Caveat:** Single-Slot-PCAP (04.05.) → zeitliche Variation nicht erfasst. Innerhalb
der einen TLS-Session koennte vieles passieren (h2-Multiplexing, Token-Refresh).

### 5.3 TLS-Konfiguration stabil ueber 3 Wochen
Cross-Check PCAP (04.05. EC2) vs. lokal (24.05. EC2): identische TLS-Versionen
und Cipher-Suites fuer alle 7 Endpoints. Rev.ai bestaetigt TLS 1.2 mit
ECDHE-RSA-AES128-GCM-SHA256, alle anderen TLS 1.3 mit TLS_AES_256_GCM_SHA384.

### 5.4 Cross-Layer-Modell `connect ≈ RTT × N_RTTs` bricht bei Cloudflare-fronted
**WICHTIG fuer NB 06:**

| Klasse | Provider | Modell |
|--------|----------|--------|
| Direkt-gehostet | deepgram_stt/tts, revai_stt, azure_stt/tts | `connect ≈ RTT × N_RTTs + Server-Konstante` |
| Cloudflare-fronted | groq, mistral, openai (LLM+TTS) | `connect ≈ Edge-RTT + Edge-Forwarding-Konstante` |

Bei Cloudflare-fronted Providern misst die RTT die Distanz zum Edge in Frankfurt (~1-2 ms), nicht zum Backend. Die "echte" Backend-RTT ist unmessbar. NB 06 muss diese zwei Klassen separat modellieren.

Beispiel: openai_llm hat RTT=1.2ms und app_data_start_ms=135.8ms → 114 RTTs (Unsinn). Tatsaechlich: 1 Edge-RTT (1.2ms) + 130ms Cloudflare-Backend-Forwarding.

### 5.5 Submetriken-Zerlegung pro Provider (Single-Capture 04.05.)

| Provider | TCP-HS | TLS-HS | Proto-Setup | App-Data-Start |
|----------|-------:|-------:|------------:|---------------:|
| azure_stt | 11.4 | 13.0 | **238.4** | 263.7 |
| azure_tts | 11.3 | 12.7 | 81.4 | 106.2 |
| deepgram_stt | 101.8 | 103.7 | 124.6 | 331.0 |
| deepgram_tts | 101.5 | 103.2 | 248.8 | 454.4 |
| groq_llm | 1.6 | 4.8 | 51.6 | 58.5 |
| mistral_llm | 1.1 | 2.8 | 50.6 | 55.1 |
| openai_llm | 1.2 | 4.6 | **129.1** | 135.8 |
| openai_tts | 1.1 | 2.5 | 48.2 | 52.3 |
| revai_stt | 142.2 | **142.3** | 394.1 | 679.6 |

Auffaelligkeiten:
- **azure_stt 238 ms Proto-Setup** = Subscription-Lookup vor STT-Stream
- **revai_stt 142 ms TLS-HS** = exakt 1 RTT mehr als TLS-1.3 (Beweis fuer TLS-1.2-Penalty)
- **openai_llm 129 ms Proto-Setup** = Cloudflare-Backend-Forwarding zum echten LLM

---

## 6. Befunde aus NB 03 (STT-Layer-3), Stand 2026-05-24

### 6.1 TTFT-Reihenfolge wider Erwartung
- Deepgram: 587 ms (schnellster, trotz US-Hosting!)
- Rev.ai: 1404 ms
- Azure: 1719 ms (langsamster, trotz EU-Hosting!)

Erklaerung: bei Azure dominieren 1670 ms Server-Processing (97 % der TTFT), bei Deepgram nur 150 ms (26 %).

### 6.2 Zwei Latenz-Profile

| Provider | Connect/TTFT | Bottleneck | Optimierungs-Hebel |
|----------|-------------:|------------|--------------------|
| deepgram | 74 % | Netzwerk | EU-Hosting / Persistent Connections → TTFT auf ~150 ms |
| revai | 42 % | beide | EU-Hosting + Modell-Wechsel |
| azure | 3 % | Server | nur Modell-/API-Variante hilft |

### 6.3 Cold-Start-Methodik validiert
Lineare Regression Median(ttft) vs run-Index liefert fuer alle 3 Provider slopes |s| < 0.03 ms/run. Keine Connection-Reuse-Artefakte, kein TCP-Caching.

### 6.4 Keine Tageszeit-/Wochenvariation
Heatmaps Stunde × Wochentag sind flach. Infrastruktur ist gut dimensioniert.

### 6.5 Drift ueber 18 Tage minimal
Azure und Rev.ai sehr stabil. Deepgram ±30 ms Tagesvariation wegen Anycast-Edge-Wechsel zwischen 123NET-PoPs.

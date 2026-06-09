# Prof-Gespräch — Figuren-Plan (zur Begutachtung)

Dieses Dokument beschreibt, **welche Figuren** in welcher Reihenfolge gezeigt werden, mit den
zugehörigen Messwerten und Befunden. Es ist als eigenständige Vorlage für eine externe
methodische Begutachtung gedacht.

## Kontext der Arbeit (Kurzfassung)
Bachelorarbeit, Netzwerk-Lehrstuhl. Gemessen wird die Latenz von 9 kommerziellen Cloud-AI-APIs
(je 3 STT, LLM, TTS) aus EU-Sicht (AWS Frankfurt, eu-central-1), im **Cold-Start** (jede Messung
neue TCP+TLS-Verbindung). Drei Messschichten: **L1** Infrastruktur (ICMP/TCP-Ping, DNS, TLS),
**L2** PCAP-Paketmitschnitt, **L3** API-Latenz (`connect_ms`, `ttft_ms`/`ttfa_ms`, `total_ms`).
Juni-Kampagne: 7 Tage × 8 Zeitschlitze, n=100/Provider/Slot = 50.400 Messungen, 0 % fehlende Werte.

**Forschungsfrage:** In welchem Maße erklären Netzwerkeigenschaften (RTT, Protokoll, Region) —
*im Vergleich zur Backend-Engine* — die Latenzunterschiede der APIs aus EU-Sicht?

**Behaupteter Kernbefund:** Aus EU-Sicht erklärt die geografische Netzwerknähe die Latenz nicht
hinreichend; den Hauptanteil trägt die Backend-Engine. Schärfster Beleg: die STT/TTS-Inversion
desselben Providers (Azure). Die Aussage wird als **Falsifikation** der Hypothese „Region erklärt
die Latenz" formuliert, **nicht** als Beweis „die Engine erklärt alles" (Anteils-, keine
Kausalaussage; n=1 EU-Provider je Kategorie).

---

## Das Figuren-Set (5 Figuren, in Reihenfolge)

### A — naive Erwartung: drei RTT-Klassen
- **Datei:** `analysis/figures/01_layer1/png/01_ping_rtt_boxplot.png`
- **Inhalt:** Boxplots (Log-Skala) der RTT pro Endpunkt, drei Referenzlinien.
- **Messwerte:** Cloudflare-Edge (openai/groq/mistral) ~1 ms · Azure Italy North ~10 ms · US (Deepgram/Rev.ai) ~140 ms.
- **Befund:** Etabliert die Erwartung „nah = schnell", die die folgenden Figuren widerlegen.

### B — Kern: Engine schlägt Geografie (STT)
- **Datei:** `analysis/figures/03_stt/png/03_stt_cdf.png`
- **Inhalt:** Drei vollständig getrennte CDF-Kurven von `ttft_ms`. Azure (EU) liegt am weitesten rechts (langsamste).
- **Messwerte:** TTFT-Median Deepgram (US, RTT 138) **575 ms** · Rev.ai 1420 ms · Azure (EU, RTT 10) **1715 ms**; 56/56 Slots ohne Überlappung. Zerlegung: connect 50 ms (Azure) vs 425 ms (Deepgram) → Azure **−375 ms** Netz; ttft 1715 vs 575 → Azure **+1140 ms** Engine; netto 765 ms langsamer.
- **Befund:** Der geografisch nähere Provider (Azure EU) ist 3× langsamer; der Netzwerkvorteil wird von der Engine überkompensiert.

### C — Money-Figure: die Inversion (TTS)
- **Datei:** `analysis/figures/05_tts/png/05_tts_ttfa_cdf.png`
- **Inhalt:** Drei CDF-Kurven von `ttfa_ms`. Azure (EU) liegt jetzt am weitesten **links** (schnellste).
- **Messwerte:** TTFA-Median Azure (EU) **67 ms** · Deepgram (US) 557 ms · OpenAI (US) 954 ms.
- **Befund:** Derselbe Azure gewinnt bei TTS, verliert bei STT. Gleiche Region/RTT, gegensätzliches Ergebnis → die Hypothese „Region erklärt die Latenz" ist falsifiziert.
- **Präsentations-Trick:** B und C nebeneinander zeigen; die Azure-Kurve (in beiden grün) springt von ganz rechts (B, langsamste) nach ganz links (C, schnellste). Die Inversion ist so ohne Worte sichtbar.

### E — Methodik-Beleg: connect-Zerlegung aus dem PCAP
- **Datei:** `analysis/figures/02_pcap/png/02_submetrics_stacked.png`
- **Inhalt:** Gestapelte Balken pro Provider: TCP-Handshake + TLS-Handshake (je ~1 RTT) + „bis 1. App-Daten".
- **Messwerte:** TCP/TLS je ~1 RTT (Deepgram 148/150 ms, Azure 18/13 ms). Dritter Balken = Zeit bis erste Applikationsdaten; bei Azure enthält er ~414 von 446 ms **client-seitige Sendelücke** (kein Server-Processing). n=1 Capture (Single-Slot), nur für Struktur, nicht für Absolutzeiten.
- **Befund:** Unabhängige L2-Kontrolle: TCP- und TLS-Handshake je ~1 RTT, sauber getrennt. (Einstieg — den eigentlichen Beweis, dass die 414 ms client-seitig sind, liefert E′.)

### E′ — Methodik-Vertiefung: Paket-Timeline + Inter-Arrival (PCAP)
- **Dateien:** `analysis/figures/02_pcap/png/02_packet_timeline_azure_stt.png` · `…/02_packet_timeline_deepgram_stt.png`
- **Inhalt:** (A) Timeline mit gebrochener x-Achse — TCP- und TLS-Handshake getrennt, ab SYN paketweise, Client/Server-Richtung getrennt. (B) Inter-Arrival-Stem (Log-Achse) — Δt je Paket; die großen Lücken erscheinen als Ausreißer.
- **Messwerte:** Azure — 3-RTT-Handshake in ~50 ms, dann **358 ms Client-Sendelücke** (87 → 445 ms), Server-Processing **776 ms** (im Inter-Arrival-Stem). Deepgram — RTT-dominierter Aufbau (TCP 148 / TLS 150 ms, je 1 RTT), **keine** Client-Lücke. `connect_ms` (49 ms) ≠ `app_data_start` (446 ms).
- **Befund:** Erfüllt die **drei Prof-Vorgaben** (TCP/TLS getrennt · Inter-Arrival · ab SYN-ACK paketweise) paketgenau und beweist: `connect_ms` ist sauber, die 414-ms-„proto_setup" ist **Client-Wartezeit, kein Server-Processing**. Der Deepgram-Kontrast zeigt, dass bei hoher RTT die Pre-Audio-Zeit der Handshake selbst ist.
- **Reproduzierbar:** `analysis/figures/02_pcap/build_packet_timeline.py` (`plot_packet_timeline(provider)`).

### F — Implikation: Latenz vs. Zuverlässigkeit (Pipeline)
- **Datei (Empfehlung):** `analysis/figures/07_e2e/png/07_e2e_availability.png`
- **Alternative/Reserve:** `analysis/figures/07_e2e/png/07_e2e_montecarlo.png`
- **Inhalt (availability):** Streudiagramm aller 27 STT+LLM+TTS-Kombinationen: x = E2E-Latenz-Median, y = Joint-Completion-Probability.
- **Messwerte:** beste Latenz-Kombi Deepgram+Groq+Azure **1134 ms**, läuft aber nur in **67 %** der Fälle durch (Groq 32,9 % HTTP-429, Free-Tier); +163 ms (Mistral statt Groq) → **96 %**. E2E gesamt: 0/27 Kombinationen < 1000 ms; Monte-Carlo der empirischen Verteilungen: median-of-sum weicht 1,4 % von der Median-Addition ab, p95 ~1350 ms, nur ~24 % der Einzelläufe < 1 s.
- **Befund:** Die schnellste Pipeline ist nicht die zuverlässigste (Latenz-vs-Zuverlässigkeit-Tradeoff); das 1-s-Budget wird im Cold-Start nicht erreicht.
- **Caveat (am Bild sagen):** Joint-Completion = Produkt der Verfügbarkeiten setzt **Unabhängigkeit** voraus. Groqs 67 % ist ein **deterministisches Free-Tier-Quota** (HTTP 429 nach ~67/Slot), kein i.i.d.-Zufall → die y-Achse ist eine **obere Schranke / Tarif-Artefakt**, qualitativ als Tradeoff lesen.

---

## Bekannte, offen deklarierte Limitationen
- Region und Engine sind konfundiert (n=1 EU-Provider je Kategorie) → Anteils-, keine Kausalaussage.
- E2E ist Median-Addition (per Monte-Carlo abgesichert), keine end-to-end gemessene Pipeline.
- Cross-Layer-connect-Modell beruht auf n=4 direkten Providern (r bewusst nicht als Gütemaß).
- Keine Transkript-Korrektheit (WER) gemessen — nur Transkript-Längen gespeichert.
- 1-Sekunden-Budget ist eine pragmatische Obergrenze (Turn-Taking-Literatur nennt 200–300 ms).
- L3-Kampagne lief auf anderem AWS-Account (eu-central-1); cross-vantage validiert, nur Deepgram-Anycast weicht ab.
- STT wird als Full-Utterance-Dump gemessen (kein Real-Time-Pacing).

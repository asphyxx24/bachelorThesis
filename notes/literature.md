# Literatursammlung — Stand 2026-05-04

## 1. Cloud-Latenz-Messmethodik

### Corneo et al. (2021) — "Surrounded by the Clouds"
- **Publiziert:** The Web Conference 2021 (WWW '21)
- **Methodik:** 12-monatige Kampagne, 8.500 RIPE Atlas Probes, 189 Rechenzentren, 9 Provider
- **Relevanz:** Gleiche Grundidee (Client-zu-Cloud-Latenz), vergleicht mit menschlichen Wahrnehmungsschwellen
- **Link:** https://dl.acm.org/doi/10.1145/3442381.3449854

### Palumbo, Aceto, Botta (2019/2021) — "Cloud-to-User Latency: Azure and AWS"
- **Publiziert:** IEEE GLOBECOM 2019 + Computer Networks (Elsevier, 2021)
- **Methodik:** 14-taegige Kampagne, 25 Vantage Points, AWS + Azure
- **Relevanz:** Fast identisches Messdesign wie unsere Arbeit (14 Tage, AWS, Azure)
- **Link:** https://ieeexplore.ieee.org/document/9013343/

### Charyyev, Arslan, Gunes (2020) — "Cloud Datacenters vs Edge Servers"
- **Publiziert:** IEEE GLOBECOM 2020
- **Relevanz:** 58% der Nutzer erreichen Edge in <10ms, nur 29% Cloud-RZ — erklaert Anycast-Vorteil (Deepgram)
- **Link:** https://ieeexplore.ieee.org/document/9322406/

### Iorio et al. (2021) — "When Latency Matters"
- **Publiziert:** ACM SIGCOMM Computer Communication Review
- **Relevanz:** Cross-Layer-Latenzanalyse, zeigt dass Netzwerknaehe nur ein Teil des Problems ist
- **Link:** https://dl.acm.org/doi/10.1145/3503954.3503956

---

## 2. TLS/WebSocket-Verbindungsaufbau

### "Layered Performance Analysis of TLS 1.3 Handshakes" (2026)
- **Publiziert:** arXiv (2603.11006)
- **Methodik:** Zerlegt Latenz in 5 Schichten: TCP-HS, TCP-to-TLS Delay, TLS-HS, TLS-to-Application Delay, Application Response
- **Relevanz:** SEHR HOCH — gleiche Zerlegungslogik wie unsere Submetriken. "TLS-to-Application Delay" = unser proto_setup_ms
- **Link:** https://arxiv.org/html/2603.11006

### "Enhanced Performance for the encrypted Web through TLS" (2019)
- **Publiziert:** arXiv (1902.02531)
- **Relevanz:** TLS 1.3 beschleunigt Verbindungsaufbau um ~30% gegenueber TLS 1.2
- **Link:** https://arxiv.org/pdf/1902.02531

---

## 3. Voice-Pipeline / Konversations-KI-Latenz

### Jacoby et al. (2024) — "Human Latency Conversational Turns"
- **Publiziert:** arXiv (2404.16053), eingereicht fuer UIST 2024
- **Relevanz:** Definiert 200-300ms-Fenster fuer natuerliche Konversation als Obergrenze
- **Link:** https://arxiv.org/abs/2404.16053

### Messerschmidt et al. (2026) — "Impact of Response Latency on Human-LLM Interaction"
- **Publiziert:** CHI 2026
- **Relevanz:** Nutzer bewerten 2s-Antworten als WENIGER durchdacht als 9s-Antworten — Latenz ist Designvariable
- **Link:** https://dl.acm.org/doi/full/10.1145/3772318.3790716

### "Building Enterprise Realtime Voice Agents from Scratch" (2026)
- **Publiziert:** arXiv (2603.05413)
- **Methodik:** Deepgram STT + vLLM + ElevenLabs TTS — P50 TTFA 947ms
- **Relevanz:** Direkt vergleichbar, nutzt teils gleiche Provider
- **Link:** https://arxiv.org/html/2603.05413v1

### Ethiraj et al. (2025) — "Low-Latency Voice Agents for Telecommunications"
- **Publiziert:** arXiv (2508.04721)
- **Relevanz:** Gleiche Pipeline-Architektur (STT->LLM->TTS), aber on-premise — untere Schranke fuer Latenz
- **Link:** https://arxiv.org/abs/2508.04721

---

## 4. Industrie-Benchmarks

### Artificial Analysis — LLM API Performance
- **Methodik:** 8 Tests/Tag (alle 3h), TTFT + Tokens/s — fast identisches Intervall wie unsere Kampagne
- **Link:** https://artificialanalysis.ai/methodology/performance-benchmarking

### MLPerf Inference v5.0/v5.1 (MLCommons, 2025)
- **Latenz-Constraints:** Llama-3.1-8B interaktiv: TTFT <=500ms, TPOT <=30ms
- **Relevanz:** Industriestandard fuer akzeptable LLM-Latenz
- **Link:** https://mlcommons.org/2025/04/llm-inference-v5/

### Pipecat STT Benchmark
- **Methodik:** 1.000 Samples, TTFS als Hauptmetrik, Deepgram/Azure/20+ Provider
- **Relevanz:** Open-Source STT-Benchmark, misst ab Sprechende (nicht ab Verbindungsaufbau wie wir)
- **Link:** https://github.com/pipecat-ai/stt-benchmark

### Picovoice TTS Latency Benchmark
- **Methodik:** Voice-Assistant-Simulation, TTFA-Messung
- **Link:** https://github.com/Picovoice/tts-latency-benchmark

### Gladia — "How to Measure Latency in STT"
- **Relevanz:** Definiert TTFB, TTFS, RTF sauber — gute Referenz fuer Metrik-Definitionen
- **Link:** https://www.gladia.io/blog/measuring-latency-in-stt

---

## 5. Cold Start (Hintergrund)

### Bermbach et al. (2023/2025) — "Cold Start Latency in Serverless Computing"
- **Publiziert:** ACM Computing Surveys (2025)
- **Relevanz:** Taxonomie der Cold-Start-Latenzquellen — methodisch verwandt mit unserem connect_ms
- **Link:** https://dl.acm.org/doi/10.1145/3700875

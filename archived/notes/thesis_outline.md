# Thesis-Gerüst (Arbeitsstand)

> Struktur der BA. **Noch kein Fließtext** — nur was in welches Kapitel gehört, mit
> Verweis auf Figure/Tabelle/Befund. Wird am Ende ausformuliert.
> **Titel (neu, Arbeit noch nicht angemeldet — Stand 2026-06-08):**
> *Engine schlägt Geografie: Netzwerk-, Protokoll- und Latenzanalyse kommerzieller
> Cloud-AI-APIs einer Echtzeit-Voice-Pipeline aus EU-Perspektive.*
> Alternativen: (a) *„Engine schlägt Geografie: Warum Netzwerknähe die Latenz kommerzieller
> Cloud-AI-Voice-APIs nicht erklärt"*; (b) alter Titel *„Kommerzielle Cloud-AI-APIs unter der
> Lupe: …"* (neutral, ohne Befund im Titel).
>
> **Leitthese / Framing (Reframe 2026-06-08, siehe `STANDORTBESTIMMUNG_2026-06-08.md`):**
> „**Engine schlägt Geografie**" — aus EU-Sicht erklärt die Netzwerknähe die wahrgenommene
> Latenz kommerzieller AI-APIs *gerade nicht*; die Backend-Engine dominiert. Das negative,
> kontraintuitive Ergebnis IST der Beitrag.

**Forschungsfrage (geschärft 2026-06-08):** In welchem Maße erklären Netzwerk- und
Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region) — *im Vergleich zur
Backend-Verarbeitung der Engine* — die Latenzunterschiede kommerzieller Cloud-AI-APIs
(STT/LLM/TTS) aus EU-Perspektive, und wie wirkt sich die Provider-Wahl auf die Gesamtlatenz
einer sequenziellen Cold-Start-Voice-Pipeline aus?

> Warum so formuliert: Diese Fassung ist in *beide* Richtungen beantwortbar — „Netzwerk
> erklärt *weniger* als die Engine" ist eine gültige, interessante Antwort, keine gescheiterte
> Hypothese. Die alte Fassung („*welche* Netzwerkeigenschaften erklären…") setzte voraus, dass
> das Netzwerk es erklärt — und kollidierte damit mit dem Befund.
>
> **Teilfragen (mappen 1:1 auf die Kapitel):**
> - TF1 — Wie unterscheiden sich die Provider auf Netzwerkebene? (L1/L2 → Kap. 5.1/5.2)
> - TF2 — Welcher Anteil der Latenz entfällt auf Netzwerk vs. Verarbeitung? (L3 + Cross-Layer → 5.3–5.6)
> - TF3 — Was folgt daraus für die Provider-Wahl in einer Voice-Pipeline? (E2E → 5.7)

**Drei Beiträge (Contribution) — NEU sortiert:**
- **C1 (Kernbefund) — „Engine schlägt Geografie":** Aus EU-Vantage dominiert die Backend-Engine,
  nicht die Netzwerknähe, die user-perceived Latenz. Schärfster Beleg = **standort-invariante
  STT/TTS-Inversion desselben EU-Providers** (Azure: bei STT klar geschlagen, bei TTS klar
  gewinnend — gleicher Standort/RTT, gegensätzliches Ergebnis). (NB 03 + 05)
- **C2 — Drei-Schichten-Messmethodik + Cloudflare-Fronting-Grenze:** Reproduzierbare L1/L2/L3-
  Zerlegung (Connect/TLS/Cold-Start), die Industrie-Benchmarks so nicht leisten; quantifiziert
  den Cloudflare-Fronting-Effekt (4/9 Provider) als **Gültigkeitsgrenze** reiner Netzwerkmessung. (NB 01 + 02)
- **C3 (Methoden-Baustein, NICHT Headline) — Ping-basierte connect-Klassen-Heuristik:**
  `connect_ms ≈ N_RTTs × ping + k` sagt die connect-Latenz**klasse** direkt-gehosteter Provider
  *ohne API-Kosten* voraus. **Limitation offen: nur 4 Punkte, N_RTTs aus Protokoll/PCAP begründet,
  nicht aus dem Fit; r bewusst nicht als Gütemaß verwendet.** (NB 06)

> ⚠️ Bewusst NICHT mehr Headline: das „r≈0.999"-Modell (n=4, in starker Lesart Tautologie) und
> das E2E-„0/27 unter 1 s" (reine Median-Addition, willkürliches 1-s-Budget). Beide werden
> ehrlich entschärft (s. u.), nicht als Kernbeitrag getragen.

---

## 1. Einleitung
- Motivation: Echtzeit-Voice-Assistenten; Latenz ist *das* UX-Problem.
- **Aufhänger (kontraintuitiv):** Intuition sagt „näher = schneller" → die Arbeit zeigt, dass das
  aus EU-Sicht für kommerzielle AI-APIs *nicht* gilt.
- Problem: Cloud-AI-APIs als Blackbox; Latenz aus EU-Sicht + ihre Treiber unklar.
- Forschungsfrage (oben).
- Beiträge C1–C3 (neue Reihenfolge).
- Aufbau der Arbeit.

## 2. Grundlagen
- Voice-Pipeline STT → LLM → TTS (sequenziell, Cold-Start).
- Latenz-Metriken: `connect_ms`, `ttft_ms`, `ttfa_ms`, `ttl_ms`, `total_ms` (Definitionen).
- Netzwerk-Stack: DNS, TCP-Handshake (1 RTT), TLS 1.2 vs 1.3 (2 vs 1 RTT), RTT, Anycast, CDN/Cloudflare-Fronting.
- Cold-Start vs. Warm (warum Cold-Start gemessen wird → Methodik).

## 3. Verwandte Arbeiten
- Abgrenzung zu Industrie-Benchmarks (Artificial Analysis u. a.): messen STT/TTS nur end-to-end
  *inkl. Netz*, **ohne** Connect/TLS/Cold-Start-Zerlegung und **ohne** Vantage-Point-Kontrolle →
  genau diese Zerlegung ist der Delta dieser Arbeit.
- TLS-1.3-Handshake-Schichtanalyse (arXiv 2603.11006 — gleiche Zerlegungslogik).
  **⚠️ TODO: arXiv 2603.11006 + 2603.05413 per Web verifizieren (Zukunfts-IDs) — bei Nicht-Existenz Ersatz.**
- Latenz-/CDN-Studien + Konversations-Latenzschwelle (Jacoby, arXiv 2404.16053: 200–300 ms) aus `notes/literature.md`.

## 4. Methodik  ← **Prof-Kritik „Methodik unklar" wird HIER entwaffnet**
- Drei-Schichten-Messdesign (L1 Infra · L2 PCAP · L3 API-Latenz) — zugleich Beitrag C2.
- Provider-Matrix (9 Provider, 3 Kategorien, Regionen, Protokolle).
- **Cold-Start-Rationale**: misst Overhead jeder neuen Gesprächssession (Serverless, nach
  Inaktivität); **empirisch belegt echt** (connect_ms über Run-Index flach → keine Session-Resumption).
- **4.x `connect_ms`-Asymmetrie-Tabelle (NEU, kritisch):** STT misst connect_ms am realen
  In-Pfad-WebSocket (ttft connect-*exklusiv*); LLM/TTS am sofort geschlossenen Wegwerf-Socket
  (ttft/ttfa connect-*inklusiv*). → Quer wird nur **„user-perceived Cold-Start"** verglichen
  (STT = connect+ttft, LLM/TTS = ttft/ttfa), **nie rohes connect_ms cross-Kategorie**.
- **4.x STT-Messung offen deklariert (NEU, kritisch):** STT als Full-Utterance-**Batch-Dump**
  gemessen (kein Real-Time-Pacing) → mit Sensitivitäts-Hinweis, wie sich der STT-Anteil ändert,
  wenn STT real-time parallel zum Sprechen liefe.
- Feste Inputs pro Kategorie (Fairness). Raw-WebSocket ohne SDK.
- Kampagne: 56 Slots (7 Tage × 8), n=100/Provider/Slot.
- Vantage Point: AWS EC2 eu-central-1 (Frankfurt).
- **4.x Validierung** ← Prof-Punkt: interne Konsistenz, Cross-Vantage-Reproduktion (8/9 <1 ms),
  Layer-2-PCAP als **Struktur**-Validierung (TLS-Version, Fronting, RTT-Anzahl — nicht Absolutzeiten;
  Caveat: anderer Account/Tag, n=1). (→ `findings.md` V1–V3)

## 5. Ergebnisse
| Abschnitt | Inhalt | Notebook | Leitfigur |
|-----------|--------|----------|-----------|
| 5.1 Layer 1 — Infrastruktur | RTT-Klassen, TLS-Versionen, DNSSEC, ASN (Methoden-Glaubwürdigkeit) | 01 | 01_ping_rtt_boxplot, 01_tls_handshake |
| 5.2 Layer 2 — Protokoll | Cloudflare-Fronting (4/9), Submetriken, keine Nebenkomm. | 02 | 02_communication_matrix |
| **5.3 KERNBEFUND — Engine schlägt Geografie (STT)** | Deepgram US (RTT 138) schlägt Azure EU (RTT 10): ttft 575 vs 1715 ms, 56/56 Slots | 03 | 03_stt_connect_anteil |
| **5.4 KERNBEFUND — Die Inversion (TTS)** | *Gleicher* EU-Provider Azure gewinnt jetzt (ttfa 67 < 557 < 954) → isoliert den Engine-Effekt | 05 | 05_tts_ttfa_cdf |
| 5.5 Layer 3 — LLM | Groq LPU schnellster; Cloudflare-Cluster; **Verfügbarkeit neben Latenz** (Groq 33 % 429) | 04 | 04_llm_ttft_cdf |
| 5.6 Cross-Layer-Heuristik (Methoden-Baustein, ~½ Seite) | connect ≈ N_RTT × ping für die 4 direkten Provider; **n=4-Limitation offen, kein r-Hero** | 06 | 06_cross_layer_scatter |
| 5.7 E2E — illustrative Implikation | Streaming-Budget, **Monte-Carlo-CI statt Median-Addition** (Δ<1,4 %, p90/p95, ~24 % Runs<1 s); **Latenz-vs-Zuverlässigkeit-Tradeoff** (Pareto: groq 67 %→mistral 96 %→openai 99,9 %, LLM ist der Hebel); Batch-Szenario gestrichen | 07 | 07_e2e_budget, 07_e2e_montecarlo, 07_e2e_availability |

## 6. Diskussion
- **Hauptbefund (C1): Engine-Speed > Netzwerknähe** — die Region erklärt die Latenz *nicht*;
  die STT/TTS-Inversion ist der saubere experimentelle Beleg.
- Cloudflare-Fronting + Anycast → wo das Cross-Layer-Modell bricht (C2), Modellgrenze als *Resultat*.
- Cross-Layer als kostenlose connect-Klassen-Heuristik (C3) — Nutzen *und* Grenzen (n=4) ehrlich.
- TLS-1.2-Penalty (Rev.ai) quantifiziert (eine konsistente Definition, ~+153 ms / +1 RTT).
- Praktische Implikation: Provider-Wahl für Voice-Pipelines (Latenz ↔ Verfügbarkeit, z. B. Groq-429).
- Sicherheit: DNSSEC 0/6 Zonen — Spoofing prinzipiell möglich.
- **Limitationen — offensiv VOR dem Prof benennen:**
  1. **E2E nie als echte Pipeline gemessen** (Median-Addition; mit Monte-Carlo nachgeschärft).
  2. **Cross-Layer-Heuristik n=4**, N_RTTs aus Protokoll begründet (nicht aus dem Fit).
  3. **Region/Engine perfekt konfundiert** (n=1 EU-Provider pro Kategorie) → Kausalaussage nur eingeschränkt.
  4. STT als Batch-Dump (kein Real-Time-Pacing); 1-s-Budget vs. Jacobys 300 ms eingeordnet.
  5. Nur Cold-Start; 7-Tage-Fenster; Kampagne aus anderem AWS-Account; Deepgram-Anycast; Provider-Errors (Groq/Rev.ai).

## 7. Fazit & Ausblick
- Zusammenfassung C1–C3 (Engine>Region als Kern).
- Future Work: Warm/persistente Verbindungen, mehr EU-Provider (gegen Konfundierung), echte
  E2E-Pipeline-Messung, real-time-gepactes STT, längere Kampagne, weitere Vantage Points.

---

## Offene Struktur-Entscheidungen
- [ ] Ergebnisse + Diskussion getrennt (klassisch) oder pro Befund integriert? (aktuell: getrennt)
- [ ] Layer 2 als eigenes Ergebnis-Kapitel oder in Methodik-Validierung? (aktuell: Ergebnis 5.2)
- [ ] Amazon Polly (Intra-Cloud-Exkurs) rein oder raus? (aktuell: raus / optionaler Anhang)
- [ ] Titelschärfung „Engine schlägt Geografie" mit Prof abstimmen? (registrierter Titel bleibt sonst)

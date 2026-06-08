# Thesis-Gerüst (Arbeitsstand)

> Struktur der BA. **Noch kein Fließtext** — nur was in welches Kapitel gehört, mit
> Verweis auf Figure/Tabelle/Befund. Wird am Ende ausformuliert.
> Titel: *Kommerzielle Cloud-AI-APIs unter der Lupe: Netzwerk-, Protokoll- und
> Latenzanalyse einer Echtzeit-Voice-Pipeline.*

**Forschungsfrage:** Welche Netzwerk-/Infrastruktureigenschaften (RTT, Protokoll,
Hosting-Region) erklären die Latenzunterschiede kommerzieller Cloud-AI-APIs (STT/LLM/TTS)
aus EU-Sicht — und wie beeinflusst die Provider-Wahl die Gesamtlatenz einer sequenziellen
Voice-Pipeline?

**Drei Beiträge (Contribution):**
- C1 — Empirisch validiertes Cross-Layer-Modell: `connect_ms ≈ N_RTTs × ping + k` (r≈0.999).
- C2 — Quantifizierung des Cloudflare-Fronting-Effekts (4/9 Provider) + Anycast-Varianz.
- C3 — „Engine-Speed schlägt EU-Region" (kontraintuitiv) + Zerlegung des 1-s-Latenzbudgets.

---

## 1. Einleitung
- Motivation: Echtzeit-Voice-Assistenten; ~1 s Latenzbudget für natürliche Konversation.
- Problem: Cloud-AI-APIs als Blackbox; Latenz aus EU-Sicht + Treiber unklar.
- Forschungsfrage (oben).
- Beiträge C1–C3.
- Aufbau der Arbeit.

## 2. Grundlagen
- Voice-Pipeline STT → LLM → TTS (sequenziell, Cold-Start).
- Latenz-Metriken: `connect_ms`, `ttft_ms`, `ttfa_ms`, `ttl_ms`, `total_ms` (Definitionen).
- Netzwerk-Stack: DNS, TCP-Handshake (1 RTT), TLS 1.2 vs 1.3 (2 vs 1 RTT), RTT, Anycast, CDN/Cloudflare-Fronting.
- Cold-Start vs. Warm (warum Cold-Start gemessen wird → Methodik).

## 3. Verwandte Arbeiten
- TLS-1.3-Handshake-Schichtanalyse (arXiv 2603.11006 — gleiche Zerlegungslogik).
- Latenz-/CDN-Studien (aus `notes/literature.md` ergänzen).

## 4. Methodik  ← **Prof-Kritik „Methodik unklar" hier adressieren**
- Drei-Schichten-Messdesign (L1 Infra · L2 PCAP · L3 API-Latenz).
- Provider-Matrix (9 Provider, 3 Kategorien, Regionen, Protokolle).
- **Cold-Start-Rationale**: misst Overhead jeder neuen Gesprächssession (Serverless, nach Inaktivität).
- Feste Inputs pro Kategorie (Fairness). Raw-WebSocket ohne SDK.
- Kampagne: 56 Slots (7 Tage × 8), n=100/Provider/Slot.
- Vantage Point: AWS EC2 eu-central-1 (Frankfurt).
- **4.x Validierung** ← Prof-Punkt: interne Konsistenz, Cross-Vantage-Reproduktion (8/9 <1 ms),
  Layer-2-PCAP als unabhängige Cross-Validierung. (→ `findings.md` V1–V3)

## 5. Ergebnisse
| Abschnitt | Inhalt | Notebook | Leitfigur |
|-----------|--------|----------|-----------|
| 5.1 Layer 1 — Infrastruktur | RTT-Klassen, TLS-Versionen, DNSSEC, ASN | 01 | 01_ping_rtt_boxplot, 01_tls_handshake |
| 5.2 Layer 2 — Protokoll | Cloudflare-Fronting, Submetriken, keine Nebenkomm. | 02 | 02_communication_matrix |
| 5.3 Layer 3 — STT | Engine vs. Netzwerk (Deepgram US schlägt Azure EU) | 03 | 03_stt_connect_anteil |
| 5.4 Layer 3 — LLM | Groq LPU schnellster, Cloudflare-Cluster | 04 | 04_llm_ttft_violin |
| 5.5 Layer 3 — TTS | Azure-Inversion (EU gewinnt) | 05 | 05_tts_ttfa_violin |
| 5.6 Cross-Layer-Modell | connect ≈ N_RTT × ping, r≈0.999 | 06 | 06_cross_layer_scatter |
| 5.7 E2E-Pipeline | 1-s-Budget, 0/27 unter 1 s | 07 | 07_e2e_budget |

## 6. Diskussion
- Hauptbefund: Engine-Speed > Netzwerknähe (C3).
- Cloudflare-Fronting + Anycast → wo das Cross-Layer-Modell bricht (C2).
- TLS-1.2-Penalty (Rev.ai) quantifiziert.
- Praktische Implikation: Provider-Wahl für Voice-Pipelines.
- Sicherheit: DNSSEC 0/7 — Spoofing prinzipiell möglich.
- **Limitationen**: nur Cold-Start; 7-Tage-Fenster; Kampagne aus anderem AWS-Account;
  Deepgram-Anycast; n=100 mit Provider-Errors (Groq/Rev.ai).

## 7. Fazit & Ausblick
- Zusammenfassung C1–C3.
- Future Work: Warm/persistente Verbindungen, mehr Provider, längere Kampagne, weitere Vantage Points.

---

## Offene Struktur-Entscheidungen
- [ ] Ergebnisse + Diskussion getrennt (klassisch) oder pro Befund integriert? (aktuell: getrennt)
- [ ] Layer 2 als eigenes Ergebnis-Kapitel oder in Methodik-Validierung? (aktuell: Ergebnis 5.2)
- [ ] Amazon Polly (Intra-Cloud-Exkurs) rein oder raus? (aktuell: raus / optionaler Anhang)

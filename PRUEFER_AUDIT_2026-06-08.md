# Prüfer-Report — Bachelorarbeit "Cloud-AI-APIs unter der Lupe"

> **Erzeugt:** 2026-06-08 durch einen read-only Multi-Agent-Audit (49 Agenten, 4 Map-Regionen,
> 7 Prüf-Dimensionen, 12 Kern-Claims × 3 unabhängige Skeptiker). Rolle: kritischer Zweitgutachter.
> Alle Zahlen aus der Juni-Kampagne (`data/processed/*.parquet`) unabhängig nachgerechnet.
> **Hinweis:** Dies ist ein KI-Diagnose-Dokument, kein Thesis-Text und keine zitierbare Quelle.
>
> Verifikations-Bilanz: **9 Claims bestätigt, 2 widerlegt (C1, C4), 1 unklar (C5)**.
> Findings: 8 critical · 17 high · 12 medium · 8 low.

---

## 1. Executive Summary

Die **Analyse steht, die Arbeit ist aber GEFÄHRDET** — nicht wegen der Daten (die sind exzellent: 0 % NaN, n=100 strukturell exakt, 50.400 Records), sondern wegen drei Dingen, die den Prof genau an seinem Kritikpunkt "Methodik unklar" treffen werden:

1. **0 % Fließtext.** Es existiert keine einzige Prosa-/`.tex`-Datei. Die gesamte Thesis ist noch zu schreiben — das ist keine Restarbeit, das ist die Hauptarbeit (`notes/thesis_outline.md:3`).
2. **Der beworbene Kernbefund (C1, r=0.999) ist der schwächste Punkt der Arbeit.** Er beruht auf n=4 Punkten in 2 Clustern, das N_RTTs ist rückwärts gefittet, und in der starken Lesart ist er eine Tautologie ("Summe von RTTs ≈ Anzahl RTTs × RTT"). Genau diesen verkaufst du als "Contribution" — und genau hier hakt der Prof ein. Die eigentlich starke Contribution (Engine > Region, C2/C3) steht im Schatten.
3. **Headline-Zahlen sind durchgängig veraltet (Mai statt Juni).** Die Verifikation hat C1, C4, C5 (Zahl 1157) und C7 (Penalty +142) **widerlegt**, weil HANDOFF/CLAUDE/README teils noch Mai-Werte tragen. Jede Gegenprüfung Briefing-vs-Notebook erzeugt sofort einen Widerspruch.

**Kurs:** Datenfundament tragfähig → umsteuern bei Framing der Contribution + Zahlen synchronisieren + Methodik-Limitationen offensiv benennen, DANN schreiben (Methodik zuerst).

---

## 2. Was existiert

| Bereich | Stand | Details |
|---|---|---|
| **Rohdaten** | vollständig, validiert | `data/layer3/*.jsonl` (56 Slots, 50.400 Per-Run + 667 Summary), `data/processed/*.parquet` (STT 16.227 / LLM 14.729 / TTS 16.796, 0 NaN), Raw→Parquet deterministisch reproduzierbar |
| **Layer 1** | vollständig (7 Tage in-Kampagne) | `layer1_ping.csv`, `dns.csv`, `traceroute.csv`; gültige TLS-Quelle nur in `layer1_extra/tls.csv` |
| **Layer 2** | n=1/Provider, post-hoc | 9 PCAP vom 2026-06-08, **andere Instanz/AWS-Account**, Rev.ai-Capture kaputt (`PROVENANCE.md`) |
| **Notebooks** | 8/8 gerechnet, 8.6. neu | NB00–07, 7 Tabellen, ~19 Figures; intern weitgehend konsistent |
| **Mess-Code** | implementiert, gelaufen | 9 Provider-Module, alle STT Raw-WebSocket; **keine echte E2E-Pipeline** (run.py kennt kein `e2e`, chain.py fehlt) |
| **Doku (steuernd)** | teils STALE | HANDOFF on-disk = Juni (ok); CLAUDE.md + README teils = Mai (falsch) |
| **Schreibstand** | **0 % Prosa** | nur Stichpunkt-Gerüst (`thesis_outline.md`) + `findings.md` (13 Befunde) |

---

## 3. Was hält (nachgerechnet bestätigt, verteidigungsfähig)

Diese Punkte sind durch unabhängige Nachrechnung aus den Rohdaten **confirmed** und tragen in der Verteidigung:

- **C2 — STT Engine > Netzwerk (confirmed, conf 3/3):** Deepgram (USA, RTT 138 ms) ttft 574,6 ms schlägt Azure (EU, RTT 10 ms) ttft 1715,2 ms. In **56/56 Slots** ohne Überlappung. Fairer Cold-Start (connect+ttft): Deepgram 999 ms vs Azure 1768 ms. Quelle: `layer3_stt.parquet`, `03_stt_statistics.csv`. **Das ist dein stärkster Befund.**
- **C3 — TTS-Inversion (confirmed, conf 3/3):** Azure ttfa 66,6 ms < Deepgram 556,5 ms < OpenAI 954,2 ms. IQRs vollständig disjunkt, Azure gewinnt 56/57 Slots. Quelle: `05_tts_statistics.csv`.
- **C6 — Cloudflare-Fronting (confirmed, conf 3/3):** 4/9 Provider-Slots (groq, mistral, openai-LLM, openai-TTS) auf AS13335. **Dreifach unabhängig belegt** (PCAP-IP→ASN, eigene IP-Range-Prüfung gegen Cloudflare-CIDRs, Traceroute über alle 7 Tage). Modellbruch quantifiziert (eff_N 7–180 statt 3).
- **C8 — Datenintegrität (confirmed):** 0 % NaN, alle 504 (Slot×Provider)-Zellen exakt 100 Versuche, Run-Indizes 0–99 lückenlos. **Offensiv als Qualitätsnachweis zeigen.**
- **Cold-Start ist echt erzwungen (low severity, positiv):** connect_ms über Run-Index-Quartile flach (Deepgram Q1–Q4: 424,8/425,8/424,6/424,8 ms) → keine TLS-Session-Resumption. NB03 testet das per Regression. Belegt, dass Cold-Start keine nachträgliche Rationalisierung ist.
- **Fehler-Ausschluss sauber:** Errors liegen separat (`layer3_errors.parquet`), kein STT-Erfolg mit transcript_len=0, kein TTS-Erfolg mit audio_bytes=0.

**E1, E2, E3, E4 wurden ebenfalls confirmed** — das sind aber die *Kritik*-Findings (s. u.), nicht Stärken.

---

## 4. Angriffsfläche (nach Severity)

### 🔴 KRITISCH

**A1 — C1-Kernbefund: r=0.999 ist überverkauft, Headline-Zahl WIDERLEGT, in starker Lesart Tautologie**
- *Problem:* Die behaupteten `slope=1.013, intercept=8.5, r=0.9992` sind **nicht reproduzierbar** (refuted, conf 0/3). Der echte 4-Punkt-Fit ist `1.006 / 10.7 / 0.99932`. Die 1.013 reproduzieren sich nur im 5-Punkt-Fit *inkl.* Rev.ai (1.015), der im Notebook gar nicht ausgegeben wird → die Headline mischt zwei Regressionen. Zudem: 4 Punkte in 2 Clustern (Azure ~31, Deepgram ~276–413) → hohes r ist mathematisch fast erzwungen, sagt nichts über Modellgüte. N_RTTs ist rückwärts gefittet (Deepgram-TTS N=2 vs Azure-TTS N=3 bei *gleicher* Protokollklasse "HTTPS Stream"; setzt man Deepgram-TTS auf N=3, fällt r auf 0.957).
- *Beleg:* `06_cross_layer_correlation.ipynb` CELL[5] Output "slope=1.006, intercept=10.7"; `06_cross_layer_master.csv` (Azure-STT eff_N=4.82 bei N_model=3); HANDOFF.md Kernbefund 1.
- *Prof-Frage:* „Auf wie vielen Punkten beruht r=0.999? Vier? Davon zwei mit identischem x? Wie haben Sie N_RTTs bestimmt — gemessen oder gewählt, damit es passt? Was ist daran ein Befund und nicht die Definition von RTT?"
- *Fix/Verteidigung:* **Contribution umrahmen.** C1 NICHT als "fast perfekte Entdeckung" verkaufen, sondern als (a) **Methoden-Validierung** ("Layer-1-Ping genügt, um die connect-Latenz-Klasse ohne API-Kosten vorherzusagen") und (b) physikalisch motivierte Strukturhypothese, **gestützt durch die unabhängige PCAP-Submetrik-Zerlegung** (TCP/TLS/proto je 1 RTT zählbar), NICHT durch r. n=4 offen als Limitation benennen. Headline-Zahl auf 1.006/10.7 korrigieren, Rev.ai-Mischung raus. r=0.999 aus Plot-Titeln streichen.

**A2 — 0 % Fließtext + Limitations-Liste verschweigt die 3 härtesten Löcher**
- *Problem:* Komplette Thesis ungeschrieben. Die einzige Limitations-Notiz (`thesis_outline.md:64`) nennt Cold-Start, 7 Tage, Anycast — verschweigt aber: (1) E2E nie gemessen (reine Median-Addition), (2) C1 n=4, (3) connect_ms-Asymmetrie.
- *Beleg:* `find` über `.tex`/Kapitel-Markdown = 0 Treffer; grep über `notes/` nach "median-addition|n=4|konfidenz" = 0.
- *Prof-Frage:* „Wo ist der Text? Und warum fehlen in Ihren Limitationen genau die offensichtlichsten Schwächen?"
- *Fix:* Methodik-Kapitel ZUERST schreiben; Limitations-Abschnitt mit den 3 Löchern aktiv eröffnen, bevor der Prof sie findet.

**A3 — connect_ms ist kategorienübergreifend NICHT dieselbe Messgröße (E1, confirmed 3/3)**
- *Problem:* STT misst connect_ms am realen In-Pfad-WebSocket (ttft connect-EXKLUSIV); LLM/TTS messen connect_ms an einem sofort geschlossenen Wegwerf-Socket, der echte Request läuft über eine 2. httpx-Verbindung (ttft/ttfa connect-INKLUSIV). Empirisch belegt: openai connect=9,4 ms, aber corr(connect,ttft)≈0 und corr(headers,ttft)≈1 → die 9 ms liegen NICHT im Latenzpfad. Jede Provider-Matrix, die connect_ms quer stellt, vergleicht Äpfel mit Birnen.
- *Beleg:* `llm_openai.py:24-33` (_measure_connect + writer.close()), `:92` (ttft über 2. Verbindung) vs `stt_deepgram.py:99`.
- *Prof-Frage:* „connect_ms — misst das bei STT, LLM und TTS dasselbe? Wo beginnt und endet die Uhr, und liegt der Connect überhaupt im Pfad des Requests?"
- *Fix:* Methodik-Tabelle mit expliziter Asymmetrie (STT=In-Pfad/connect-exklusiv, LLM/TTS=Wegwerf-Connect+connect-inklusive ttft). Durchgängig "user-perceived Cold-Start" verwenden: STT = connect+ttft, LLM/TTS = ttft/ttfa. Niemals rohes connect_ms cross-Kategorie nebeneinanderstellen.

### 🟠 HOCH

**A4 — STT misst KEINE First-Token-Streaming-Latenz, sondern Full-Utterance-Batch (Blindspot, NEU)**
- *Problem:* Das gesamte 4,84 s-Audio wird als Dump in send_ms ≈ 137 ms (Deepgram) / 142 ms (Rev.ai) / 12 ms (Azure) gesendet — kein Real-Time-Pacing. Der Server hat die GANZE Äußerung, bevor er transkribiert. In einer echten Voice-Pipeline trifft Audio über ~5 s inkrementell ein und STT läuft *parallel zum Sprechen*; der reale STT-Beitrag zur E2E wäre nur das Post-Sprechende-Processing — **drastisch kleiner**. Damit ist C5 ("STT dominiert 67 %, 0/27 unter 1 s") potenziell ein Methodik-Artefakt. AssemblyAI wurde laut CLAUDE.md *genau wegen* Real-Time-Pacing verworfen — die realistischere Methode wurde bewusst aufgegeben.
- *Beleg:* `layer3_stt.parquet` send_ms-Mediane; CLAUDE.md Provider-Matrix-Notiz zu AssemblyAI.
- *Prof-Frage:* „Ihr STT bekommt die komplette Äußerung als Dump in 137 ms. Messen Sie dann Streaming-First-Token oder Batch-Transkription der ganzen Datei? Was bleibt vom 67-%-STT-Anteil, wenn STT real-time parallel zum Sprechen liefe?"
- *Fix:* In der Methodik offen deklarieren, dass STT als Batch-Dump gemessen wurde. **Sensitivitätsrechnung**: wie ändert sich E2E, wenn STT real-time-gepact (= parallel) liefe? Das ist die entscheidende Robustheitsprüfung für C5 und muss vor dem Schreiben geklärt sein.

**A5 — 1-Sekunden-Budget willkürlich, widerspricht der eigenen Literatur (Blindspot, NEU)**
- *Problem:* Die ganze E2E-Story misst gegen 1000 ms. Die einzige zitierte Konversations-Schwellenquelle (Jacoby, arXiv 2404.16053, `literature.md:48`) nennt **200–300 ms**. Die 1000 ms sind nirgends hergeleitet. Bei 300 ms wären 0/27 trivial und auch Warm (666 ms) verfehlt es.
- *Beleg:* `literature.md:48` vs `07_e2e_pipeline.ipynb` Budget-Plot.
- *Prof-Frage:* „Warum 1 Sekunde? Ihre eigene Referenz sagt 300 ms."
- *Fix:* 1000 ms durch zitierbare Voice-Agent-Literatur stützen ODER Diskrepanz zu Jacobys 300 ms explizit in der Diskussion auflösen (z. B. 1 s = tolerierbare Obergrenze für Assistenten vs 300 ms für natürlichen Turn-Taking-Dialog).

**A6 — E2E ist reine Median-Addition, kein echter Run, kein CI (C5/E3, confirmed + Statistik-Finding)**
- *Problem:* `stream_e2e = stt_connect + stt_ttft + llm_ttft + tts_ttfa` — drei Mediane addiert. Mediane sind nicht additiv. Nur Punktschätzer, keine CI/IQR. Code für echte Pipeline existiert nicht (run.py kennt kein `e2e`, chain.py fehlt). Außerdem: ~76 % der Pipelines lägen real >1000 ms (Monte-Carlo) — "0/27 unter 1 s" gilt nur für MEDIAN-Kombis, nicht für jeden Einzel-Run.
- *Beleg:* `07_e2e_pipeline.ipynb` CELL[4]; `run.py:241-242` (choices ohne e2e).
- *Prof-Frage:* „Haben Sie die Pipeline je als Ganzes gemessen, oder addieren Sie drei Mediane? Wo ist das Konfidenzintervall der 1134 ms?"
- *Fix:* Monte-Carlo-Faltung der empirischen Verteilungen (5 Zeilen, kein neues Geld) → liefert median-of-sum + p90/p95. Belegt sogar, dass Sum-of-Medians konservativ ist (Abweichung <1 %). Median-Addition als bewusste, benannte Limitation. Ein einziger echter E2E-Lauf (n=20) auf EC2 würde 1134 ms massiv absichern.

**A7 — STT total_ms cross-Provider unbrauchbar, verseucht alle Batch-E2E-Zahlen (E4, confirmed 3/3)**
- *Problem:* Deepgrams `_recv_finals` bricht NICHT beim ersten Final ab, sondern liest bis WS-Close (~3374 ms Leerlauf-Tail). Azure/Rev.ai returnen beim ersten Final. Median total_ms: Deepgram 4350 / Azure 1769 / Rev.ai 2117. Die "Streaming spart 3350 ms"-Aussage IST der Deepgram-Tail (Batch−Stream-Delta = exakt 3351 ms bei Deepgram, 4 ms bei Azure) — ein Schleifen-Artefakt, kein echter Batch-vs-Streaming-Effekt. send_ms ist nur 137 ms, die Tail-Begründung "Audio-Transfer ~4 s" im NB07 ist falsch.
- *Beleg:* `stt_deepgram.py:74-90` (kein return) vs `stt_azure.py:128`/`stt_revai.py:77` (return); `07_pipeline_combinations.csv` (deepgram batch 4485).
- *Prof-Frage:* „Deepgram total_ms ist 4,3 s bei ttft 0,6 s — was passiert in den 3,7 s, und warum hat Azure die Lücke nicht? Ist Ihr Batch-Szenario ein Provider-Vergleich oder ein Schleifen-Artefakt?"
- *Fix:* total_ms NUR provider-intern interpretieren. Batch-Szenario entweder Deepgram-Tail bereinigen oder **ganz streichen** und nur Streaming-E2E berichten (das ist ohnehin die realistische Voice-Pipeline). In der Auswertung behebbar, kein Neumessen.
- ✅ **ERLEDIGT (2026-06-09): Batch-Szenario gestrichen.** NB07 entfernt `batch_e2e`/`stt_total_ms` aus Combos, CSV, Stacked-Bar, Budget; `07_e2e_stream_vs_batch`-Figure gelöscht; Methodik-Hinweis im Notebook-Intro + `known_anomalies.md §5.1` + `findings.md F10`. Nur noch Streaming-E2E (0/27 < 1 s, beste Kombi 1134 ms).

**A8 — Verfügbarkeit ignoriert: "beste" Pipeline nutzt Groq mit 33 % Ausfall (Statistik-Finding)**
- *Problem:* Alle Mediane nur über Erfolge. Groq-Bestmarke (68 ms) beruht auf 3755/5600 Versuchen (32,9 % Fehler, alle HTTP 429). Die "beste E2E-Kombi" deepgram+groq+azure kommt real nur in ~67 % der Fälle zustande. Groq-Erfolge clustern zudem am Slot-Anfang (Survivorship: Erfolg-Run-Median 38 vs Fehler 64).
- *Beleg:* `layer3_errors.parquet` (groq 1845 LLM-Fehler); `07_pipeline_combinations.csv` ohne Verfügbarkeits-Spalte.
- *Prof-Frage:* „Ihre beste Pipeline nutzt Groq, das ein Drittel der Anfragen ablehnt. Ist eine 1134-ms-Pipeline, die nur in 67 % der Fälle durchläuft, wirklich die beste?"
- *Fix:* Verfügbarkeits-Spalte neben jeden Latenz-Median. Joint completion probability in der E2E-Tabelle. Erklären, dass Groq-429 ein Free-Tier-Quota-Problem ist (konstant 67/Slot), kein Latenzproblem. Mistral (4 % Fehler) als robustere Alternative anbieten.

**A9 — Layer-2 als "unabhängige Validierung" ist brüchig (E-Findings, high)**
- *Problem:* PCAPs vom 8.6., **andere Instanz/AWS-Account**, ~19 h nach Kampagnenende, n=1/Provider. Für LLM/TTS keyt der Analyzer auf das Wegwerf-SYN → rtts_to_ready=180 (unsinnig). Rev.ai-Capture (einziger TLS-1.2-Provider!) kaputt. NB02 nutzt scapy, dokumentiert aber tshark (`_pcap_helpers.py:25` Windows-hardcoded Pfad, toter Code).
- *Beleg:* `PROVENANCE.md:6-11`; `analysis_summary.json` (rtts_to_ready); `_pcap_helpers.py:25`.
- *Prof-Frage:* „Ihre PCAP-Validierung stammt von anderem Tag/Instanz — was validiert sie konkret, und warum ist der einzige TLS-1.2-Provider kaputt aufgenommen?"
- *Fix:* Layer 2 NUR für **Protokoll-STRUKTUR** beanspruchen (TLS-Version, Fronting, RTT-Anzahl, STT-Submetrik) — vantage-unabhängig, hält. NICHT für Absolutzeiten. Die stärkere Validierung ist `validation_2026-06-08` (191 Runs, reproduziert RTT-Klassen) — die hervorheben. NB02-Markdown auf scapy korrigieren.

### 🟡 MITTEL

**A10 — LLM-Output-Degeneration nicht geprüft (Blindspot, NEU):** Mistral hat 21 Erfolge mit token_count=None, 17 mit =1, 34 mit =2 → 72 quasi-leere "Erfolge" in den Mistral-Medianen (Median nur 3 Tokens vs OpenAI/Groq 7). STT/TTS-Degeneration wurde geprüft, LLM nicht. *Fix:* Mistral-Mediane neu über token_count≥3 rechnen, prüfen ob ttft=230 ms stabil bleibt.

**A11 — token_count zählt SSE-Chunks, nicht Tokens (`llm_openai.py:81`):** Die gen_ms/13×-Story und jeder Tokens/s-Vergleich beruhen auf Chunks≠Tokens (provider-spezifisches Chunking). *Fix:* Als "Chunk-Generierungsrate" formulieren oder gegen API-usage-Felder kalibrieren.

**A12 — Timestamp-Spillover: Phantom-57.-Slot (Datenintegrität):** Azure-TTS-21h-Slot vom 7.6. ist nach 22:00 getimestamped → `groupby(['date','hour'])` zählt 57 statt 56. NB00 CELL[9] zeigt selbst "openai count=57, min=2" — sieht wie gescheiterter Slot aus. *Fix:* nach `tag` statt Timestamp-Stunde gruppieren; eine Zeile in known_anomalies.md.

**A13 — TTS-E2E endet bei ttfa, ignoriert Playback (Blindspot):** Der Nutzer hört die vollständige Antwort erst nach Audio-Generierung+Playback. ttfa=66 ms ist nur der Start. *Fix:* E2E-Endpunkt begründen; Sensitivität mit tts_total rechnen.

**A14 — Keine STT-Inhaltskorrektheit/WER (Blindspot):** transcript_len>0 wurde als "gültig" genommen, aber nie auf Wort-Korrektheit geprüft. Deepgram liefert tl bis 86 (Halluzination?) und 2× tl=12 (abgeschnitten) bei ttft ~18,6 s. Ein "schnelles falsches Transkript" zählt als Erfolg. *Fix:* WER aus Raw-transcript-Strings gegen Referenz rechnen.

---

## 5. Widersprüche (vor dem nächsten Prof-Termin bereinigen)

Diese internen Zahlen-Inkonsistenzen erzeugen bei jeder Gegenprüfung sofort einen Treffer. **Maßgeblich ist immer der Juni-Wert (Notebook/Tabelle/Parquet); Mai-Werte in CLAUDE/README sind falsch.**

| # | Behauptung (stale) | Korrekt (Juni) | Wo der Fehler lebt |
|---|---|---|---|
| W1 | C1 slope=1.013 / k=8.5 / r=0.9992 | **1.006 / 10.7 / 0.99932** | HANDOFF, CLAUDE, README |
| W2 | TLS-1.2-Penalty +142 ms | **+153 ms** (NB06/01) — oder +142/+144 je Definition | HANDOFF, README; intern 3 Werte (140/142/153)! |
| W3 | E2E beste 1157 ms | **1134 ms** (gesamte Top-5 ~20 ms zu hoch) | README |
| W4 | Warm 676 ms | **666 ms** | README |
| W5 | Groq-Error 35 % / 34,97 % | **32,9 %** | HANDOFF, README |
| W6 | "Groq 13× schneller" (ttft) | **ttft 7,9× / 3,4×**; 13× gilt nur für gen_ms | HANDOFF, CLAUDE |
| W7 | STT-ttft 587/1719, connect 437/48 | **574,6/1715,2; 424,9/49,5** | README, CLAUDE |
| W8 | TTS ttfa 65/551/938 | **66,6/556,5/954,2** | README |
| W9 | CLAUDE connect-Submetrik Deepgram 337 / Azure 265 ms | **424,9 / 49,5 ms** (Azure 265 war NIE korrekt) | CLAUDE.md Submetrik-Tabelle |
| W10 | "14 Tage" Kampagne | **7 Tage** | `07_e2e_pipeline.ipynb:528` (in einer FIGURE!), cost_analysis.md, literature.md |
| W11 | DNSSEC 0/7 vs 0/6 | **0 von 6 distinkten Zonen (7 Endpoints, microsoft.com doppelt)** | known_anomalies.md vs NB01 |
| W12 | Deepgram AS12129 | Transit-AS 174/6461 (PCAP) vs DNS-Host-AS — **sauber trennen** | HANDOFF, README |
| W13 | Mistral-Modell "mistral-small-4" | Code: **mistral-small-2603** | CLAUDE.md vs `llm_mistral.py:19` |

**Besonders heikel:** W10 steckt in einem Figure-Untertitel (`07_e2e_pipeline.ipynb:528`), der in die Thesis wandern könnte. W2 ist dreifach widersprüchlich in *einer* Arbeit.

**Tote/kaputte Artefakt-Stolperfallen:** `data/processed/layer1_tls.csv` ist komplett leer (Bug `process_raw_data.py:210-216`) — entfernen oder klar auf `layer1_extra/tls.csv` verweisen. `_pcap_helpers.py` tshark-Pfad Windows-hardcoded, faktisch ungenutzt. 3 referenzierte Plan-Dateien (`implementation_plan.md`, `analysis_plan.md`, `briefing_prof.md`) fehlen.

---

## 6. Lücken & blinde Flecken

Was zur fertigen Thesis fehlt bzw. der Audit selbst übersah (Vollständigkeits-Kritiker):

- **Schreibstand:** 0 % Prosa — alle 7 Kapitel. Methodik (Prof-Kritikpunkt) + Diskussion/Limitations tragen die Verteidigung.
- **STT-Real-Time-Pacing-Frage (A4):** der härteste ungeprüfte Validitäts-Einwand. Nirgends diskutiert.
- **1-s-Schwelle-Herleitung (A5):** zentrale E2E-Aussage hängt an unbelegter Schwelle.
- **arXiv-2603-IDs:** Kern-Referenz `2603.11006` (GESAMTE Submetrik-Zerlegung) + `2603.05413` haben Zukunfts-IDs (März 2026, nach Cutoff). **Vor Zitation per Web verifizieren** — bei Nicht-Existenz ist die Methoden-Fundierung zitationslos.
- **Related Work:** existiert nur als Linkliste, keine Synthese, keine Abgrenzung. Risiko "na und, das macht Artificial Analysis täglich" (C4 ist Benchmark-Replikation) — Abgrenzungs-Delta (EU-Vantage + Cold-Start + Cross-Layer + Pipeline-Budget) muss aktiv formuliert werden.
- **Statistische Absicherung:** Keine CIs/IQR in den Headlines, obwohl die CSVs p90/p99/std enthalten. Besonders bei Deepgram (CV 87 %, max-ttft 18,7 s) und Mistral (std 1708 ms, p99=30×p50).
- **Generalisierbarkeit:** Azure ist der EINZIGE EU-STT — "Engine>Region" (C3) ruht auf n=1 EU-Provider pro Kategorie. Als Limitation benennen.
- **WER/Inhaltskorrektheit (A14), LLM-Degeneration (A10), TTS-Playback (A13)** — alle ungeprüft.
- **E2E-STT-Term-Komposition:** ausweisen, woraus der "67 % STT-Anteil" besteht (connect+ttft inkl. Dump-Effekt).

---

## 7. Priorisiertes To-Do

### VOR dem nächsten Prof-Termin (Zahlen + Framing — billig, hoher Hebel)

1. **Alle Mai-Zahlen auf Juni synchronisieren** (W1–W13). Eine einzige Wahrheitsquelle (Notebook/Tabellen). Besonders Figure-Untertitel `07_e2e_pipeline.ipynb:528` ("14 Tage").
2. **Contribution neu sortieren:** (1) Engine>Region (C2/C3, *deine stärkste, kontraintuitive Karte*), (2) 1-s-Budget-Zerlegung der Cold-Start-Pipeline, (3) Cloudflare-Fronting quantifiziert. C1 wird **Methoden-Baustein**, nicht Kernbefund.
3. **C1 ehrlich neu framen:** n=4 als Limitation, r weglassen/abschwächen, durch PCAP-Submetrik stützen. Headline-Zahl korrigieren.
4. **3 harte Limitationen formulieren:** E2E nie gemessen (Median-Addition), C1 n=4, connect_ms-Asymmetrie. Offensiv = entwaffnend.
5. **arXiv 2603.11006 + 2603.05413 web-verifizieren** (WebSearch/WebFetch). Bei Nicht-Existenz Ersatz finden.
6. **1-s-Schwelle herleiten/belegen** und Diskrepanz zu Jacobys 300 ms auflösen.
7. **Prof-Antworten üben:** "Was wird gemessen / warum Cold-Start / Contribution" (s. Checkliste §8).

### Für die fertige Thesis (mehr Arbeit)

8. **Methodik-Kapitel zuerst schreiben** — inkl. connect_ms-Asymmetrie-Tabelle, STT-Dump-Deklaration (A4), Metrik-Definitionen.
9. **Monte-Carlo-E2E** (A6): median-of-sum + p90/p95 mit CI aus den Parquets (read-only, 5 Zeilen).
10. **STT-Real-Time-Sensitivität** (A4): Gedankenrechnung "STT parallel zum Sprechen" → wie kippt der 67-%-Anteil?
11. **Verfügbarkeits-Dimension** (A8) in E2E-Tabelle; ~~Batch-Szenario streichen (A7)~~ ✅ erledigt 2026-06-09.
12. **WER/Inhaltskorrektheit** (A14) + Mistral-Degeneration-Recheck (A10) + token_count-Klarstellung (A11).
13. **Statistik:** IQR/p90 in alle Vergleichsaussagen; Mann-Whitney/Bootstrap-CI für die 3 Kernvergleiche.
14. **Related Work** zu echtem Fließtext mit Abgrenzungsabsatz; **Diskussion/Limitations**; dann Einleitung/Grundlagen/Fazit.

---

## 8. Verständnis-Checkliste (musst du SELBST erklären können)

1. **Warum Cold-Start statt Warm?** — *Kommt dran:* Prof-Hauptfrage. Cold-Start = Overhead jeder neuen Gesprächssession (Serverless, nach Inaktivität); per Run-Index-Flachheit empirisch als echt belegt. *Wo:* CLAUDE.md, NB03 §4, connect_ms-Quartile.
2. **connect_ms-Zerlegung (tcp_hs/tls_hs/proto_setup) + warum es bei STT vs LLM/TTS verschiedenes misst.** — *Kommt dran:* "Was genau messen Sie?" Die Asymmetrie (In-Pfad vs Wegwerf-Socket, connect-exklusiv vs -inklusiv) ist der gefährlichste Methodik-Punkt. *Wo:* CLAUDE.md Metrik-Tabelle, `stt_deepgram.py:99` vs `llm_openai.py:24-92`.
3. **Warum Engine > Netzwerknähe (Azure EU langsamer als Deepgram USA)?** — *Kommt dran:* Dein stärkster, kontraintuitiver Befund = die eigentliche Contribution. Azure spart 130 ms Netz, verliert 1130 ms Engine. *Wo:* NB03, `03_stt_statistics.csv`.
4. **Warum bricht das Cross-Layer-Modell bei Cloudflare-Providern?** — *Kommt dran:* erklärt die Grenze des Modells. Edge-RTT ~1 ms, Backend nicht messbar → eff_N 7–180. *Wo:* NB06, NB02 §7.1.
5. **TLS-RTT-Zählung: warum WS-TLS1.3=3, HTTPS=2, TLS1.2=4 RTTs?** — *Kommt dran:* N_RTTs-Zuweisung ist der Angriffspunkt von C1 (rückwärts gefittet?). Du musst N aus dem Protokoll/PCAP begründen, nicht aus dem Fit. *Wo:* NB06 PROVIDER_META, PCAP-Submetrik.
6. **Aussagekraft von r=0.999 bei n=4.** — *Kommt dran:* Prof rechnet das in 2 Min nach. Hohes r bei 2 Clustern ist erzwungen; argumentiere mit Residualfehler <21 ms, nicht mit r. *Wo:* `06_cross_layer_master.csv`, A1.
7. **Warum ist die E2E-Zahl (1134 ms) eine Median-Addition und keine echte Messung — und was das limitiert.** — *Kommt dran:* "Validierung?" Mediane nicht additiv, kein CI, Connect-Semantik gemischt. *Wo:* `07_e2e_pipeline.ipynb` CELL[4], run.py (kein e2e).
8. **TLS-1.2-Penalty: wie kommt +153 ms zustande und warum 1 extra RTT?** — *Kommt dran:* Penalty ist dreifach widersprüchlich dokumentiert (140/142/153). Du brauchst EINE Definition: reine TLS-RTT-Differenz aus PCAP = ~143 ms; connect_ms-Counterfactual = 153 ms. *Wo:* NB06 CELL[7], NB01 §7.3.
9. **Warum wird STT als Audio-Dump (kein Real-Time-Pacing) gemessen — und was das für die E2E-Validität heißt?** — *Kommt dran:* härtester ungeprüfter Einwand; AssemblyAI flog genau deswegen raus. *Wo:* send_ms in `layer3_stt.parquet`, CLAUDE.md.
10. **Warum 1000 ms als Budget, wenn die Literatur 300 ms sagt?** — *Kommt dran:* die ganze praktische Relevanz hängt an der Schwelle. *Wo:* `literature.md:48` (Jacoby) vs E2E-Budget-Plot.
11. **Warum ist "0 % NaN" / n=100 ein Qualitätsnachweis — und was es NICHT bedeutet (keine 100 % Erfolge; Errors separat ausgelagert)?** — *Kommt dran:* "0 % NaN" ist tautologisch (Fehler vorher entfernt); n=100 ist Versuchszahl, nicht nutzbares n (Groq 67, Rev.ai 0 in 5 Slots). *Wo:* NB00, `known_anomalies.md`, `layer3_errors.parquet`.
12. **Forschungsfrage: warum ist "Region erklärt Latenz" kausal nicht beantwortbar (Konfundierung)?** — *Kommt dran:* RQ-Validität (E2, confirmed). Region/Engine/Protokoll pro Provider perfekt konfundiert; ehrliche Antwort = Engine dominiert, Netzwerk erklärt's gerade NICHT. Das ist der Beitrag, kein Fehler. *Wo:* `thesis_outline.md` RQ, `findings.md:42`.

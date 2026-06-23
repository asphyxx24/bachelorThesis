# Lernplan — Referenz / Antwortschlüssel (pro Modul)

> **Nutzung:** Das ist **nicht** zum Vorab-Lesen. Zu jedem Modul aus `lernplan.md` gehst du erst selbst durch
> (mit mir per `/explain`), versuchst die Erklär-Fragen **in eigenen Worten** zu beantworten — und **erst danach**
> schlägst du hier nach, um zu prüfen/ergänzen. So bleibt es aktives Lernen. Zahlen sind faktengeprüft
> (56 von 56 Slots, A4, success-only; Bootstrap-CI noch ausstehend). Quellen stehen im Gerüst.

---

## Gesamt — Die Arbeit in einem Satz
> „Ich messe von einem festen Punkt in Frankfurt aus die Cold-Start-Latenz von 9 kommerziellen Cloud-AI-APIs
> (STT, LLM, TTS) in drei sauber getrennten Schichten — Netz-Infrastruktur, Paketebene, API-Latenz — und zeige:
> Drei LLMs hängen am **selben** Cloudflare-Edge in Frankfurt (~1 ms), antworten aber bis zu **~7,3× (gepoolt 8,3×)
> unterschiedlich schnell. Also kann die Netznähe die Spreizung nicht erklären** — sie entsteht im Backend der Anbieter."

---

## M1 — Vertrauensproblem & Neuanfang
- Prof: „Im Kern reicht das", **aber „ich vertraue den Daten nicht"** — **kein** „Zahlen falsch", sondern
  Methodik/Setup/Struktur **nicht dargelegt** (kein reproduzierbares Verfahren; 3 Anbieter mit ~1 ms unerklärt).
- Reaktion: bewusster Neuanfang für interne Stringenz. Leitprinzip: **erst Methodik schriftlich, dann Code, dann
  messen.** Behalten wurde nur das *Wissen* (Reframe, Contribution, 3-Layer-Idee), nicht die alten Rohdaten.

## M2 — Forschungsfrage
- Wortlaut: *In welchem Maße erklären Netzwerk-/Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region) —
  verglichen mit der Backend-Verarbeitung — die Latenzunterschiede zwischen kommerziellen Cloud-AI-APIs aus
  EU-Sicht, und wie wirkt die Provider-Wahl auf die Cold-Start-Gesamtlatenz einer sequenziellen Voice-Pipeline?*
- **Beidseitig beantwortbar:** „Netzwerk erklärt *weniger* als das Backend" ist gültig/erwartet. Vergleicht *Anteile*.

## M3 — C1 „Backend statt Geografie" + schärfster Beleg
- **Wasserdichte Aussage ist NEGATIV:** „Netznähe erklärt die Spreizung **nicht**." (Nicht „Engines immer schneller".)
- LLM @ identischem Edge: OpenAI/Groq/Mistral terminieren **alle** bei Cloudflare FRA (AS13335, ~1 ms), 100 % Traffic
  gemessen + ASN-belegt. `ttft` (56 von 56 Slots, A4): **Groq 66,9 / Mistral 278,9 / OpenAI 486,6 ms** → openai/groq = **~7,3×** (gepoolt 8,3×).
  **Geografie invertiert:** EU-Mistral langsamer als US-Groq.
- TTS-Zweitbeleg: OpenAI-TTS **auch** bei CF-FRA (gleiche IPs, connect ~1 ms) → `ttfa` ~942 ms = reines Backend. Azure schnellstes
  TTS (`ttfa` ~94 ms); „trotz US-Konkurrenz" sauber nur ggü. Deepgram (~280 ms connect, echter US-Transit).
- STT **kein** C1-Beleg: auf `ttfp` ist Azure nicht langsamster; alte „1722-ms-Endpointing"-These = Dump-Artefakt, gestrichen.
- **Confound:** Groq = kleinstes Modell **und** spezielle HW (LPU) zugleich → „Backend (HW+Modell) statt Geografie",
  nie „Rechenleistung allein". Darum „Engine" **nicht im Titel**.
- **H1-Stolperstein:** 75/268/476 ms = Predeploy-Pilot, nicht reproduzierbar → Kampagnenzahlen führen.

## M4 — C2 & C3
- **C2:** 3-Schichten-Zerlegung macht Aussagen reproduzierbar + löst „3 Anbieter ~1 ms" über Edge/Host-Grenze;
  Layer 2 validiert Layer 3 (paket-geeichter Connect-Timer).
- **C3:** ping-basierte Connect-Klassen-Heuristik — **bewusst nicht** als Gütemaß (`r` kein Qualitätsmaß; n klein).

## M5 — Setup, Cold-Start, Kampagne
- EC2 `c6i.large` (nicht burstable → keine CPU-Credit-Drosselung), Frankfurt, OpenSSL 3.x, UTC, chrony.
- Cold-Start, kein Pooling: jede Messung neue TCP+TLS → „erste-Eindruck"-Latenz; Verbindungsaufbau zum Backend
  = interessanter Anteil aus EU-Sicht.
- Kampagne: 7×8 Slots × n=100, interleaved = 56 Slots = 5.600/Endpunkt = 50.400 Calls. Vollkampagne, abgeschlossen (56/56) (A4).
- `run_meta` je Slot: git-Commit (+dirty), Lockfile-Hash, instance_id, cpu_steal (keine Drosselung), OpenSSL, chrony.
  Code eingefroren `f9e6dc8`.

## M6 — Layer 1 (RTT, Edge vs. Host)
- **TCP-Ping primär** (Port 443), nicht ICMP (oft geblockt); N=20, Minimum + Median. ICMP nur Validierung.
- **Edge nur wenn ALLE 3:** (a) RTT ≈ 1–2 ms, (b) IP in CDN-ASN (AS13335), (c) Traceroute endet im CDN-AS. Sonst Host.
- 3 Klassen (EC2 16.6.): Edge ~1 ms (OpenAI/Groq/Mistral/OpenAI-TTS, AS13335) · EU-RZ ~11 ms (Azure, AS8075,
  Italy North, **kein** CDN) · US-Backend ~140 ms (Deepgram: Zayo AS6461 ×3 + Cogent AS174 ×3; Rev.ai: AWS AS16509 ×3).
- Niedrige RTT ≠ Edge (Azure 11 ms = Host); „Anycast"-Label ≠ Edge (Deepgram misst ~140 ms = Host). **Messung > Marketing.**
- **H4/A1:** `data/layer1/` = macOS-Dev-Lauf (~17–21 ms) → nur EC2-L1; macOS-LibreSSL kappt TLS auf 1.2 → TLS nur von EC2.

## M7 — Layer 2 (Paket-Eichung)
- Experiment: N≈30 Cold-Start-Connects parallel mit tcpdump; App-`tcp_handshake_ms` vs. Wire-SYN→SYN-ACK, Paarung über Quell-Port.
- Ergebnis: **~0,1 ms** Übereinstimmung (Azure +0,11 ms @ 11 ms; Deepgram ~+0,1 ms @ 139 ms) → Connect-Timer paket-validiert (C2).
- **H2-Reichweite:** nur Connect-Timer geeicht. `ttft/ttfa/ttfp` = derselbe `perf_counter`, aber ab Request-Absenden im
  httpx/websockets-Stack → **nicht direkt** geeicht. Nie „alle L3-Zahlen paket-validiert".

## M8 — Layer 3 & Metrik-Asymmetrie
- Connect-Submetriken (Wegwerf-Socket): dns/tcp/tls (+ws bei STT). „connect total" = abgeleitete Summe.
- Asymmetrie: STT-Uhr ab **erstem Audio-Chunk** (connect-**exklusiv**), Primär `ttfp`. LLM/TTS ab Request-Absenden
  (connect-**inklusiv**), Primär `ttft`/`ttfa`. Grund: STT misst nutzer-wahrgenommene Zeit ab Audio-Senden.
- E2E **nicht naiv addieren** (sonst connect doppelt): `connect + stt_ttft + llm_ttft + tts_ttfa`.

## M9 — STT `ttfp` + 1×-Pacing
- `ttft` (Final) vermischt Engine-Speed + **Endpointing-Policy** (verschieden je Anbieter) → unfair. (Azure-1722-ms = Dump-Artefakt.)
- Lösung: Primär `ttfp` (erstes Interim-Wort, vor Finalisierung). Audio **1×-realtime gepact** (4096 B / ~0,128 s) +
  **paralleler Empfang** (`asyncio.gather`) — sonst kein Interim.
- Gepact: Azure ~1045 ≈ Deepgram ~1045 ms (**gleichauf**), Rev.ai ~1494 ms höher → Azure nicht langsamster. `ttft` bleibt sekundär (ehrlich „inkl. Endpointing").
- 3 Grenzen: ~0,8 s Pacing-Floor (nur Deltas = Signal); kaum geografie-sensitiv; Emissions-Kadenz teils Policy.

## M10 — Code-Architektur & Timing
- Struktur: layer1 (hosts.py + Diagnose), layer2 (capture+analyze), layer3 (config=SSOT, connect, llm/tts/stt, run=Orchestrator).
- Timing: `time.perf_counter()`, ms gerundet. Cold-Start: frischer httpx.Client / WebSocket je Call. **IPv4 erzwungen**
  (`local_address="0.0.0.0"` / `AF_INET`), sonst IPv6 → Layer-Brücke bräche.
- Libs: httpx (HTTP/2 + SSE), websockets (raw, ohne SDK), ssl/socket (Submetriken), tcpdump (Eichung), asyncio (STT parallel).
- run.py: flock-Lock, interleaved Round-Robin mit Rotation (`shift = rnd % len(eps)`), per-Call Hard-Timeout (Thread 75 s),
  Slot-Deadline, SIGTERM-sauber, JSONL: run_meta → Calls → run_end.
- Erfolg = inhaltlich (LLM ≥3 Zeichen; Mistral 1 Chunk ≠ Fehler; TTS ≥1000 B; STT nicht-leer). Fehler = Roh-String (kein Enum, H3).

## M11 — Provider-Matrix & „warum US"
- Pipeline Audio→STT→Text→LLM→Antwort→TTS→Audio; 3/Kategorie = 9. Je Kategorie EU-naher Kontrast (Azure; Mistral) vs. US.
- **Warum überwiegend US (= Befund, kein Bias):** keine kommerziellen, ausgereiften, *streamenden* EU-STT/TTS dieser
  Qualität → EU-Teams **müssen** US-Engines nutzen → als Limitation + Befund genannt.
- Modell-Pinning wo möglich (`gpt-4o-mini-2024-07-18`, `llama-3.1-8b-instant`, `mistral-small-2603`); `effective_model` geloggt (Drift).

## M12 — Datenartefakte & echte Ergebnisse
- Maßgeblich: `data/audit_20260618/ec2_data/` (56 von 56 Slots, A4). Belege: `l1_rtt_per_ip.md`, `asn_per_ip.md`.
- Kernzahlen: LLM-`ttft` 66,9/278,9/486,6 (~7,3×, gepoolt 8,3×); Edge ~1 ms; L2 ±0,1 ms; Azure-TTS ~94 ms; OpenAI-TTS ~942 ms (connect ~1 ms); STT-`ttfp` ~1045/1045/1494 ms.
- Final: 56-Slot-A4 + EC2-L1 + L2-PCAP = belastbar (Bootstrap-CI noch ausstehend). Pilot & macOS-L1 = nicht verwenden. Diurnal = unbestätigt.

## M13 — Aggregation A4 & Verfügbarkeit
- A4: je (Endpunkt, Slot) Median → **Headline = Median der Slot-Mediane** + gepoolt als Gegenprobe + Bootstrap-95%-CI.
  ⚠ Interim noch strittig (Slot-Bootstrap n=8 „lumpy" → pooled gegenprüfen).
- Perzentile: p50/p90 slot-auflösbar; p95/p99 nur volle Kampagne (n·(1−q) ≥ 5–10).
- Verfügbarkeit = eigene Achse: Latenz nur success-only, Verfügbarkeit separat, Pareto (Latenz vs. Verfügbarkeit). OpenAI-TTS „schnell" aber 3,1 % (173/5600) Fails.

## M14 — HIGH-Auflagen H1–H4
- H1: 75/268/476 = Pilot, nicht reproduzierbar → 66,9/278,9/486,6 (56-Slot-A4). Selbstkorrektur = Vertrauens-Plus.
- H2: nur Connect-Timer geeicht (s. M7).
- H3: kein `error_kind`-Enum; `error=='timeout'` verfehlt 158/161 → Roh-String per Teilstring bucketieren (`ReadTimeout`=tts_openai, `http_503`, `timeout`).
- H4: `data/layer1/` = macOS → nur EC2-L1 / `l1_rtt_per_ip.md`.

## M15 — MEDIUM-Punkte & Confounds (Auswahl)
- M1: sequenzielles E2E braucht `stt_ttft`; `ttfp`-Summe unterschätzt STT ~3,7–3,9 s.
- M2: OpenAI-TTS @ Cloudflare = zweite identical-edge-Instanz (stützt C1); „US-Konkurrenz" nur ggü. Deepgram.
- M3: „~1 ms am Edge" schließt CF→Origin-Backhaul nicht *automatisch* aus; mit Daten widerlegbar (groq/openai teilen
  CF-FRA→US, differieren ~370 ms) → „nicht in der EU-Edge-Nähe".
- M4: rev.ai TLS 1.2 = ganze Extra-RTT (~143 ms) = Protokoll, nicht Geografie.
- M6: Round-0-Cold-Start verzerrt Tails (Median immun) → r0 als Warm-up.
- M9/M10: Deepgram-`ttfp`-Tageskurve = Input-Text-Artefakt (corr 0,915); OpenAI-TTS-Fail real **3,1 % (173/5600)** (nicht 8 %, nicht 10,4 %), Diurnal unbestätigt (~1,5 Tage/Slot).

## M16 — Limitationen & ehrliche Story
- Single Vantage Point (FRA): RTT-/Edge-Zahlen FRA-spezifisch. **C1 robust**, weil bei *konstanter* Netzdistanz gemessen → ~7,3× (gepoolt 8,3×) gilt aus jeder EU-Sicht.
- Confounds: Modellgröße+HW gekoppelt (Groq); Software-Stack nicht isoliert → „Backend (HW+Modell)".
- STT kein Engine-Beleg. Out of Scope: Transkript-/Audio-Qualität (nur Latenz + Verfügbarkeit). Diurnal = Snapshot.

## M17 — Prüfer-Einwände (Karteikarten)
- „3 Anbieter ~1 ms?" → Edge-Klassifikation (RTT ≤2 ms + CDN-ASN + Traceroute), per IP über 56 Slots; Infrastruktur, kein Messfehler; Backend separat → ~7,3× (gepoolt 8,3×).
- „STT langsam?" → `ttfp` (vor Endpointing); gepact Azure ≈ Deepgram (~1045 ms).
- „Warum 5.600 / Aggregation?" → 7×8×100; Median der Slot-Mediane + pooled + Bootstrap-CI.
- „macOS vs. EC2?" → nur EC2 (OpenSSL 3.x); macOS markiert + ausgeschlossen.
- „Connect-vs-ttft-Asymmetrie?" → STT ab Audio-Chunk, LLM/TTS ab Request; bewusst, damit E2E connect nicht doppelt.
- „Nur Modellgröße?" → ja, der Confound — deshalb wasserdichte Aussage NEGATIV; invertierte Geografie (EU-Mistral > US-Groq) zeigt es unabhängig.

## M18 — Stand & offene Punkte
- Kampagne beendet (Vollkampagne, abgeschlossen (56/56), A4 = finale Zahlen; Bootstrap-CI noch ausstehend); Arbeitstitel-Wahl offen; Färber angefragt (Exposé raus, Juli-Gespräch);
  Audit-Auflagen in der Auswertung anzuwenden; Folien (Block E) offen. **Nicht** mehr nötig: Neumessungen/Code-Umbau — nur Auswertung + Reporting.

---

# Ergänzungen aus dem Vollständigkeits-Audit (2026-06-19)

> Diese Punkte ergänzen die obigen Module (Lücken, die das Audit gefunden hat). Pro Modul zugeordnet.

## M2 (Ergänzung) — Relevanz / Latenz-Schwelle (= eine der „roten" Prüfer-Fragen) ✅ belegt
- **Warum Latenz überhaupt zählt:** Echtzeit-Voice ist *konversationell* — Nutzer erwarten antwort-nahe Reaktion.
  Die frühere „1-Sekunde" war willkürlich; sie ist jetzt durch **belegte Anker** ersetzt.
- **Zitierbare Anker (recherchiert 2026-06-19):**
  - **Miller (1968)**, *Response time in man-computer conversational transactions* — Ursprung der Schwellen.
  - **Nielsen (1993)**, *Usability Engineering* — <0,1 s „sofort", <1 s „Gedankenfluss bleibt erhalten", <10 s „Aufmerksamkeit".
  - **Stivers et al. (2009)**, *Universals and cultural variation in turn-taking in conversation*, PNAS 106(26):10587–10592 — Antwort-Lücke modal **~200 ms**, kulturübergreifend universal.
  - **ITU-T G.114**, *One-way transmission time* — interaktive Sprache: **≤150 ms** bevorzugt, **150–400 ms** akzeptabel, **>400 ms** inakzeptabel (einseitig, Echo-kontrolliert).
- **Fertiger Motivations-Absatz (drop-in, beim Schreiben formal zitieren):**
  > „Latenz ist für sprachbasierte Echtzeit-Assistenten kein Nebenkriterium, sondern bestimmt die Nutzbarkeit.
  > Menschliche Konversation läuft mit Antwort-Lücken von im Median nur etwa 200 ms ab, kulturübergreifend
  > universal (Stivers et al. 2009). Für interaktive Systeme gilt seit Miller (1968) bzw. Nielsen (1993):
  > Reaktionen unter rund einer Sekunde halten den Gedankenfluss aufrecht, etwa 0,1 s wirken unmittelbar; für
  > die reine Sprachübertragung empfiehlt ITU-T G.114 höchstens 150 ms (bevorzugt) bzw. 400 ms (noch akzeptabel)
  > einseitig. Eine STT→LLM→TTS-Pipeline muss ihre Gesamt-Antwortlatenz also in einem engen, sub-sekündlichen
  > Budget halten, weshalb die hier vermessenen Stufen-Latenzen — und die Frage, ob Netz oder Backend sie
  > dominieren — direkt über die Alltagstauglichkeit entscheiden."
- **C1-Brücke (stark fürs Gespräch):** Die EU→Edge-Strecke misst ~1 ms, weit innerhalb der 150 ms von G.114 →
  **nicht das Netz** ist der Engpass im Konversationsbudget, sondern die Backend-Hunderte-ms. Der Relevanz-Anker
  motiviert also direkt die Kernfrage.
- ⚠ **Rest-To-do (klein):** beim Schreiben der Motivation formal zitieren (Literaturverzeichnis) + entscheiden,
  welche der vier Anker rein sollen (Stivers + Nielsen/Miller + G.114 reichen).

## M3 (Ergänzung) — Deepgram-interne C1-Mini-Inversion
- Deepgram trifft 6 US-IPs in 2 Rechenzentren. Der **langsamere** `ttft`-Mode (Cogent-DC, ~101 ms RTT) hat eine
  **niedrigere** RTT als der schnellere Mode (~140 ms) → der langsamere Mode ist Backend/DC-Wahl, **nicht** Netz.
  Stützt C1 ein **zweites Mal innerhalb eines** Anbieters. Eleganter Konter, falls jemand Deepgram-Streuung als
  „Netz erklärt doch Latenz" deutet. (Beleg: `asn_per_ip.md`.)

## M6 (Ergänzung) — DNS-Dimension von Layer 1
- Layer 1 misst auch **DNS** (erste der 4 L1-Säulen): Auflösung über **3 Resolver** (Google 8.8.8.8, Cloudflare
  1.1.1.1, Quad9 9.9.9.9) + TTL. So erkennt man Round-Robin/Anycast: Deepgram löst auf **6 IPs über 2 ASNs** auf
  → Multi-DC. (Optional DNSSEC-AD-Flag.) Antwort auf „wie habt ihr Round-Robin/Anycast erkannt, welche Resolver?".

## M8 (Ergänzung) — Die zwei IP-Felder & Output-Mengen-Confound
- **IP-Felder:** top-level `resolved_ip` = echter Peer der Mess-Anfrage (`getpeername`), **null bei Fails** → nur
  für die Cross-Layer-RTT-Brücke (nur Samples mit `resolved_ip == connect.resolved_ip`). `connect.resolved_ip` =
  vom Wegwerf-Socket, **immer befüllt** → für Region/ASN/Verfügbarkeit. Weichen bei Round-Robin in ~29 % ab.
  **Fails NIE über `top-level == null` filtern** (sonst verschwinden Timeouts aus der Verfügbarkeit) — über
  `success`/Fehler-String filtern.
- **Output-Mengen-Confound (A8):** `total_ms` skaliert mit der Ausgabelänge → ein wortkarges Modell wirkt „schnell"
  durch Knappheit, nicht Tempo. Deshalb `ttft`/`ttfa` (mengen-unabhängig) **primär**, `total_ms` nur sekundär
  (pro-Token normalisieren). `max_tokens=50` ist ein **Cap**, kein Fixwert. TTS: nur der mp3-**Container** ist
  gepinnt, nicht die Bitrate → `audio_bytes` ~3,6× verschieden → nur **Erfolgs-Gate**, kein Vergleichsmaß.

## M9 (Ergänzung) — `ttfp` enthält ~1 In-Band-RTT
- `ttfp` ist eine *Engine*-Metrik, enthält aber bauartbedingt **einen Netz-Roundtrip** (Audio raus + Interim
  zurück) — also Netz + Engine-Reaktion, nicht reine Rechenzeit. **Trennung:** den Netz-Anteil über `connect`/RTT
  separat abziehen (am Edge ~1 ms, US ~140 ms). Prüfer-Falle „ist `ttfp` nicht auch netzabhängig?" → ja, um genau
  ~1 RTT, der bekannt und abziehbar ist.

## M12 (Ergänzung) — Deepgram-Beleglage (teilzirkulär)
- Für Deepgram kommt die per-IP-RTT **nur aus dem L3-`connect`-Timer** (gleiche SYN→SYN-ACK-Größe), nicht aus einem
  **unabhängigen** L1-Ping — der eigene L1-Ping deckte nur **1 von 6** produktiv getroffenen IPs; der Slow-Mode-DC
  wurde nie unabhängig L1-gemessen. `asn_per_ip.md` schließt die Lücke sauber nur für die **LLMs** (100 % AS13335).
  → ehrlich als Limitation der Cross-Layer-Brücke benennen (trifft genau die vom Prof bemängelte Verankerung).

## M13 (Ergänzung) — Survivorship-Zensur & Monte-Carlo-Faltung
- **Survivorship-Zensur:** Bei OpenAI-TTS (3,1 % (173/5600) Fails) ist **jedes Quantil oberhalb der Fail-Rate** am
  30-s-Timeout **zensiert** — p95/p99 sind ~30 s (Cap), kein echtes Backend-Tail. Deshalb kann OpenAI-TTS
  gleichzeitig schnell (p50) **und** das schlechteste Tail haben. Immer berichten: „p95 = X (nur erfolgreiche,
  96,9 %); Gesamtverfügbarkeit separat."
- **E2E = Monte-Carlo-Faltung:** Pipeline-Gesamtlatenz **nicht** durch Median-Addition, sondern: aus jeder
  Phasen-Verteilung (`stt_ttft`, `llm_ttft`, `tts_ttfa`) zufällig ziehen, summieren, ~10.000× wiederholen → echte
  E2E-Verteilung mit p50/p90/p95 + CI (p95 der Summe ≠ Summe der p95).

## M14 (Ergänzung) — `ttl_ms` existiert nicht
- ⚠ Wie H3 (Doku behauptet etwas, das es nicht gibt): **`ttl_ms` (Time-to-Last-Token) existiert nicht** in
  Code/Daten. Die „Pro-Token-Normalisierung über `ttl_ms`" ist so **nicht ausführbar** → stattdessen `total_ms`
  nutzen und Pro-Token-Rate als `(total_ms − ttft_ms) / output_tokens` rechnen. Sonst bricht „wir normalisieren
  pro Token" bei der Rückfrage „mit welcher Spalte?".

## M16 (Ergänzung) — Mess-Floor / Stack-Overhead-Baseline
- Eingeräumte Grenze: die App-Timer haben einen **Stack-Overhead-Floor**, der nicht „Netz" ist: `tls_handshake`
  ist **krypto-CPU-dominiert** (~3,5–5 ms bei TLS 1.3), **nicht** „1 RTT"; rev.ai TLS 1.2 kostet zusätzlich eine
  ganze RTT (M4); dazu SSE-Parsing und Python-GIL. → bei sehr kleinen Werten (Edge ~1 ms) ist ein Teil
  Mess-/Stack-Floor, nicht reine Netz-/Backend-Zeit. Ehrlich als Baseline-Limitation nennen.

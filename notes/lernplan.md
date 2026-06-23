# Lernplan — Das ganze Repo erklären können (Block B)

> **Zweck:** Gerüst, das dich Schritt für Schritt durch das **gesamte Projekt** führt — bis du jeden Punkt einem
> skeptischen Prüfer (Prof. Wählisch) **in eigenen Worten** erklären kannst. Genau das war der Grund für den
> Neuanfang: nicht „Zahlen falsch", sondern „Methodik nicht dargelegt".
>
> **Das hier ist nur die Struktur** — *was* du lernst, *wo* es steht, und *welche Fragen* du am Ende beantworten
> können musst. Die **Inhalte/Antworten** erarbeiten wir Modul für Modul live (per `/explain`). Die faktengeprüften
> Antworten stehen in **`lernplan_referenz.md`** — dort schaust du **erst nach deinem eigenen Erklärversuch** rein.
>
> **Ablauf je Modul:** `/explain <Modul>` → zusammen durchgehen → die Erklär-Fragen **laut in eigenen Worten**
> beantworten → in der Referenz gegenprüfen → erst dann ☑. Realistisch 1–2 Module pro Sitzung.
>
> **Status:** ☐ offen · ◐ in Arbeit · ☑ „kann ich erklären" · **Stand:** 2026-06-19

---

## Repo-Landkarte (Orientierung — wo liegt was)

| Ort | Was drin ist |
|-----|--------------|
| `CLAUDE.md`, `NEUANFANG.md`, `HANDOFF.md` | Projekt-Hubs: Forschungsfrage, Contribution, Stand, To-dos |
| `setup/messprotokoll.md` | **Methodik-Bibel** (3 Layer, Metriken, Kampagne, Aggregation, Fehler) |
| `setup/anbieter_auswahl.md` | Welche 9 Anbieter, mit Begründung |
| `setup/api_endpunkte.md` | Hosts/URLs/Auth + Edge-/Host-Klassifikation |
| `setup/deployment.md`, `setup/mess_kommandos.md` | EC2-Betrieb + welcher Befehl misst was |
| `setup/AUDIT_stt_methodik_2026-06-16.md` | Warum STT-Primärmetrik `ttfp` (Modul 9) |
| `measurements/layer1,2,3/` | Code der drei Schichten |
| `data/audit_20260618/` | Maßgebliche Daten + Audit-Urteil (16 Slots, `VERDICT.md`, `l1_rtt_per_ip.md`, `asn_per_ip.md`) |
| `archived/` | Alte Iteration vor dem Neuanfang — nur Nachschlagewerk |

---

## Vorlauf (vor dem ersten Modul, ~25 min)

- **Mini-Glossar** (10 min): TCP-/TLS-Handshake, WebSocket-Upgrade, SSE (Server-Sent Events), Streaming,
  Cold-Start, RTT, ASN, Edge/CDN. Diese Begriffe tauchen überall auf — einmal sauber klären spart später Stocken.
- **Statistik-Vorlauf** (10–15 min, spätestens vor Teil 6): Median vs. Mittelwert, Perzentil, Bootstrap-
  Konfidenzintervall, warum hohe Perzentile (p95/p99) mehr Daten brauchen.

## Tagesplan für morgen (priorisiert — 18 Module NICHT gleich tief)

> **Realität:** 6 tragende Module (**M3, M6, M8, M9, M13, M17**) je 45–60 min = das Herz. Die übrigen 12 als
> 15–20-min-Durchläufe; M15+M16 als Schnell-Wiederholung schon gelernter Punkte. So wird es ein voller,
> aber machbarer Tag (~9–10 h inkl. Pausen).

- **Vormittag (Fundament, ~4 h):** Glossar → M1 → **M2 (+ Latenz-Schwelle/Literatur)** → M5 → **M6 (Kern, + DNS)**
  → **M8 (Kern, + IP-Felder + Output-Confound)** → **M9 (Kern, + In-Band-RTT)**.
- **Mittag (Kernaussage, ~1,5 h):** **M3 (Kern — jetzt mit Fundament aus M6+M8)** → M4 → M11.
- **Nachmittag (Daten & Ehrlichkeit, ~2,5 h):** Statistik-Vorlauf → **M13 (Kern, + Survivorship + Monte-Carlo)**
  → M12 → M7 → M10 (nur Überblick) → M14 → M15+M16 (Schnell-Wiederholung).
- **Abend (Selbsttest, ~45 min):** **M17 (Karteikarten laut, ohne Nachschauen)** → M18.

---

# TEIL 1 — Das Warum

## Modul 1 — Vertrauensproblem & Neuanfang ☑
**Ziel:** Erklären, *warum* das Projekt neu aufgebaut wurde.
**Themen:** Was „ich vertraue den Daten nicht" wissenschaftlich heißt · Doku-/Reproduzierbarkeits-Problem (kein „Zahlen falsch") · Leitprinzip „erst Methodik, dann Code, dann messen" · was behalten/verworfen wurde.
**Quellen:** `NEUANFANG.md` §1, `CLAUDE.md` §„Warum der Neuanfang".
**Erklär-Check:** Was heißt „ich vertraue den Daten nicht" (Reproduzierbarkeit, nicht Betrug)? Was stellt Vertrauen wieder her?

## Modul 2 — Die Forschungsfrage ☑
**Ziel:** Die Frage exakt wiedergeben und ihre Offenheit verteidigen.
**Themen:** Wortlaut der Frage · Vergleich von *Anteilen* (Netz vs. Backend) · Beidseitigkeit als Stärke · **Relevanz: ab wann ist Latenz ein Problem (Akzeptanzbudget) + Literatur-Anker** ✅ (Anker recherchiert: Stivers 2009 ~200 ms · Miller 1968 / Nielsen 1993 · ITU-T G.114; fertiger Absatz in der Referenz — beim Schreiben nur formal zitieren).
**Quellen:** `CLAUDE.md` §Forschungsfrage, `NEUANFANG.md` §2.1.
**Erklär-Check:** Warum ist die Offenheit der Frage gut für die Glaubwürdigkeit? Ab wann ist Latenz spürbar/ein Problem — und worauf stützt du das?

---

# TEIL 2 — Die Kernaussage (C1/C2/C3)

## Modul 3 — C1 „Backend statt Geografie" + schärfster Beleg ☑ ⭐
**Ziel:** Kernaussage + stärksten Beweis + ehrliche Grenze verteidigen.
**Themen:** negative Kernaussage vs. Overclaim · LLM @ identischem Cloudflare-Edge · Geografie-Inversion · TTS als zweiter Beleg · warum STT nicht zählt · Modellgrößen-Confound · warum „Engine" nicht im Titel · H1 (Pilot- vs. Kampagnenzahlen) · **Nebenbeleg: Deepgram-interne Inversion** (langsamerer DC hat niedrigere RTT → Backend, nicht Netz).
**Quellen:** `CLAUDE.md` §Contribution, `HANDOFF.md` §3, `data/audit_20260618/{l1_rtt_per_ip.md,asn_per_ip.md}`.
**Erklär-Check:** Warum ist der LLM-Beleg schärfer als TTS? Warum zählt STT nicht? Warum ist „Mistral langsamer als Groq" ein K.o. für Geografie? Warum darf „Engine" nicht in den Titel?

## Modul 4 — C2 (3-Schichten) & C3 (Connect-Heuristik) ◐
**Ziel:** Die *methodischen* Beiträge benennen.
**Themen:** 3-Schichten als reproduzierbarer Beitrag · Layer 2 validiert Layer 3 · C3 bewusst kein Gütemaß.
**Quellen:** `CLAUDE.md` §Contribution, `NEUANFANG.md` §2.1.
**Erklär-Check:** Was bringt Layer 2 zusätzlich zu Layer 1+3? Warum ist C3 absichtlich vorsichtig formuliert?

---

# TEIL 3 — Die Methodik (Setup & 3 Schichten)

## Modul 5 — Setup, Cold-Start & Kampagne ◐
**Ziel:** Das Gesamt-Messdesign erklären.
**Themen:** Vantage Point EC2 (warum nicht burstable) · Cold-Start/kein Pooling · 7×8 Slots × n=100 interleaved · Reproduzierbarkeits-Anker (`run_meta`) · Code eingefroren.
**Quellen:** `setup/messprotokoll.md` (Kampagne), `setup/deployment.md`, `measurements/layer3/run.py`.
**Erklär-Check:** Warum keine burstable-Instanz? Warum Cold-Start? Warum UTC-Slots? Warum 5.600/Endpunkt?

## Modul 6 — Layer 1: Infrastruktur (Edge vs. Host) ◐ ⭐
**Ziel:** Den Einwand „3 Anbieter mit ~1 ms" auflösen.
**Themen:** TCP-Ping als Primärmetrik (warum nicht ICMP) · die 3 Edge-Kriterien · die 3 RTT-Klassen · „Messung > Marketing" · H4/A1 (macOS-vs-EC2, LibreSSL-TLS) · **DNS-Dimension: Multi-Resolver (Google/Cloudflare/Quad9) + TTL** (Round-Robin/Anycast erkennen).
**Quellen:** `setup/messprotokoll.md` (Layer 1), `setup/api_endpunkte.md`, `measurements/layer1/*`.
**Erklär-Check:** Warum TCP- statt ICMP-Ping? Nach welchen 3 Kriterien ist etwas „Edge"? Warum ist Azure trotz 11 ms ein „Host"? Wie habt ihr Round-Robin/Anycast im DNS erkannt (welche Resolver)?

## Modul 7 — Layer 2: Paket-Eichung ◐
**Ziel:** Erklären, was „geeicht" heißt — und was nicht.
**Themen:** das Eich-Experiment (tcpdump-Vergleich) · ~0,1-ms-Übereinstimmung · der +Offset · H2-Reichweite (nur Connect-Timer).
**Quellen:** `setup/messprotokoll.md` (Layer 2), `measurements/layer2/{capture,analyze}.py`, `data/layer2/`.
**Erklär-Check:** Was wird gegen was verglichen? Was bedeutet der +0,1-ms-Offset? Welche Zahlen sind NICHT geeicht und warum?

## Modul 8 — Layer 3 & Metrik-Asymmetrie ◐ ⭐
**Ziel:** Die Metriken sattelfest erklären (häufigster Prüf-Punkt).
**Themen:** Connect-Submetriken (Wegwerf-Socket) · die Asymmetrie (STT connect-exklusiv vs. LLM/TTS connect-inklusiv) · warum · E2E nicht naiv addieren · **die zwei IP-Felder** (`resolved_ip` vs. `connect.resolved_ip`) + Fail-Filter-Falle · **Output-Mengen-Confound (A8)** (warum `ttft`/`ttfa` primär, `total_ms`/`audio_bytes` nicht vergleichbar).
**Quellen:** `setup/messprotokoll.md` (Metrik-Asymmetrie), `measurements/layer3/{connect,llm,tts}.py`.
**Erklär-Check:** Warum startet die STT-Uhr anders als bei LLM/TTS? Was passiert, wenn man E2E naiv aufsummiert? Welches IP-Feld wofür — und warum nie Fails über `null` filtern? Warum gewinnt ein wortkarges Modell nicht einfach durch Knappheit?

## Modul 9 — STT `ttfp` + 1×-Pacing ◐ ⭐
**Ziel:** Die wichtigste Metrik-Korrektur erklären.
**Themen:** Problem von `ttft` (Engine + Endpointing vermischt) · `ttfp` als Lösung · 1×-Realtime-Pacing + paralleler Empfang · Azure ≈ Deepgram gepact · 3 ehrliche Grenzen von `ttfp` · **`ttfp` enthält ~1 In-Band-RTT** (Netz-Roundtrip + Engine-Reaktion, nicht reine Rechenzeit).
**Quellen:** `setup/AUDIT_stt_methodik_2026-06-16.md`, `measurements/layer3/stt.py`.
**Erklär-Check:** Warum ist `ttft` für STT unfair? Was bringt 1×-Pacing? Warum sind Azure/Deepgram auf `ttfp` gleichauf? Warum trägt STT C1 nicht? `ttfp` enthält einen Netz-Roundtrip — wie trennst du Netz von Backend?

---

# TEIL 4 — Der Code

## Modul 10 — Code-Architektur & Timing ◐
**Ziel:** Ein Skript am Bildschirm grob durchgehen können.
**Themen:** Verzeichnis-Struktur (layer1/2/3) · `perf_counter` · Cold-Start im Code · IPv4-Zwang (warum) · Bibliotheken (httpx/websockets/ssl/tcpdump/asyncio) · `run.py`-Orchestrierung · Erfolg content-basiert · Fehler als Roh-String (H3).
**Quellen:** `measurements/layer3/{config,connect,llm,tts,stt,run}.py`, `measurements/layer1/*`, `measurements/layer2/*`.
**Erklär-Check:** Wo startet/stoppt die LLM-`ttft`-Uhr im Code? Warum frischer Client je Call? Was verhindert das Round-Robin-Rotieren? Warum ist „Erfolg" content-basiert?

---

# TEIL 5 — Die Anbieter

## Modul 11 — Provider-Matrix & „warum US" ◐
**Ziel:** Verteidigen, warum genau diese 9 — und warum überwiegend US.
**Themen:** die Pipeline & 9 Endpunkte · EU-Kontrastpunkte (Azure, Mistral) · „warum US" als Befund (keine reifen EU-Streaming-Anbieter) · Modell-Pinning + `effective_model`.
**Quellen:** `setup/anbieter_auswahl.md`, `CLAUDE.md` §Provider-Matrix.
**Erklär-Check:** Warum diese 9? Warum überwiegend US (und warum kein Sampling-Fehler)? Rolle von Mistral/Azure?

---

# TEIL 6 — Daten & Auswertung

## Modul 12 — Datenartefakte & echte Ergebnisse ☐
**Ziel:** Wissen, wo welche Zahl herkommt und was sie bedeutet.
**Themen:** maßgeblicher Datensatz + Beleg-Artefakte · die Kernzahlen (LLM/TTS/STT/Edge/Eichung) · Interim vs. final · was nicht verwendet wird · **Deepgram-Beleglage** (per-IP-RTT nur aus L3-connect; nur 1/6 IPs unabhängig L1-gepingt).
**Quellen:** `data/audit_20260618/*`, `HANDOFF.md` §3/§5.
**Erklär-Check:** Welcher Datensatz ist maßgeblich, welcher nicht — und warum? Was ist Zwischenstand, was final?

## Modul 13 — Aggregation (A4) & Verfügbarkeit ☐
**Ziel:** Erklären, wie aus 5.600 Zahlen eine Headline wird — ehrlich.
**Themen:** zweistufiger Median (A4) + pooled-Gegenprobe + Bootstrap-CI · Perzentil-Regel (p95/p99 nur volle Kampagne) · Verfügbarkeit als eigene Achse (Pareto) · success-only · **Survivorship-Zensur** (p95/p99 oberhalb der Fail-Rate zensiert, kein echtes Backend-Tail) · **E2E = Monte-Carlo-Faltung** der 3 Phasen-Verteilungen (statt Median-Addition).
**Quellen:** `setup/messprotokoll.md` (Aggregation, Verfügbarkeit).
**Erklär-Check:** Warum Median der Slot-Mediane statt poolen? Warum p95 nur über die volle Kampagne? Warum Verfügbarkeit getrennt? Warum kann OpenAI-TTS gleichzeitig schnell (p50) und das schlechteste Tail haben?

---

# TEIL 7 — Ehrlichkeit: Probleme & Limitationen

## Modul 14 — HIGH-Auflagen H1–H4 ☐
**Ziel:** Die vier wichtigsten Audit-Befunde als *Stärke* (Selbstkorrektur) präsentieren.
**Themen:** H1 Headline-Zahlen (Pilot vs. Kampagne) · H2 Eichungs-Reichweite · H3 Fehler-Filter (kein Enum) · H4 L1-Datensatz (macOS vs. EC2) · **`ttl_ms` existiert nicht** → Pro-Token-Rate über `(total−ttft)/output_tokens`.
**Quellen:** `HANDOFF.md` §4, `data/audit_20260618/VERDICT.md`.
**Erklär-Check:** Formuliere für jede der 4 eine ruhige Ein-Satz-Antwort an einen skeptischen Prüfer.

## Modul 15 — MEDIUM-Punkte & Confounds ☐
**Ziel:** Die wichtigsten Reporting-/Interpretations-Fallen kennen.
**Themen:** M1 E2E-Formel · M2 OpenAI-TTS @ Cloudflare · M3 Backhaul-Confound · M4 TLS-1.2-RTT (rev.ai) · M6 Round-0 · M9/M10 Deepgram-Textmix & OpenAI-TTS-Verfügbarkeit/Diurnal.
**Quellen:** `data/audit_20260618/VERDICT.md`, `HANDOFF.md` §5.
**Erklär-Check:** Welche Punkte betreffen die *Interpretation* (nicht nur Reporting)? Wie entkräftest du M3?

## Modul 16 — Limitationen & ehrliche Gesamtstory ☐
**Ziel:** Souverän sagen, was die Arbeit **nicht** kann.
**Themen:** Single Vantage Point (warum C1 trotzdem robust) · Confounds (HW+Modell) · STT kein Engine-Beleg · Out of Scope (Qualität) · Diurnal = Snapshot · **Mess-Floor / Stack-Overhead** (TLS-Krypto-CPU ~3,5–5 ms statt 1 RTT, SSE-Parsing, GIL) als eingeräumte Grenze.
**Quellen:** `setup/messprotokoll.md` (Limitation), `HANDOFF.md` §3 (Interpretations-Kompass).
**Erklär-Check:** Warum ist „Single Vantage Point" für C1 nicht tödlich? Unterschied „eingeräumte Limitation" vs. „verteidigbare Generalisierung"?

---

# TEIL 8 — Verteidigung

## Modul 17 — Prüfer-Einwände & Ein-Satz-Antworten ☐
**Ziel:** Die wahrscheinlichsten Wählisch-Fragen reflexartig beantworten.
**Themen (Karteikarten):** „3 Anbieter ~1 ms?" · „STT langsam?" · „Warum 5.600 / Aggregation?" · „macOS vs. EC2?" · „Connect-vs-ttft-Asymmetrie?" · „Nur Modellgröße?".
**Erklär-Check:** Jede Karte einmal laut, ohne nachzuschauen.

## Modul 18 — Stand & offene Punkte ☐
**Ziel:** Den aktuellen Projektstatus sauber zusammenfassen.
**Themen:** Vollkampagne, abgeschlossen (56/56) · Arbeitstitel offen · Färber/Juli · Audit-Auflagen in der Auswertung · Folien (Block E) · „nicht mehr nötig: Neumessungen".
**Quellen:** `HANDOFF.md`, `notes/arbeitsplan.md`.

---

## Offene Rückfragen (nachzuholen)

> Punkte, die beim Durchgehen offen blieben und vor dem ☑ noch geklärt/getestet werden müssen.

- **M4 — Erklär-Check noch offen** (Modul erklärt, aber aktiver Recall fehlt): (1) Was bringt Layer 2
  zusätzlich zu Layer 1+3? → keine neue Messung, sondern **Validierung des Connect-Timers** (paket-geeicht
  ±0,1 ms), NICHT von `ttft`/`ttfa`. (2) Warum ist C3 bewusst vorsichtig? → der `r=0.999`/`n=4`-Überverkauf
  (A1); statt `r` mit dem **Residualfehler** argumentieren.
- **M5 — Erklär-Check noch offen:** (1) Warum keine burstable-Instanz? → CPU-Credit-Throttling verfälscht
  ms-Timer; belegt via flachem `cpu_steal` (37→37). (2) Warum Cold-Start statt Pooling? → der Verbindungsaufbau
  ist der interessante EU-Anteil, den Pooling wegmitteln würde. (3) Warum UTC-Slots? → zeitzonen-/DST-frei,
  Tagesgang über Tage vergleichbar. (4) Warum interleaved? → Block-Variante gaukelt einen Anbieter-Unterschied
  vor, der nur Timing ist.
- **M6 — Erklär-Check noch offen:** (1) TCP- statt ICMP-Ping (ICMP von CDNs geblockt → nicht alle 9; TCP/443
  bei allen; denselben Port; ICMP nur Cross-Validierung). (2) Die 3 Edge-Kriterien (RTT ~1–2 ms ∧ CDN-ASN
  AS13335 ∧ traceroute endet im CDN-AS) und warum **alle drei** nötig. (3) Azure trotz 11 ms = Host → Bedingung
  (b) scheitert (AS8075 Microsoft, kein CDN). (4) DNS-Round-Robin/Anycast über 3 Resolver (Google/Cloudflare/
  Quad9) erkannt; Indiz Deepgram = 6 IPs über 2 ASNs.
- **M7 — Erklär-Check noch offen:** (1) Was gegen was? App-`tcp_handshake` (`perf_counter`) vs. Wire-SYN→SYN-ACK
  (Kernel-Zeitstempel aus PCAP), gepaart über den Quell-Port, N≈30. (2) Der +0,1-ms-Offset = Kernel-Returnzeit
  (App misst minimal mehr), klein + konstant → Beweis sauberer Messung, kein Fehler. (3) Nur der Connect-Timer
  ist geeicht, NICHT `ttft`/`ttfa` (starten erst beim Request im httpx/ws-Stack, gleicher `perf_counter`, aber
  nicht direkt paket-geeicht) → nie „alle L3-Zahlen validiert".
- **M8 — Erklär-Check noch offen:** (1) STT-Uhr connect-exklusiv (ab Audio-Chunk, Session steht schon) vs.
  LLM/TTS connect-inklusiv (ab Request, frische Verbindung) — bildet die reale Nutzungssituation ab. (2) E2E
  naiv = connect bei LLM/TTS doppelt gezählt; korrekte Formel `stt_connect + stt_ttft + llm_ttft + tts_ttfa`.
  (3) `connect.resolved_ip` (immer befüllt) für Region/ASN/Verfügbarkeit, top-level `resolved_ip` (null bei Fail)
  nur für RTT-Brücke; Fails NIE über `null` filtern (Timeouts verschwänden). (4) `ttft`/`ttfa` primär
  (mengen-unabhängig) → wortkarges Modell gewinnt nicht durch Knappheit; `total_ms` nur sekundär.
- **M9 — Erklär-Check noch offen:** (1) `ttft` unfair für STT (mischt Engine-Speed + anbieterspezifische
  Finalisierungs-/Endpointing-Politik). (2) 1×-Pacing zwingend, sonst liefert Deepgram im Dump kein Partial
  → `ttfp` unvergleichbar. (3) Azure ≈ Deepgram auf `ttfp`, weil der ~0,8-s-Pacing-Floor den RTT-Unterschied
  überdeckt. (4) `ttfp` enthält ~1 In-Band-RTT → Netz-Anteil aus Layer-1-RTT bekannt und abziehbar.
  Vollständig verschriftlicht in `lernskript_modul9.md`.
- **M11 — Erklär-Check noch offen:** (1) Warum diese 9 (kommerziell + echte Streaming-API + roher
  Protokollzugang; je Kategorie US + EU-Kontrast). (2) Warum überwiegend US = Befund, kein Sampling-Bias
  (keine marktreifen EU-Streaming-STT/TTS → EU muss US nutzen). (3) Mistral/Azure = eingebaute Geografie-
  Kontrollpunkte (Mistral zeigt die Inversion, Azure = echter naher Host).
- **Statistik-Einschub fürs `lernskript`:** Korrelation / `r` erklären (was `r` ist, warum `r=0.999`
  bei `n=4` trügerisch ist, Residualfehler statt `r`) — als kleiner Stats-Vorlauf-Block aufnehmen.
- **M10 — Erklär-Check noch offen:** (1) LLM-`ttft`-Uhr startet kurz vor dem Request-Absenden (vor frischer
  Verbindung), stoppt beim ersten Antwort-Chunk → connect automatisch inklusive. (2) Frischer Client je Call =
  technische Garantie für Cold-Start; Wiederverwenden → Keep-Alive, Verbindungsaufbau fiele ab Call 2 weg.
  (3) Rotation der Startreihenfolge verhindert, dass ein Anbieter dauerhaft auf einer festen (bevorzugten/
  benachteiligten) Position sitzt. (4) Erfolg inhaltsbasiert, sonst zählt eine quasi-leere Antwort als „schnell"
  (A10). Vollständig in `lernskript_modul10.md`.
- **Lernskripte liegen in `notes/lernen/`:** `tts/modulNN.md` (Fließtext, natürliche Sprache zum Vorlesen)
  + `md/modulNN.md` (strukturiert, Überschriften/Tabellen zum Lesen). **Vollständig niedergeschrieben: alle 18
  Module M1–M18** (je 18 Dateien pro Ordner). Stand 2026-06-22: **M4–M8 + M12–M18 ergänzt** (Multi-Agent-Workflow,
  faktengeprüft gegen `setup/*` + `lernplan_referenz.md`; M6 und M8 als ⭐-Kernmodule besonders ausführlich). Alle
  Zahlen = finale 56-Slot-A4-Werte (Vollkampagne, abgeschlossen (56/56); Bootstrap-CI noch ausstehend). TTS-Format verifiziert: keine Markdown-/Sonderzeichen,
  keine Ziffern, Zahlen ausgeschrieben, Orthografie (ß statt ss) bereinigt. **Tiefen-Faktencheck (55-Agenten-Workflow,
  803 Einzel-Fakten gegen `setup/*` + `lernplan_referenz.md`):** 31 bestätigte Befunde korrigiert (u.a. Freeze-Commit
  f9e6dc8, Eich-Differenz Deepgram +0,12 ms konsistent, ws_upgrade_ms existiert nicht → ws_connect_ms, Pilot-Faktor-
  Richtung, „158/161 Timeouts" statt Fehler, Diurnal als unbestätigt gehedged, L1-Momentaufnahme vs. 16 L3-Slots
  entflochten). Quer-Konsistenz Zahlen + Kernaussagen: 0 Widersprüche.

---

## Fortschritt
☑ M1 ☑ M2 ☑ M3 ◐ M4 ◐ M5 ◐ M6 ◐ M7 ◐ M8 ◐ M9 ◐ M10 ◐ M11 ☐ M12 ☐ M13 ☐ M14 ☐ M15 ☐ M16 ☐ M17 ☐ M18

> **Lernskripte (Stand 2026-06-22):** Alle 18 Module sind in `notes/lernen/tts/` + `notes/lernen/md/` verschriftlicht.
> Die ☑/◐/☐-Marken oben bezeichnen weiterhin den **Erklär-Stand** (aktiver Recall im Gespräch), *nicht* die Existenz
> der Skripte — M4–M8 + M12–M18 sind geschrieben, aber erst nach dem mündlichen Durchgang auf ☑ zu setzen.

> **Empfohlener Einstieg:** Modul 1–3 (Warum + Kernaussage) geben dir das Gerüst, mit dem du alles andere einordnest.
> Danach 5→9 (Methodik/Metriken — das Herz). Sag „**/explain Modul 1**", dann legen wir los.

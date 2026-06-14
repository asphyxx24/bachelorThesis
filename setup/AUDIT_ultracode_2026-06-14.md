> Quelle: ultracode-Workflow wf_b91f6d35 — 59 Agenten, 72 Findings (48 signifikant, 41 bestaetigt). Run 2026-06-14.

# Audit-Synthese — Setup-Review vor dem Skript-Bau (Neuanfang)

> Stand 2026-06-14 · Quelle: zusammengeführte E1–E5 + R1–R5 Findings (verifiziert) · Zielartefakte: `setup/messprotokoll.md`, `setup/mess_kommandos.md`, `setup/api_endpunkte.md`, `setup/anbieter_auswahl.md`, `NEUANFANG.md`

## 1) Executive Summary

35 signifikante Findings geprüft; nach adversarialer Verifikation bleiben **0 kritische**, **2 hohe**, **~13 mittlere** und der Rest niedrig/info — keiner invalidiert die Kern-These „Engine schlägt Geografie". Die meisten „kritisch/hoch"-Findings betrafen **archivierte Alt-Skripte** (`archived/`), die per Neuanfang ohnehin verworfen werden, und sind in `messprotokoll.md` als Soll bereits korrekt spezifiziert — also **Implementierungs-Checklisten, keine offenen Defekte**. Echte, noch ungelöste Lücken im neuen `setup/`: **Modell-Versionen ungepinnt** (R4, hoch), **Edge/Host-Klassifikator nicht operationalisiert** (R3, mittel), **Statistik-Schicht fehlt** (Aggregation, CI, Perzentil-Ehrlichkeit, R2, mittel), **Per-Run-Capture von Ziel-IP/Versionen/Instanz-Doku** (R4, mittel) und **TLS-Probe-Footgun auf macOS-LibreSSL** (E2, hoch — aber nur bei lokalem Durchsickern). **Go für den Skript-Bau** — die Bausteine sind tragfähig; Block A unten vor/während des Baus abarbeiten, Block B+D beim Schreiben des Methodik-Kapitels.

---

## 2) A — Bestätigte Fehler (jetzt fixen)

Sortiert nach Severity. „Doku-Fix" = ein Absatz in `setup/`; „Code-Pflicht" = beim Bau der neuen Skripte zu beachten.

### A1 · [HOCH] TLS-Versions-Probe auf macOS/LibreSSL meldet systematisch falsch (1.2 statt 1.3)
- **Begründung:** `/usr/bin/python3` **und der projekteigene `.venv`** sind gegen LibreSSL 2.8.3 gelinkt; `create_default_context().maximum_version` cappt auf TLS 1.2 → die `mess_kommandos.md`-(b)-Probe meldet für ALLE 7 Hosts TLSv1.2. Echtes OpenSSL (EC2/Ubuntu) handelt 6/7 als 1.3 aus. `curl` liefert auf macOS gar kein `tls_version` → die Python-ssl-Probe ist die einzige Quelle, kein Cross-Check fängt das ab.
- **Handlung:** (1) `tls_version` NIE aus macOS-Python übernehmen; Kampagne auf EC2 fahren. (2) Im Skript `maximum_version` NICHT cappen, nach Handshake `ssock.version()` als **harten Guard** prüfen. (3) Pro Messung `ssl.OPENSSL_VERSION` mitloggen (LibreSSL-Zeilen sofort verwerfbar). (4) `openssl s_client` (echtes OpenSSL) als Cross-Check. (5) Interpreter pinnen.
- **Datei:** `setup/messprotokoll.md` (Reproduzierbarkeits-Voraussetzung), neues Layer-1-TLS-Skript.

### A2 · [HOCH] Modell-Versionen nicht gepinnt/datiert → Reproduktion unmöglich
- **Begründung:** `gpt-4o-mini`, `tts-1`, `nova-3`, `aura-2-asteria-en`, `en-US-JennyNeural` sind rollende Aliase (nur `mistral-small-2603` trägt ein Datum). `anbieter_auswahl.md:73` führt das als „offenen Punkt", nicht erledigt. Zudem wird die pro-Run effektiv bediente Modell-Version nirgends gespeichert — stiller Backend-Drift würde den Headline-Befund unbemerkt nicht-reproduzierbar machen.
- **Handlung:** (1) In `api_endpunkte.md` je Endpunkt exakte Modell-ID + Abrufdatum festschreiben; datierte Snapshots verwenden wo verfügbar (z. B. `gpt-4o-mini-2024-07-18`), sonst als Limitation benennen. (2) LLM (OpenAI-Schema-SSE): `chunk.get('model')` als `effective_model` ins JSONL (liegt bereits geparst vor, wird heute verworfen). (3) STT/TTS: angefragte ID + Doc-Pinning, opportunistisch Response-Header.
- **Datei:** `setup/api_endpunkte.md`, `setup/messprotokoll.md` (§Rohdaten-Speicherung), neue L3-Skripte.

### A3 · [MITTEL] Edge/Host-Terminierungs-Klassifikator deklariert, aber nicht operationalisiert
- **Begründung:** Dreh- und Angelpunkt für C2 und den zentralen Prof-Einwand („3 Anbieter mit ~1 ms RTT noch nicht erklärt"). `NEUANFANG.md §3` nennt die Werkzeuge, aber **kein Kriterium, kein Ziel-Artefakt, keine Spalte**. `api_endpunkte.md` hält Cloudflare-Range bewusst „nicht gedeutet" fest.
- **Handlung:** Klassifikator festschreiben: „Edge-terminiert" gdw. **(a) TCP-RTT ≈ 1–2 ms aus FRA UND (b) IP in CDN-ASN (Cloudflare AS13335) UND (c) traceroute bricht am CDN ab"** (Konjunktion zwingend — Deepgram hat Anycast-Label, aber ~143 ms = NICHT Edge). RTT-Beleg aus **TCP-Ping** (rev.ai blockt ICMP). Ergebnis als feste Spalte „Terminierung (Edge/Host)" in `api_endpunkte.md` = Single Source of Truth; explizit: die ~1-ms-RTT ist der Terminierungs-Nachweis, nicht der IP-Besitz.
- **Datei:** `setup/messprotokoll.md` (neuer Layer-1-Endpunkt-Abschnitt), `setup/api_endpunkte.md`.

### A4 · [MITTEL] Statistik-Schicht fehlt: Aggregation, CI und Perzentil-Anspruch (R2-Bündel)
Drei zusammengehörige Lücken, gemeinsam als **Abschnitt „Aggregation & Inferenz" in `messprotokoll.md`** lösen:
- **(a) Aggregationsregel undefiniert:** 56 Slots × 100 Runs → keine Regel, wie EINE Provider-Zahl entsteht (Pooling aller 5600 vs. Median-of-Slot-Medians liefern andere Zahl + CI). Headline „Deepgram 575 < Azure 1715" ist sonst nicht reproduzierbar definiert. → Primär: Median je (Endpunkt × Slot-`tag`) über 7 Tage (n≈700) = Diurnal-Profil; **EINE** Headline-Regel explizit benennen (Empfehlung: Median der 8 Slot-Mediane + gepoolter Median als Sensitivität).
- **(b) Perzentil-Overclaim:** `messprotokoll.md:256` sagt „n=100 komfortabel auch für Perzentile" — falsch für p99 (faktisch das Maximum aus 100). p50/p90 slot-aufgelöst ok; p95 nur gepoolt + Bootstrap-CI; p99 nur über alle 56 Slots ODER als Limitation. Faustregel n·(1−q) ≥ 5–10 ergänzen; rechtsschief (CV 87 %, eigene Daten) → Bootstrap statt t-CI.
- **(c) CI nirgends verankert:** `grep konfidenz|bootstrap|ci` = 0 Treffer in `setup/`. Headline-Vergleiche treten als nackte Punktschätzer auf — genau die Prof-Angriffsfläche. → Jede Median/Perzentil-Zahl bekommt Bootstrap-95%-CI; Cross-Provider „X schneller als Y" primär über **Differenz-Bootstrap/Mann-Whitney** (nicht nur disjunkte CIs). „56/56 Slots"-Aussage explizit als Slot-Median-Vorzeichentest kennzeichnen (Roh-Tails überlappen).
- **Datei:** `setup/messprotokoll.md`.

### A5 · [MITTEL] Per-Run-Capture fehlt: aufgelöste Ziel-IP, Versionen, Instanz-Metadaten
- **Begründung:** `messprotokoll.md:225-238` listet Per-Messung-Felder, aber NICHT die tatsächlich verbundene **Peer-IP** — ohne sie ist über 56 Slots nicht belegbar, welcher (Cloudflare-/Deepgram-)Edge ein Latenz-Sample bediente (blockiert den Edge-vs-Backend-Beleg). Ebenso fehlen Lib-/Python-Versionen (requirements.txt nur `>=`, kein Lockfile) und Instanz-Doku (`messprotokoll.md:298` führt das selbst als „offen").
- **Handlung:** (1) `sock.getpeername()[0]` direkt nach Connect als `resolved_ip` in JEDEN L3-Record (Kosten ~null, samplegenau). (2) `run_meta`-Record pro Slot: `git_commit`, `python_version` + `pip_freeze`/Lockfile-Hash, `instance_id/type`, `ami_id`, `kernel`, `iface`, `delay_s`. (3) Lockfile (`uv.lock`/`pip freeze`) committen; pro L3-Record `response.http_version` erfassen (robuster als httpx[http2]-Pinning).
- **Datei:** `setup/messprotokoll.md` (§Rohdaten-Speicherung + offener Hardware-Abschnitt), `requirements.txt` + Lockfile.

### A6 · [MITTEL] Instanz-Typ wählen: NICHT-burstable (CPU-Steal/Credit verfälscht ms-Timer)
- **Begründung:** `messprotokoll.md:9-13` dokumentiert nur Region; Instanz-Typ/AMI/Kernel fehlen (selbst als „offen" markiert). Die **alte** Instanz war `t3.small` (burstable, `archived/.../PROVENANCE.md:4`) — bei Credit-Erschöpfung springen ms-Latenzen ohne Netz-Ursache (genau die unerklärte Varianz, die der Prof bemängelt).
- **Handlung:** Festen non-burstable Typ (c6i.large/m6i.large) wählen + AMI/Kernel/vCPU/EBS/AZ fixieren. Pro Slot CPU-Steal-Time (`/proc/stat`) mitloggen → empirisch belegen, nicht nur behaupten.
- **Datei:** `setup/messprotokoll.md`.

### A7 · [MITTEL] Erfolgs-/Fehlerkriterium nicht operationalisiert (Timeouts, Output-Schwellen)
- **Begründung:** `messprotokoll.md:240-246` nennt Erfolg nur prosaisch („LLM ≥ Mindest-Tokenzahl"), keine Zahl. Ohne fixe Schwellen ist „Verfügbarkeit X %" (A8-Dimension) nicht reproduzierbar/angreifbar. (Hinweis: Connect-Timeout ist im Alt-Code bereits einheitlich 10 s; real asymmetrisch ist nur der Response-Timeout STT 20 s vs. LLM/TTS 30 s.)
- **Handlung:** Tabelle „Erfolgskriterien & Timeouts je Kategorie": Connect-Timeout, Response-Timeout (Asymmetrie vereinheitlichen oder begründen), Mindest-Output (LLM ≥ N Chunks, STT nicht-leeres Final, TTS ≥ X Bytes) + Fehler-Enum (`timeout/connection_reset/http_4xx/http_5xx/empty_output`) roh speichern.
- **Datei:** `setup/messprotokoll.md`.

### A8 · [MITTEL] Modell-/Inversions-Confound bei TTFT/total: Output-Menge nicht kontrolliert
- **Begründung:** Feste Inputs standardisieren nur die EINGABE. `total_ms`/`ttl_ms` skalieren mit Output-Tokenzahl (`max_tokens=50` ist nur Obergrenze) — ein knappes Modell „gewinnt" durch Geschwätzigkeit, nicht Speed. (TTS-Format-Teil ist überwiegend gelöst: Azure/Deepgram bereits mp3-gepinnt; nur OpenAI `response_format` offen. STT-`ttft` = Time-to-first-**FINAL** inkl. Endpointing.)
- **Handlung:** Engine-Primärmetrik = `ttft`/`ttfa` (output-mengen-robust); `total_ms`/`ttl_ms` nur sekundär bzw. pro Token normalisiert. OpenAI-TTS `response_format`+Rate explizit pinnen. STT-`ttft` als „inkl. Provider-Endpointing" etikettieren. **Wichtig:** Kern-Beleg (STT/TTS-Inversion) ruht auf `ttft`/`ttfa` → vom Confound NICHT betroffen.
- **Datei:** `setup/messprotokoll.md`, `setup/api_endpunkte.md` (TTS-Format).

### A9 · [NIEDRIG, billig] Doku-Korrekturen mit Außenwirkung
- **Deepgram-Label:** „USA (Anycast)" ist falsch → **„USA (Multi-DC, DNS-Round-Robin)"** (kurze TTL 4–5 s rotiert md1/sac1/sv1; NICHT GeoDNS). Korrigieren in `anbieter_auswahl.md`, `CLAUDE.md`, `NEUANFANG.md`. Per-Run-Logging des verbundenen DC/IP (s. A5) erklärt die RTT-Streuung 102–148 ms.
- **rev.ai-IP:** `api_endpunkte.md:87` „dedizierte IP 208.184.56.200" ist falsch zugeordnet — gehört zu Deepgram-Auflösung und ist AS6461 (Zayo)-Transit, keine dedizierte Deepgram-IP. Korrigieren.
- **`connect_ms` vs `connect_total_ms`:** `messprotokoll.md:47-48` nutzt den abgeschafften Begriff weiter → vereinheitlichen.
- **`-W 2`-Plattform-Notiz:** `mess_kommandos.md:37` — „`-W` = Sekunden (Linux), Millisekunden (macOS); lokale Tests `-t 5`". EC2-Kampagne korrekt, nur lokale Vortests betroffen.
- **rev.ai TLS 1.2:** echter Server-Befund (einziger TLS-1.2-Host) — als Color/Footnote führen, NICHT via macOS-LibreSSL belegen (zeigt fälschlich alle als 1.2).

---

## 3) B — Methodik-Änderungen zum Überdenken (kein harter Fehler)

- **Same-IP-Pinning für tcp≈icmp-Validierung festschreiben:** ICMP pingt aktuell den **Hostnamen** (`mess_kommandos.md:37`), TCP die **aufgelöste IP** — bei Anycast trifft das verschiedene Edges (groq Δ persistent ~8–10 ms). Beide auf DIESELBE einmalig aufgelöste IP pinnen; Validierung auf direkte Hosts (deepgram/azure-stt/azure-tts) stützen. **openai NICHT als „direkter Anker" zählen** — ist Cloudflare. Das fragile „groq=signal vs mistral=noise"-Detail weglassen (vantage-point-abhängig).
- **IP-Version verbindlich festlegen:** groq/mistral bieten AAAA → `curl`/`traceroute`/ssl ohne `-4` driften zu IPv6, während TCP-Ping (`gethostbyname`) IPv4 misst. Empfehlung: IPv4 erzwingen (`curl -4`, `traceroute -4`, `dig A`, ssl zur v4-IP).
- **ASN pro IP, nicht Single-Sample:** Deepgram floatet AS174 (Cogent) ↔ AS6461 (Zayo) je DNS-Antwort. Alle aufgelösten IPs je Host lookupen; Org-Namen via zweitem Cymru-Lookup (`ASn.asn.cymru.com`): AS13335=Cloudflare, AS174=Cogent, AS6461=Zayo, AS16509=Amazon, AS8075=Microsoft.
- **min-RTT-Schätzer:** N (Ping-Wiederholungen) beziffern (≥20), Literaturreferenz für min-RTT-als-Pfadlatenz setzen, und festlegen, ob min oder median in die Cross-Layer-Brücke eingeht (min = Geo-Untergrenze, median = inkl. Queueing für connect-Vorhersage); beide als Sensitivität.
- **Cross-Layer-Brücke ehrlich scopen:** `connect ≈ N×ping` ist nur bei **host-terminierten** Anbietern (n=4) ein nicht-trivialer Beleg; bei Cloudflare-Edge ist die Ping≈connect-Übereinstimmung tautologisch (gleicher Knoten) → aus Stützmenge ausschließen, n offen angeben. (Steht in archivierten Notes bereits korrekt; nur in `setup/` übertragen.)
- **`session_init_ms` als eigene STT-Submetrik:** Lücke `t_first_chunk − t_ws` separat speichern (rev.ai: echter blockierender `connected`-Recv = ≥1 RTT; Azure: `speech.config` fire-and-forget ≈ 0; Deepgram: keine). `ws_upgrade = 1 RTT` entsprechend relativieren, NICHT pauschal „zzgl. Session-Init bei Azure/Rev.ai" (überzeichnet Azure).
- **LLM/TTS-connect-Caveat:** Referenz-connect ist ein Wegwerf-Socket ≠ Mess-Socket → bei Anycast evtl. anderer Edge; `connect_total` ist hier Schätzung, nicht exakt subtrahierbar. Caveat klein halten (cross-provider wird ohnehin connect-inklusiv verglichen) oder echte Mess-Verbindung instrumentieren.

---

## 4) C — Plattform-/EC2-Caveats (macOS ↔ Linux)

- **TLS-Versions-Feld:** macOS-Python = LibreSSL → falsch 1.2; EC2/Ubuntu = OpenSSL 3.x → korrekt. **Kampagne auf EC2, TLS dort verifizieren** (s. A1).
- **`ping -W`:** Linux = Sekunden, macOS = Millisekunden. EC2-`-W 2` korrekt; lokal `-t 5`/`-W 2000`.
- **`traceroute`:** Die 4 dokumentierten Flags (`-n -w -q -m`) sind portabel. Für Cloudflare/Firewall-Ziele auf EC2 zusätzlich **TCP-SYN-traceroute `-T -p 443`** (Linux; macOS nur `-P tcp`) — deckt Azure/Deepgram-Pfade weiter auf als UDP.
- **Interface:** nie literal `ens5`. Als `--iface`-Flag/Auto-Detect (`ip -br link` Linux, `route get default` macOS); tatsächliches Interface in PCAP-Metadaten loggen. Pre-Capture-Sanity-Check (5-s-tcpdump, Paketzähler > 0) vorschreiben. macOS = en0 nur für Dev.
- **sudo/tcpdump:** tcpdump vorhanden, braucht root; N Cold-Start-Calls (normaler User) parallel → Orchestrierung (PID merken, N Calls, SIGTERM, pcap-Flush) als ausführbares Verfahren beschreiben. **`tcpdump -c` von 10000 → 200000** (N≈30 Calls + STT-Audio sprengen 10000 sonst).
- **tshark fehlt lokal:** auf EC2 `apt-get install tshark` einplanen (Layer-2-Analyse).
- **API-Keys:** alle 7 Hosts ohne Key per HTTPS erreichbar (TLS+HTTP schließen durch); appconnect-Zahlen NICHT als RTT verwerten (lokaler Mac). openai gibt `421` auf nacktem `/` (Cloudflare-Edge) — echter `/v1/...`-Pfad mit Host-Header funktioniert.

---

## 5) D — Lücken/Fehlendes (im Setup noch nicht abgedeckt)

- **Zeitbasis/Clock:** `grep ntp|chrony|clock` = 0. Absatz „Zeitbasis" ergänzen: alle Dauer-Metriken aus `perf_counter()`/CLOCK_MONOTONIC → NTP-irrelevant; Wall-Clock-`ts` nur Slot-Label; chrony/Amazon-Time-Sync aktiv + einmal `chronyc tracking` loggen. **Korrektur ggü. Finding:** L2/L3-Eichung vergleicht nur DIFFERENZEN (PCAP `frame.time_relative` vs perf_counter-Diffs) → kein Clock-Confound; Phantom-Slot (A12) ist über `tag`-Gruppierung gelöst, nicht über Drift-Logging.
- **WER (A14) nur halb gelöst:** Roh-Transkript-String wird jetzt gespeichert (gut), aber Referenz-String + Normalisierungsregeln (Casing/Punctuation — Deepgram `punctuate=true` vs Azure!), WER-Tool (`jiwer` fehlt in requirements) und `sample.wav`-Provenienz (menschlich vs. TTS-generiert → sonst zirkulär) fehlen. Zuerst Scope entscheiden (Sekundäranalyse oder bewusste Limitation).
- **Datenbereinigung/Robustheit (niedrig, meist schon implizit):** Ein Satz „kein Warm-up — Cold-Start misst bewusst den ersten Aufbau; Interleaved-RR entschärft Erst-Run-Effekt" + „kein Trimming auf Headline-Zahlen, Tail via p95; Fehlschläge = Verfügbarkeit, kein Outlier".
- **Single Vantage Point (externe Validität):** Als Limitation benennen — „EU-Sicht = gut angebundenes AWS-FRA-RZ, kein Last-Mile; AWS-Peering kann AWS/Cloudflare-Hosts begünstigen (rev.ai = AWS-Oregon, AS16509 = AWS-zu-AWS-Pfad)". Billig: AWS-zu-rev.ai- + einen Cloudflare-Pfad per traceroute/ASN dokumentieren. **Verteidigung:** Azure-STT/TTS-Inversion ist peering-IMMUN (within-provider). Optionaler 2. VP = Future Work.
- **LLM-Region via RTT unmessbar:** openai/groq/**mistral** alle Cloudflare-fronted → RTT misst FRA-Edge, nicht Backend. Besonders mistral (EU-LLM, soll Geo-Achse tragen) ist Edge-maskiert. Als Limitation + Backend-Lokalisierungs-Beleg (TTFT-Untergrenze) führen; STT/TTS-Region ist NICHT maskiert (Azure 12 ms vs US 134–144 ms).
- **Diurnal als erklärende Variable:** Slots werden erfasst, aber nicht als Auswerteachse deklariert. Im Analyseplan: Inversion **pro Slot** auswerten (Vorkampagne: 56/56 robust) — falls sie zu US-Lasthoch kippt, eigener Befund.
- **E2E-Auswerteschritt:** Monte-Carlo-Faltung statt Median-Addition (p50/p90/p95+CI) + Joint-Completion-Pareto-Front (Latenz vs. Zuverlässigkeit) als Pflicht-Output verankern; „Gewinner" erst nach der Front (Groq schnell, aber ~33 % Ausfall).

---

## 6) E — Was solide ist (bleibt)

- **TCP-Ping als primäre RTT-Metrik:** funktioniert für alle 7/9 Hosts (5/5 OK), inkl. ICMP-Verweigerer rev.ai; `socket.create_connection` misst sauber genau 1 RTT (TLS NICHT enthalten, via curl-Phasen verifiziert). DNS-vorab-Auflösung korrekt.
- **curl-Phasen-Logik:** für alle 7 monoton (dns<tcp<tls<ttfb<total); `tls_handshake = appconnect − connect` korrekt; alle h2/ALPN.
- **ASN-/Edge-Ansatz:** reine Bordmittel, EC2-reproduzierbar; Cloudflare-Gruppierung (AS13335 für openai/groq/mistral) empirisch hart belegt; stützt C1/C2.
- **Submetrik-Zerlegung (Soll):** `dns/tcp/tls/ws` roh + `connect_total` abgeleitet — in `messprotokoll.md` korrekt spezifiziert (nur STT-WS-Pfad braucht manuelle Instrumentierung statt `websockets.connect`-One-Shot).
- **E2E-Doppelzähl-Logik:** `stt_connect+stt_ttft+llm_ttft+tts_ttfa` zählt connect nachweislich NICHT doppelt (gegen Code geprüft, kohärent).
- **Kampagnen-Design:** Interleaved/Round-Robin mit Rotation + `round`-Index + Fehler-markieren-und-weiter ist in `messprotokoll.md:272-284` bereits korrekt entschieden (Alt-Runner war batchweise — nur Referenz).
- **Confound-Bewusstsein:** Region/Engine-Konfundierung ist als Limitation bewusst eingegangen; die Within-Provider-STT/TTS-Inversion (Azure, Region konstant) ist die quasi-experimentelle Kontrolle und peering-/RTT-immun → C1 robust.
- **Anycast/Edge-Caveat** existiert bereits in `messprotokoll.md:58-63` (nur Co-Location in den Layer-3-Abschnitt fehlt — A3/B).

**Kernhinweis für den Skript-Bau:** Die alten `archived/measurements/`-Skripte NICHT als Vorlage kopieren (n=1-PCAP-Annahme, `token_count`=Chunks, nur Differenzen, kein round-Index, `transcript_len` statt String) — das neue `messprotokoll.md` schreibt durchweg das Richtige vor; die archivierten „kritisch"-Findings sind erledigt, sobald der neue Code dem Doc folgt.
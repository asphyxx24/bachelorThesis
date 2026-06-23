# HANDOFF — Stand 2026-06-19 (hier einsteigen)

> Kurz-Einstieg: Die **Messkampagne ist abgeschlossen** (EC2, Vollkampagne 56/56 Slots gelandet). Nur
> **Layer 3** läuft slotweise (8×/Tag); **Layer 1 war eine einmalige Momentaufnahme (16.6.)**, kein Slot-Betrieb.
> Die **Messmethodik ist im Kern valide**, aber der **Ultracode-Voll-Audit vom 2026-06-18** (72 Agenten, Urteil
> **GO-mit-Auflagen**, 85 Befunde) hat Doku-/Reporting-Korrekturen aufgedeckt, die VOR der Auswertung sitzen
> müssen (s. §4) — durchweg **Doku/Reporting, KEINE Neumessungen**. **Erledigt seither:** Campaign-Check,
> Arbeitstitel-Kandidaten (`notes/arbeitstitel.md`), Zweitprüfer-Anfrage an Prof. Färber **raus**, Doku-/Tracking-Review
> (IP-Feld-Regel reconciled, C1 → „Backend statt Geografie", Azure-TTS ~94 ms), **L1-RTT- + ASN-Lücken am 19.6.
> aus vorhandenen Daten geschlossen** (kein Neumessen), H1–H4 in den Docs eingearbeitet. **Jetzt dran:**
> Arbeitstitel final wählen, **Datenaufbereitung, Statistik gegenprüfen, Interpretation, Prof-Folien.**

---

## 1. Was JETZT läuft (nichts tun nötig)

- **Layer-3-Kampagne** auf EC2 `i-0f8f6d2414cecebb8` (c6i.large, eu-central-1b, Frankfurt), Code **`f9e6dc8`**
  (Branch `neuaufbau-layer1`, gepusht) — **eingefroren** für den Rest der Kampagne.
- **cron:** 8 UTC-Slots/Tag (00/03/06/09/12/15/18/21h), je `run.py --n 100` über alle 9 Endpunkte interleaved.
- **Nur Layer 3 ist slotgetrieben.** Layer 1 (RTT/DNS/ASN/Traceroute/TLS) + Layer 2 (Handshake-Eichung) waren
  **einmalige** EC2-Läufe am 16.6.
- **Ziel:** 7 Tage = 56 Slots = 5.600/Endpunkt = 50.400 Calls. **Kampagne beendet: Vollkampagne (56/56) Slots gelandet (A4-Basis).**
- **Zugang:** `ssh -i ~/.ssh/thesis-ec2 ubuntu@<IP>` — IP wechselt bei stop/start, zuletzt `3.70.215.163`.
  Aktuelle IP: `.venv/bin/aws ec2 describe-instances --region eu-central-1 --instance-ids i-0f8f6d2414cecebb8 --query 'Reservations[].Instances[].PublicIpAddress' --output text`

**Täglicher Check:**
```bash
ssh -i ~/.ssh/thesis-ec2 ubuntu@<IP> 'ls ~/thesis/data/layer3/campaign/*.jsonl | wc -l; tail -3 ~/thesis/data/layer3/cron.log'
```
→ Slot-Zahl ~+8/Tag. **Rev.ai-Guthaben** im Blick behalten (~2.040 min geladen, ~1.400 nötig).

---

## 2. Was abgesichert ist (Messmethodik)

Gegen Rohdaten (n=200 bzw. volle Kampagne) nachgerechnet + paket-geeicht:

- **Instrument geeicht (Layer 2, echt, NUR Connect-Timer):** App-`tcp_handshake_ms` = Wire-SYN→SYN-ACK
  gerichtet **+0,11 ms** (Median, Azure 11 ms, 30/30) bzw. **+0,12 ms** (Deepgram 139 ms, 28/30; 2 am
  Capture-Fensterrand verloren; idx0-Cold-Start-Outlier ausgeschlossen) → der **Connect-Timer** ist
  paket-validiert (C2). **Wichtig (Audit H2):** `ttft`/`ttfa` nutzen denselben `perf_counter`-Mechanismus,
  starten aber erst beim Request-Absenden im httpx/websockets-Stack → **nicht direkt paket-geeicht**. Nicht als
  „alle L3-Zahlen geeicht" formulieren. Code: `measurements/layer2/{capture.py,analyze.py}`; Belege `data/layer2/`.
- **Clock:** chrony sub-µs → ms-Timing belastbar.
- **STT:** `ttfp` (Time-to-first-Partial) primär, 1×-Realtime-Pacing + paralleler Empfang; `ttft`=Stream-Ende-Final sekundär.
- **LLM:** F2 (`output_tokens` via `stream_options`, 200/200) + F3 (Erfolg inhaltlich). Modell-Pinning sauber.
- **TTS:** mp3-Container gepinnt (Bitrate NICHT → `ttfa` fair, `total`/`audio_bytes` nicht). Verfügbarkeit eigene Achse.
- **Quer:** IPv4 erzwungen, Cold-Start/kein-Pooling belegt, cpu_steal flach (kein Throttling), `git_dirty=False`.

Vier Audit-Runden: 23 → 62 → 85 Befunde (Methodik-Audit 16.6., alle gefixt), dann **Voll-Audit 2026-06-18**
(72 Agenten, 85 neue Befunde, Urteil **GO-mit-Auflagen**) → H1–H4 in den Docs eingearbeitet (s. §4). Maßgebliches
Voll-Urteil: `data/audit_20260618/VERDICT.md` (gitignored); Belege `data/audit_20260618/{l1_rtt_per_ip.md,asn_per_ip.md}`.

---

## 3. C1-Stand (für Interpretation/Folien — nicht wieder kippen lassen)

**C1 — „Backend statt Geografie"** ruht jetzt auf:
1. **Kernbeleg — LLM @ identischer Edge-RTT:** OpenAI/Groq/Mistral terminieren ALLE bei Cloudflare FRA. Seit 19.6.
   **für 100 % des LLM-Traffics gemessen + ASN-belegt** (je Host 2 CF-IPs ~50/50, alle AS13335 @ ~1 ms; Belege
   `data/audit_20260618/{l1_rtt_per_ip.md,asn_per_ip.md}`; RTT alle ~1 ms: groq 1,3 / mistral 1,1 / openai 1,2 ms).
   `ttft` streut dennoch (Voll-Kampagne, 56 von 56 Slots, A4 = Median der Slot-Mediane, success-only):
   **~67 → 279 → 487 ms ≈ 7,3×** (gepoolt 8,3×; groq<mistral<openai; Bootstrap-CI noch ausstehend).
   **Per-IP invariant**, Geografie sogar **invertiert** (EU-Mistral langsamer als US-Groq). HINWEIS (Audit H1):
   die früher zitierten **75/268/476 ms** sind der Predeploy-Pilot (n=200, 2 Slots) und reproduzieren aus keinem
   Kampagnen-Datensatz — daher die Voll-Kampagnen-Zahlen führen. Der finale Faktor (~7,3×, gepoolt 8,3×) ist sogar
   GRÖSSER als der Pilot — Ordnung identisch, der Kernbefund wird dadurch STÄRKER.
2. **2. Beleg:** Azure **schnellstes TTS** (`ttfa` ~94 ms). „Trotz US-Konkurrenz" gilt sauber nur gegenüber
   **Deepgram** (~280 ms connect, echter US-Transit; `ttfa` ~516 ms). **OpenAI-TTS terminiert ebenfalls bei Cloudflare FRA**
   (gleiche IPs wie LLM-OpenAI, AS13335, ~1 ms connect — selber Edge wie LLM-OpenAI) → zweite identical-edge-Instanz
   (`ttfa` ~942 ms, connect-exkl. ~941 ms = reines Backend) und **stärkt C1** (Audit M2).
3. **STT:** ehrlich — kein Engine-Beleg (auf `ttfp` ist Azure nicht langsamster; alte „1722 ms = Endpointing"-These war Dump-Bulk-Compute, gestrichen).

> ⚠️ **Interpretations-Kompass:** Die **wasserdichte** Aussage ist die NEGATIVE: „Netznähe erklärt die
> Spreizung nicht". Der Schritt zu „Backend" trägt den **Modellgrößen-Confound** (Groq = kleinstes Modell UND
> spezielle HW). Formulieren als **„Backend (HW+Modell) statt Geografie"**, nicht „Engine-Rechenleistung allein".
> (Deshalb „Engine/Backend" NICHT im Arbeitstitel — s. `notes/arbeitstitel.md`.)

---

## 4. Offene Audit-Auflagen vor der Auswertung (2026-06-18, alle nur Doku/Reporting)

> Vor der ersten Statistik/Interpretation/Folie beachten. C1 ist inhaltlich von keinem Punkt bedroht (Ordnung
> invariant). Voll-Liste: `data/audit_20260618/VERDICT.md`. **In den lebenden Docs am 19.6. bereits eingearbeitet:**
> H1-Zahlen (56 von 56 Slots, A4), H2-Eichungsreichweite, H4-L1-Quelle, ttl_ms; **noch in der Analyse zu beachten:**

- **H1 — Headline-Zahlen:** 75/268/476 ms = Predeploy-Pilot, nicht reproduzierbar; Voll-Kampagne (56 von 56 Slots, A4,
  success-only) ~67/279/487 ms (~7,3×, gepoolt 8,3×). Finale Zahlen eingesetzt; Bootstrap-CI noch ausstehend.
- **H2 — Eichungs-Reichweite:** nur Connect-Timer paket-validiert; ttft/ttfa gleicher Mechanismus, nicht direkt geeicht.
- **H3 — Fehler-Filter:** Es gibt **kein** `error_kind`-Enum (F4 existiert nicht im Code). Filter `error=='timeout'`
  verfehlt die echten Timeouts. Roh-String per Teilstring bucketieren (173× `ReadTimeout`=tts_openai [3,1 %, 173/5600],
  22× `http_503`=mistral) VOR jeder Failure-Gruppierung; Mapping dokumentieren.
- **H4 — L1-Datensatz:** `data/layer1/` im Repo ist macOS-Dev-Lauf (~17–21 ms), NICHT EC2 (~1 ms). In der
  Auswertung nur EC2-L1 (ts 2026-06-16) bzw. `l1_rtt_per_ip.md` nutzen.
- **M1 — E2E-Formel:** sequenzielle Pipeline braucht `connect_total + stt_ttft` (LLM startet erst auf finalem
  Transkript). ttfp-Summe unterschätzt STT um ~3,7–3,9 s → nur als „STT-Standalone-Responsiveness".
- **`ttl_ms`:** existiert nicht in Code/Daten → durch `total_ms` bzw. `(total−ttft)/output_tokens` ersetzen.

L1-RTT-/ASN-Lücken am 19.6. aus vorhandenen Daten geschlossen (kein Neumessen): LLM/tts_openai 100 % AS13335
Cloudflare @ ~1 ms; Deepgram Multi-DC = Zayo AS6461 ×3 + Cogent AS174 ×3 (beide US; Slow-Mode-DC Cogent hat die
*niedrigere* RTT ~101 ms → langsamer Mode = Backend, nicht Netz); rev.ai 3× AWS AS16509 ~140 ms; Azure AS8075 ~11 ms.
Eingearbeitet in `api_endpunkte.md` + `messprotokoll.md`.

---

## 5. To-dos (in dieser Reihenfolge)

> **Auswertungs-Disziplin (sonst kippt's beim Schreiben):**
> - **IP-Feld:** Region/ASN/Verfügbarkeit/connect → `connect.resolved_ip` (nie null); L3↔L1-RTT-Brücke → top-level
>   `resolved_ip`, nur bei Feld-Gleichheit. Fails NIE über top-level==null filtern. SSOT: `messprotokoll.md` → „Welches IP-Feld wofür".
> - **Layer-1 nur EC2 (H4):** `data/layer1/` im Repo = macOS-Dev-Lauf, nicht EC2. Nur EC2-Snapshot bzw. `l1_rtt_per_ip.md`.
> - **`ttl_ms` NICHT verwenden** — existiert nicht; Pro-Token-Rate über `(total−ttft)/output_tokens`.
> - **Fehler-/Timeout-Filter:** NICHT `error=='timeout'`. Roh-String per Teilstring (`ReadTimeout`) bucketieren.
> - **OpenAI-TTS-Fail-Rate real 3,1 %** (173/5600; Pre-Header-Hänger ~30 s; Audit M10). Latenz nur success-only;
>   jedes Quantil oberhalb 3,1 % bleibt zensiert (Survivorship-/Asterisk-Caveat gilt unverändert).
> - **C1:** groq sauber disjunkt; **mistral<openai nur Median-Ordnung** (Tails überlappen) → Mann-Whitney/Bootstrap.
> - **Diurnal (56/56 Slots, Tag×Slot nicht-orthogonal)** — Tageszeit-Inferenz weiterhin vorsichtig (nicht-orthogonales
>   Design, keine vollen 7×8). **Deepgram-`ttfp` nach `ttfp_text` stratifizieren** (Mix „Good"/„Good morning" UTC-strukturiert, corr=0,915; Audit M9).
> - **`total_ms` längenabhängig** → `ttft`/`ttfa` primär. **Code eingefroren (f9e6dc8).**

0. **Audit-Auflagen H1–H4 + M1 + ttl_ms — Doku-Teil erledigt (19.6.); in der Analyse weiter beachten (s. §4).**
1. **Arbeitstitel final wählen** (`notes/arbeitstitel.md`) und dem Betreuer vorlegen.
2. *(optional, durch die Mail terminiert)* **Einseitiges Exposé/Methodik-Onepager**, falls Färber zusagt.
3. **Datenaufbereitung:** Slots von EC2 ziehen (zuletzt `data/audit_20260618/ec2_data/`); Auswerte-Notebook/Skript bauen.
4. **Statistik sauber + GEMEINSAM gegenprüfen** (nächste ungeprüfte Fehlerfläche): Aggregation **A4** (Median der
   Slot-Mediane) + **Bootstrap-95%-CI**; Perzentile slot-aufgelöst; Verfügbarkeit eigene Achse; Mann-Whitney/Bootstrap
   für „X schneller als Y". Regeln: `setup/messprotokoll.md` §Aggregation (A4).
5. **Erste Interpretation** entlang §3 (mit dem Kompass-Caveat).
6. **LaTeX-Folien für den Prof:** (i) 3-Schichten + Layer-2-Eichung (Connect-Timer!), (ii) Edge/Host-Klassifikation (C2),
   (iii) C1-Kernbeleg LLM-Edge, (iv) ehrliche Limitationen.

**Später (kein Blocker):**
- Richere Layer-2-Analyse (IAT/Retransmits während echter Calls) — Eichung selbst steht.
- WER/Transkriptqualität: `sample.wav`-Provenienz (A14), Latenz ≠ Qualität als Out-of-Scope.
- **~23.6.: `crontab -r` + Instanz `i-0f8f6d2414cecebb8` stoppen** (Kosten). Danach Aufräum-Reminder `NEUANFANG.md §7`
  (AWS-Key löschen, Console-PW, Validierungs-Instanz `i-045a2d0eeb338b290`).

---

## 6. Wichtige Dateien

| Datei | Inhalt |
|-------|--------|
| `notes/` | Arbeits-/Korrespondenz-Ordner: Arbeitsplan, Titel-Kandidaten, Mail-Entwürfe, Exposé (md/html/pdf) |
| `notes/arbeitstitel.md` | Titel-Kandidaten (Favorit + 2 Alternativen) — finale Wahl steht aus |
| `notes/zweitpruefer_anfrage.md` | Versandte Zweitprüfer-Anfrage an Prof. Färber + Fit-Kontext |
| `setup/messprotokoll.md` | Methodik (3 Layer, Metriken, **IP-Feld-Regel reconciled**, Aggregation A4, C1-Logik) |
| `data/audit_20260618/VERDICT.md` | **Maßgebliches** Voll-Urteil (72 Agenten, GO-mit-Auflagen, H1–H4) |
| `data/audit_20260618/l1_rtt_per_ip.md` | RTT je produktiv getroffener IP (L1-Lücke geschlossen, 100 % Traffic) |
| `data/audit_20260618/asn_per_ip.md` | ASN je IP (Edge-/Multi-DC-Beleg) |
| `data/audit_20260618/ec2_data/` | Roh-Pull der Kampagne (L1/L2/Logs) — gitignored |
| `data/audit_20260616/VERDICT.md` | Methodik-Voll-Audit (3 Runden, historisch) |
| `setup/deployment.md` | EC2-Betrieb, prüfen/stoppen |
| `NEUANFANG.md` | Lebende Referenz |

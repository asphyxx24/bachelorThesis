# HANDOFF — Stand 2026-06-18 (hier einsteigen)

> Kurz-Einstieg: Die **Messkampagne läuft** (EC2, unabhängig, Check 18.6. sauber). Die **Messmethodik
> ist abgesichert** (3× ultracode-auditiert + Layer-2-geeicht + Daten-Audit Tag 1). **Erledigt seither:**
> Campaign-Check, Arbeitstitel-Kandidaten (`arbeitstitel.md`), Zweitprüfer-Anfrage an Prof. Färber
> **raus**, Doku-/Tracking-Review (IP-Feld-Regel reconciled, C1 umbenannt, Zahl-Fix). **Jetzt dran:**
> Arbeitstitel final wählen, **Datenaufbereitung, Statistik gegenprüfen, Interpretation, Prof-Folien.**

---

## 1. Was JETZT läuft (nichts tun nötig)

- **Layer-3-Kampagne** auf EC2 `i-0f8f6d2414cecebb8` (c6i.large, eu-central-1b, Frankfurt), Code **`f9e6dc8`**
  (Branch `neuaufbau-layer1`, auf GitHub gepusht) — **eingefroren** für den Rest der Kampagne.
- **cron:** 8 UTC-Slots/Tag (00/03/06/09/12/15/18/21h), je `run.py --n 100` über alle 9 Endpunkte interleaved.
- **Ziel:** 7 Tage = 56 Slots = 5.600/Endpunkt = 50.400 Calls. **Stop-Termin ~2026-06-23.**
- **Zugang:** `ssh -i ~/.ssh/thesis-ec2 ubuntu@<IP>` — IP wechselt bei stop/start, zuletzt `3.70.215.163`.
  Aktuelle IP: `.venv/bin/aws ec2 describe-instances --region eu-central-1 --instance-ids i-0f8f6d2414cecebb8 --query 'Reservations[].Instances[].PublicIpAddress' --output text`

**Täglicher Check (1 Befehl):**
```bash
ssh -i ~/.ssh/thesis-ec2 ubuntu@<IP> 'ls ~/thesis/data/layer3/campaign/*.jsonl | wc -l; tail -3 ~/thesis/data/layer3/cron.log'
```
→ Slot-Zahl sollte ~+8/Tag wachsen. **Rev.ai-Guthaben** im Dashboard im Blick behalten (~2.040 min geladen,
~1.400 nötig — der einzige Verbrauchsstoff, der leerlaufen könnte).

---

## 2. Was abgesichert ist (Messmethodik — der Teil, der laufen muss)

Selbst gegen Rohdaten (n=200) nachgerechnet + paket-geeicht:

- **Instrument geeicht (Layer 2, echt):** App-`tcp_handshake_ms` = Wire-SYN→SYN-ACK auf **±0,1 ms**
  (Azure 11 ms: +0,11 / Deepgram 139 ms: +0,12, je N=30). → Layer-3-Timer am Paket-Level validiert (C2).
  Code: `measurements/layer2/{capture.py,analyze.py}`; Belege `data/layer2/`.
- **Clock:** chrony sub-µs (System time ~1,3 µs) → ms-Timing belastbar.
- **STT:** `ttfp` (Time-to-first-Partial) primär, **1×-Realtime-Pacing** + paralleler Empfang; `ttft` = Stream-Ende-Final sekundär. `ttfp_is_final=0/200` (echte Interims).
- **LLM:** F2 (`output_tokens` via `stream_options`, 200/200) + F3 (Erfolg inhaltlich). Modell-Pinning sauber.
- **TTS:** mp3-Container gepinnt (Bitrate NICHT → `ttfa` fair, `total`/`audio_bytes` nicht). Verfügbarkeit eigene Achse.
- **Quer:** IPv4 erzwungen (0 IPv6/3584), Cold-Start/kein-Pooling belegt, cpu_steal +4/Slot (kein Throttling), `git_dirty=False`.

**Konfidenz Messmethodik: ~92 %** (Instrument ~96 %, Interpretation ~83 %, Analyse noch nicht ausgeführt).
3 Audits: 23 → 62 → 85 Befunde, alle gefixt. Voll-Urteil: `data/audit_20260616/VERDICT.md`.

---

## 3. C1-Stand (für Interpretation/Folien — wichtig, nicht wieder kippen lassen)

**C1 — „Backend statt Geografie"** ruht jetzt auf:
1. **Kernbeleg — LLM @ identischer Edge-RTT:** OpenAI/Groq/Mistral terminieren ALLE bei Cloudflare FRA
   (~1 ms RTT, ASN 13335), aber `ttft` = **75 → 268 → 476 ms ≈ 6,4×** (n=200, paced). **Per-IP invariant**,
   Geografie sogar **invertiert** (EU-Mistral 3,6× langsamer als US-Groq).
2. **2. Beleg:** Azure **schnellstes TTS** (`ttfa` ~94 ms) trotz US-Konkurrenz.
3. **STT:** ehrlich — kein Engine-Beleg (auf `ttfp` ist Azure nicht langsamster; alte „1722 ms = Endpointing"-These war Dump-Bulk-Compute, gestrichen).

> ⚠️ **Interpretations-Kompass:** Die **wasserdichte** Aussage ist die NEGATIVE: „Netznähe erklärt die
> Spreizung nicht". Der Schritt zu „Engine" trägt den **Modellgrößen-Confound** (Groq = kleinstes Modell
> UND spezielle HW). Formulieren als **„Backend (HW+Modell) statt Geografie"**, nicht „Engine-Rechenleistung
> allein". Das ist der Punkt, an dem Prof. Wählisch sonst nachhakt. (Deshalb auch „Engine/Backend" NICHT im
> Arbeitstitel — s. `arbeitstitel.md`.)

---

## 4. To-dos

> **Daten-Audit Tag 1 (17.6.) erledigt → Datensatz VERTRAUENSWÜRDIG** (6 Slots, 5.400 Calls, 0 Wertfehler;
> C1 hält diurnal; Anomalien providerseitig erklärt). Voll-Urteil: `data/audit_20260617/VERDICT.md`.
> **Auswertungs-Disziplin (sonst kippt's beim Schreiben — unbedingt beachten):**
> - **IP-Feld:** für **Region/ASN/Verfügbarkeit/connect** → `connect.resolved_ip` (nie null); für die
>   **L3↔L1-RTT-Brücke** → top-level `resolved_ip`, nur bei Feld-Gleichheit. Fails NIE über top-level==null
>   filtern. Single Source of Truth: `setup/messprotokoll.md` → „Welches IP-Feld wofür (reconciled)".
> - **Verfügbarkeit getrennt von Latenz** (Latenz nur success-only; OpenAI-TTS ~88 % + Mistral-03h-n=78 als eigene Achse).
> - **C1:** groq sauber disjunkt; **mistral<openai nur Median-Ordnung** (Tails überlappen) → Mann-Whitney/Bootstrap, nicht „getrennte Verteilungen". Spread 6,2–7,8× = diurnal variierend, keine Konstante.
> - **Diurnal = Snapshot (6/56 Slots)** — noch keine Tageszeit-Inferenz; volle Kampagne abwarten.
> - **`total_ms` längenabhängig** → `ttft`/`ttfa` primär.
> - **Code für Rest der Kampagne einfrieren (f9e6dc8)**; 30-s-Read-Timeout (`config.RESPONSE_TIMEOUT_S`) ≠ 75-s-Hard-Timeout.

**Erledigt (17.–18.6.):**
- ✅ **Campaign-Check** — läuft sauber, Slots wachsen, cron pünktlich.
- ✅ **Arbeitstitel-Kandidaten** ausgearbeitet → `arbeitstitel.md` (Favorit + 2 Alternativen; Linie:
  neutral-deskriptiv, Rigor-Signal, „Engine/Backend" NICHT im Titel). **Offen: finale Wahl + dem Betreuer vorlegen.**
- ✅ **Zweitprüfer-Anfrage an Prof. Michael Färber raus** (`zweitpruefer_anfrage.md`; Kaltanfrage auf
  Wählischs Anregung, er als Erstprüfer genannt). **Offen: Antwort abwarten** — bietet einseitiges Exposé an.
- ✅ **Doku-/Tracking-Review** (18.6.): IP-Feld-Regel reconciled (messprotokoll), C1 → „Backend statt
  Geografie" umbenannt, Azure-TTS-Zahl in CLAUDE.md auf ~94 ms korrigiert.

**Als Nächstes (in dieser Reihenfolge):**
1. **Arbeitstitel final wählen** (`arbeitstitel.md`) und dem Betreuer vorlegen.
2. *(optional, durch die Mail terminiert)* **Einseitiges Exposé/Methodik-Onepager** vorbereiten, falls Färber zusagt.
3. **Datenaufbereitung starten:** Slots von EC2 ziehen; Auswerte-Notebook/Skript bauen (Code bleibt `f9e6dc8`).
4. **Statistik sauber ausführen + GEMEINSAM gegenprüfen** (= die nächste ungeprüfte Fehlerfläche):
   Aggregation **A4** (Median der Slot-Mediane, nicht gepoolt) + **Bootstrap-95%-CI**; Perzentile (p50/p90
   slot-aufgelöst, p95/p99 nur gepoolt); Verfügbarkeit als eigene Achse; Differenz-Bootstrap/Mann-Whitney
   für „X schneller als Y". Regeln stehen in `setup/messprotokoll.md` §Aggregation (A4).
5. **Erste Interpretation** entlang §3 (mit dem Kompass-Caveat).
6. **LaTeX-Folien für den Prof:** Story = (i) 3-Schichten-Methodik + **Layer-2-Eichung** (beantwortet sein
   Datenvertrauen!), (ii) Edge/Host-Klassifikation (C2), (iii) C1-Kernbeleg LLM-Edge, (iv) ehrliche Limitationen.

**Später in der Woche (kein Blocker):**
- Richere Layer-2-Analyse (IAT/Retransmits aus PCAPs *während* echter API-Calls) — Eichung selbst steht schon.
- WER/Transkriptqualität: `sample.wav`-Provenienz klären (A14), Rev.ai „Frankford"-Fehler → Latenz ≠ Qualität explizit als Out-of-Scope.
- **~23.6.: `crontab -r` + Instanz stoppen.** Danach Aufräum-Reminder aus `NEUANFANG.md §7` (AWS-Key löschen,
  Console-PW, Validierungs-Instanz `i-045a2d0eeb338b290` prüfen).

---

## 5. Wichtige Dateien

| Datei | Inhalt |
|-------|--------|
| `arbeitstitel.md` | Titel-Kandidaten (Favorit + 2 Alternativen) — finale Wahl steht aus |
| `zweitpruefer_anfrage.md` | Versandte Zweitprüfer-Anfrage an Prof. Färber + Fit-Kontext |
| `setup/messprotokoll.md` | Methodik (alle 3 Layer, Metriken, **IP-Feld-Regel reconciled**, Aggregation A4, C1-Logik) |
| `data/audit_20260616/VERDICT.md` | Voll-Audit-Urteil + alle Befunde/Fixes |
| `data/audit_20260616/SUMMARY_real.txt` | Aggregierte n=200-Echtzahlen (LLM/TTS/STT + AWS + L1) |
| `data/audit_20260617/VERDICT.md` | Daten-Audit Tag 1 (Vertrauenswürdigkeit + Auswertungs-Disziplin) |
| `data/layer2/` | PCAPs + Eichungs-Logs |
| `setup/deployment.md` | EC2-Betrieb, prüfen/stoppen |
| `NEUANFANG.md` | Lebende Referenz |

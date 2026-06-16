# HANDOFF — Stand 2026-06-16 Abend (hier morgen einsteigen)

> Kurz-Einstieg: Die **Messkampagne läuft** (EC2, unabhängig). Die **Messmethodik ist abgesichert**
> (3× ultracode-auditiert + Layer-2-geeicht). Morgen geht es an **Datenaufbereitung, Statistik, Prof-Folien,
> erste Interpretation — und mehrere Arbeitstitel ausarbeiten.** Details unten.

---

## 1. Was JETZT läuft (nichts tun nötig)

- **Layer-3-Kampagne** auf EC2 `i-0f8f6d2414cecebb8` (c6i.large, eu-central-1b, Frankfurt), Code **`f9e6dc8`**
  (Branch `neuaufbau-layer1`, auf GitHub gepusht).
- **cron:** 8 UTC-Slots/Tag (00/03/06/09/12/15/18/21h), je `run.py --n 100` über alle 9 Endpunkte interleaved.
- **Ziel:** 7 Tage = 56 Slots = 5.600/Endpunkt = 50.400 Calls. **Stop-Termin ~2026-06-23.**
- **Bisher gelandet:** 12h/15h/18h-Slots, ~99 % Erfolg (891–893/900). Disk 18 % belegt. cron feuert pünktlich.
- **Zugang:** `ssh -i ~/.ssh/thesis-ec2 ubuntu@<IP>` — IP wechselt bei stop/start, aktuell `3.70.215.163`.
  Aktuelle IP: `.venv/bin/aws ec2 describe-instances --region eu-central-1 --instance-ids i-0f8f6d2414cecebb8 --query 'Reservations[].Instances[].PublicIpAddress' --output text`

**Morgen-Früh-Check (1 Befehl):**
```bash
ssh -i ~/.ssh/thesis-ec2 ubuntu@3.70.215.163 'ls ~/thesis/data/layer3/campaign/*.jsonl | wc -l; tail -3 ~/thesis/data/layer3/cron.log'
```
→ Slot-Zahl sollte gewachsen sein (~+6–8 über Nacht). **Rev.ai-Guthaben** kurz im Dashboard prüfen
(~2.040 min geladen, ~1.400 nötig — sollte reichen, ist aber der einzige Verbrauchsstoff, der leerlaufen könnte).

---

## 2. Was abgesichert ist (Messmethodik — der Teil, der laufen muss)

Selbst gegen Rohdaten (n=200) nachgerechnet + paket-geeicht:

- **Instrument geeicht (Layer 2, NEU & echt):** App-`tcp_handshake_ms` = Wire-SYN→SYN-ACK auf **±0,1 ms**
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

**„Engine/Backend schlägt Geografie"** ruht jetzt auf:
1. **Kernbeleg — LLM @ identischer Edge-RTT:** OpenAI/Groq/Mistral terminieren ALLE bei Cloudflare FRA
   (~1 ms RTT, ASN 13335), aber `ttft` = **75 → 268 → 476 ms ≈ 6,4×** (n=200, paced). **Per-IP invariant**,
   Geografie sogar **invertiert** (EU-Mistral 3,6× langsamer als US-Groq).
2. **2. Beleg:** Azure **schnellstes TTS** (`ttfa` ~94 ms) trotz US-Konkurrenz.
3. **STT:** ehrlich — kein Engine-Beleg (auf `ttfp` ist Azure nicht langsamster; alte „1722 ms = Endpointing"-These war Dump-Bulk-Compute, gestrichen).

> ⚠️ **Interpretations-Kompass:** Die **wasserdichte** Aussage ist die NEGATIVE: „Netznähe erklärt die
> Spreizung nicht". Der Schritt zu „Engine" trägt den **Modellgrößen-Confound** (Groq = kleinstes Modell
> UND spezielle HW). Formulieren als **„Backend (HW+Modell) statt Geografie"**, nicht „Engine-Rechenleistung
> allein". Das ist der Punkt, an dem Prof. Wählisch sonst nachhakt.

---

## 4. MORGEN — konkrete To-dos (in dieser Reihenfolge)

1. **Campaign-Check** (s. §1) — Slots gewachsen? Rev.ai-Guthaben ok? Fehler in cron.log?
2. **Mehrere Arbeitstitel ausarbeiten** (ausdrücklich gewünscht). Aktueller Platzhalter:
   *„Engine schlägt Geografie: Netzwerk-, Protokoll- und Latenzanalyse kommerzieller Cloud-AI-APIs einer
   Echtzeit-Voice-Pipeline aus EU-Perspektive."* Morgen 3–5 Varianten entwickeln, die den geschärften
   C1-Kern (LLM-Edge / „Backend statt Geografie") + die 3-Schichten-Methodik + Eichung tragen.
   Mögliche Achsen: (a) Befund-betont („Backend schlägt Geografie…"), (b) methodik-betont
   („Drei-Schichten-Messmethodik für…"), (c) nüchtern-deskriptiv. → mit Anton entscheiden.
3. **Datenaufbereitung starten:** Slots von EC2 ziehen; Auswerte-Notebook/Skript bauen.
4. **Statistik sauber ausführen + GEMEINSAM gegenprüfen** (= die nächste ungeprüfte Fehlerfläche):
   Aggregation **A4** (Median der Slot-Mediane, nicht gepoolt) + **Bootstrap-95%-CI**; Perzentile (p50/p90
   slot-aufgelöst, p95/p99 nur gepoolt); Verfügbarkeit als eigene Achse; Differenz-Bootstrap/Mann-Whitney
   für „X schneller als Y". Regeln stehen in `setup/messprotokoll.md` §Aggregation (A4).
5. **Erste Interpretation** entlang §3 (mit dem Kompass-Caveat).
6. **LaTeX-Folien für den Prof:** Story = (i) 3-Schichten-Methodik + **Layer-2-Eichung** (beantwortet sein
   Datenvertrauen!), (ii) Edge/Host-Klassifikation (C2), (iii) C1-Kernbeleg LLM-Edge, (iv) ehrliche Limitationen.

**Später in der Woche (kein Blocker für morgen):**
- Richere Layer-2-Analyse (IAT/Retransmits aus PCAPs *während* echter API-Calls) — Eichung selbst steht schon.
- WER/Transkriptqualität: `sample.wav`-Provenienz klären (A14), Rev.ai „Frankford"-Fehler → Latenz ≠ Qualität explizit als Out-of-Scope.
- ~23.6.: `crontab -r` + Instanz stoppen.

---

## 5. Wichtige Dateien für morgen

| Datei | Inhalt |
|-------|--------|
| `data/audit_20260616/VERDICT.md` | Voll-Audit-Urteil + alle Befunde/Fixes |
| `data/audit_20260616/SUMMARY_real.txt` | Aggregierte n=200-Echtzahlen (LLM/TTS/STT + AWS + L1) |
| `data/audit_20260616/real_slots/` | Roh-Slots 12h/15h (n=100×9, paced) |
| `data/layer2/` | PCAPs + Eichungs-Logs |
| `setup/messprotokoll.md` | Methodik (alle 3 Layer, Metriken, Aggregation A4, C1-Logik) |
| `setup/deployment.md` | EC2-Betrieb, prüfen/stoppen |
| `NEUANFANG.md` | Lebende Referenz |

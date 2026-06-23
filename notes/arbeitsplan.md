# Arbeitsplan — Bachelorarbeit (lebendes Aufgaben-Dokument)

> **Zweck:** Damit nichts im Chat verloren geht. Hier steht, was **noch** zu tun ist, in welcher
> Reihenfolge. Ergänzt (ersetzt nicht) `../HANDOFF.md` (Session-Einstieg) und `../NEUANFANG.md` (Referenz).
>
> **Leitziel über allem:** Anton muss bei der Wählisch-Konsultation **alles selbst erklären können** —
> Setup, Skripte, Methodik, Ergebnisse. Der Code muss nicht selbst geschrieben sein, aber die Methodik
> *verteidigt* werden. Deshalb hat **Block B (Erklärbarkeit)** Vorrang.

**Status-Legende:** ☐ offen · ◐ in Arbeit · ☑ erledigt · ⏸ später/Blocker
**Stand:** 2026-06-23 — Folien komplett, Finale-Zahlen-Sweep durch (Vollkampagne, abgeschlossen (56/56), A4). Nächster Brocken:
**Block B (Erklärbarkeit)** + **Block F (Auswertung)**.

---

## ✅ Erledigt (raus aus der offenen Liste)

- **A1 · Arbeitstitel-Mail** an Wählisch verschickt (Kandidaten in `arbeitstitel.md`).
- **A2 · Exposé** an Färber verschickt (`exposee.md/.html/.pdf`).
  ⚠️ Die **versendete PDF trägt noch 6,5×**; die Repo-Quelle ist auf **7,3×** aktualisiert → bei Neuversand PDF neu erzeugen.
- **Folien komplett** (`notes/folien/`): Deck `folien_konsultation.pdf` (26 S.) · `folien_sprechzettel.pdf` ·
  `folien_erklaerung.pdf` (jede Zeile erklärt) · `messziele_referenz.pdf` (Endpunkte + Ping-Befehle).
  Enthält Backup-Folien Mess-Stack, Endpunkte und **„Anatomie einer Latenzzahl"** (connect ~7 ms → Backend trägt die Spreizung).
- **Finale-Zahlen-Sweep:** alle Docs + Lernmodule auf **Vollkampagne, abgeschlossen (56/56), A4** (LLM 66,9/278,9/486,6 ms; **~7,3×**, gepoolt 8,3×;
  OpenAI-TTS-Fail **3,1 %** (173/5600); OpenAI-TTS-Connect ~1 ms; Azure-TTS ~94 ms).
- **Audit-Doku-Fixes (H1–H4, M1, ttl_ms)** in die lebenden Docs eingearbeitet (Anwendung in der Auswertung → Block C).

---

## Block A — Außenkommunikation (offen)

- ☐ **Juli-Gespräch mit Prof. Färber** vorschlagen/abstimmen.

---

## Block B — Verständnis & Erklärbarkeit ⭐ (Querschnittsziel)

> Ziel: Anton kann jeden Punkt einem skeptischen Prüfer in eigenen Worten erklären. Pro Thema ein Häkchen
> „kann ich erklären". Resource: **`folien_erklaerung.pdf`** (jede Folienzeile erklärt) + `/explain <Thema>`;
> Quellen in `../setup/` (v.a. `messprotokoll.md`, `mess_kommandos.md`) und Code in `../measurements/`.

- [ ] **B1 · Gesamt-Setup:** Vantage Point AWS EC2 Frankfurt, warum von dort, Cold-Start (jede Messung neue
      Verbindung, kein Pooling), 8 Slots/Tag, n=100, interleaved.
- [ ] **B2 · Layer 1:** was DNS/Ping(TCP+ICMP)/TLS/Traceroute messen, „RTT zum Host", warum nur der EC2-Lauf zählt.
- [ ] **B3 · Layer 2:** was tcpdump/PCAP macht, was „Eichung des Connect-Timers" heißt (App = SYN→SYN-ACK auf
      ~0,1 ms) — und was die Eichung **nicht** abdeckt (ttft/ttfa). Plus die zweite Rolle (IAT/Retransmits → Block D).
- [ ] **B4 · Layer 3:** Submetriken (tcp/tls/ws) + ttft/ttfa/total; **Metrik-Asymmetrie** (STT: ttfp connect-exklusiv;
      LLM/TTS: ttft/ttfa connect-inklusiv) — **die zentrale Verwirrungsquelle**, hier sattelfest sein.
- [ ] **B5 · Bibliotheken/Skripte:** welche Tools (httpx, websockets, raw socket, tcpdump, dig, traceroute …),
      welcher Befehl misst was (`mess_kommandos.md`), grober Aufbau von `../measurements/`. (→ Backup-Folie Mess-Stack.)
- [ ] **B6 · Kernbefund C1 in einem Satz:** „Drei LLMs am selben Cloudflare-Edge in Frankfurt (~1 ms, gemessen +
      ASN-belegt), trotzdem ~7,3× (gepoolt 8,3×) unterschiedlich schnell → der Unterschied kann nicht die Netznähe
      sein." Plus ehrlicher Caveat (Backend = HW+Modell, Modellgrößen-Confound).

---

## Block C — Audit-Auflagen in der Auswertung beachten (H1–H4, M1)

> Doku-Teil ist erledigt (s. oben); hier offen ist, was **in der Auswertung selbst** umgesetzt werden muss.
> C1 ist von keinem Punkt inhaltlich bedroht.

- [ ] **H1 · Headline-Zahlen:** 75/268/476 ms = Predeploy-Pilot (nicht reproduzierbar). Maßgeblich Voll-Kampagne
      **~67/279/487 ms (~7,3×, gepoolt 8,3×)** — Vollkampagne (56/56) (A4, success-only). **Bootstrap-CI noch ausstehend.**
- [ ] **H2 · Eichungs-Reichweite:** nur der **Connect-Timer** ist paket-validiert; ttft/ttfa nicht direkt. Nie
      „alle L3-Zahlen geeicht" formulieren.
- [ ] **H3 · Fehler-/Timeout-Filter:** kein `error_kind`-Enum. **Nicht** `error=='timeout'` — Roh-String per
      Teilstring bucketieren (`ReadTimeout`=tts_openai, `http_503`=mistral, `timeout`).
- [ ] **H4 · L1-Datensatz:** `../data/layer1/` = macOS-Dev-Lauf (~17–21 ms). In der Auswertung **nur EC2-L1**
      (ts 2026-06-16) bzw. `l1_rtt_per_ip.md`.
- [ ] **M1 · E2E-Formel:** sequenzielle Pipeline = `connect_total + stt_ttft` (LLM startet erst auf finalem
      Transkript). ttfp-Summe unterschätzt STT um ~3,7–3,9 s → nur „STT-Standalone-Responsiveness".
- [ ] **ttl_ms** existiert nicht → `total_ms` bzw. `(total−ttft)/output_tokens`.

---

## Block D — Layer 2: richere Analyse (vom Prof angeregt) ⭐ neu

> Die **Kern-Eichung steht** (16.6.: App-`tcp_handshake_ms` = SYN→SYN-ACK auf ~0,1 ms = Contribution C2).
> Offen ist die **zweite, eigenständige Rolle** von Layer 2 — genau der Punkt, den Prof Wählisch mit den
> Inter-Arrival-Times angesprochen hat. **Eigene kleine Messung nötig**, kein Blocker für die Abgabe.

- [ ] **D2 · Inter-Arrival-Times (IAT) & Retransmits aus echten Calls**
  - **Zweck (3 neue Aussagen, die der App-Timer nicht liefern kann):**
    1. **IAT der Antwort-Pakete** → Token-/Chunk-Kadenz des Backends auf der Leitung (stützt „Backend statt Geografie" sichtbar).
    2. **Retransmits / Out-of-Order** → Pfadqualität → trennt Netz-Jitter von Backend-Latenz.
    3. **Erstes Antwort-Paket nach Request** → paket-seitiger Cross-Check von `ttft` → **schließt die H2-Lücke** („sogar ttft paket-gegengeprüft").
  - **Braucht eine EIGENE Aufnahme:** `tcpdump` mit vollem Mitschnitt (`-s 0`) **während echter API-Calls**
    (nicht nur Handshake wie bei der Eichung), ~20–50 Calls je Provider. **NICHT** die 50k-Kampagne nochmal (~1 h Aufwand).
  - **Auswertung:** dependency-frei via `tcpdump -tt -n -r <pcap>` (Muster: `../measurements/layer2/analyze.py`);
    IAT = Differenz aufeinanderfolgender Paket-Zeitstempel; Retransmits via TCP-Sequenzanalyse.
  - **TLS 1.3** verschlüsselt den Inhalt → nur **Timing/Größen/Anzahl** lesbar — reicht für IAT/Retransmits.
  - **Vantage:** eine **frische** c6i.large in `eu-central-1` genügt (eigene Charakterisierung, nicht an die
    eingefrorene Kampagne gebunden) → **auch nach EC2-Stopp machbar**, kein Zeitdruck.
  - **Schon JETZT ohne neue Messung:** grobe Generierungsrate `(total_ms − ttft) / output_tokens` aus den
    50k-Daten = App-seitiger Pacing-Proxy (für die Konsultation als Ausblick nutzbar).

---

## Block F — Auswertung (Hauptarbeit nach Kampagnenende)

> Vollkampagne (56/56) erhoben + A4-Mediane stehen. Offen: volle Statistik (CI), Diagramme, E2E, Interpretation.
> Disziplin nach `../setup/messprotokoll.md` (A4-Aggregation, Bootstrap-CI, IP-Feld-Regel).

- ◐ **F1 ·** Daten von EC2 ziehen / sichten — alle 56 Slots gezogen, A4-Mediane berechnet. *(Aufräumen offen.)*
- [ ] **F2 ·** Statistik festklopfen: Median der Slot-Mediane (A4) + **Bootstrap-95%-CI**; Latenz nur success-only;
      Verfügbarkeit eigene Achse; Mann-Whitney/Bootstrap für „X schneller als Y".
- [ ] **F3 ·** Diagramme (final, nicht mehr Zwischenstand): LLM-ttft pro Provider, connect-Submetriken,
      Edge-RTT-Beleg, Verfügbarkeit/Pareto. Sachlich, keine Deko-Emojis.
- [ ] **F4 ·** Interpretation entlang C1/C2/C3 sammeln (mit Kompass-Caveat).
- [ ] **F5 ·** E2E: Monte-Carlo-Faltung der drei Phasen-Verteilungen (statt Median-Addition) + Joint-Completion/Pareto.

---

## Block G — Betrieb & Abschluss

- ⏸ **G1 · Kampagne stoppen** — `crontab -r` auf EC2 + Instanz `i-0f8f6d2414cecebb8` stoppen (Kosten).
- ⏸ **G2 ·** Danach Aufräumen (AWS-Key, Console-PW, Validierungs-Instanz `i-045a2d0eeb338b290`) — `../NEUANFANG.md §7`.

---

## Vorgeschlagene Reihenfolge

1. **Block B — Erklärbarkeit** sattelfest machen (zahlt direkt auf die Konsultation ein).
2. **Block F — Auswertung** (Bootstrap-CI + finale Diagramme + E2E).
3. **Block C** wird bei der echten Auswertung scharf (parallel zu F beachten).
4. **Block D2 — Layer-2 IAT/Retransmits** (eigene kleine Messung, sobald Zeit / nach Block F).
5. **Block A (Färber-Juli)** + **Block G (Abschluss/Aufräumen)** laufend.

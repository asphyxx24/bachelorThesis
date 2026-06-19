# Arbeitsplan — Bachelorarbeit (lebendes Aufgaben-Dokument)

> **Zweck:** Damit nichts im Chat verloren geht. Hier steht, was zu tun ist, in welcher Reihenfolge,
> und was schon erledigt ist. Wird nach und nach abgearbeitet und aktualisiert. Ergänzt (ersetzt nicht)
> `../HANDOFF.md` (Session-Einstieg) und `../NEUANFANG.md` (Referenz).
>
> **Leitziel über allem:** Anton muss bei der nächsten Wählisch-Konsultation **alles selbst erklären
> können** — Setup, Skripte, Methodik, Ergebnisse. Der Code muss nicht selbst geschrieben sein, aber
> die Methodik *verteidigt* werden. Genau das war der Grund für den Neuanfang („ich vertraue den Daten
> nicht, weil die Methodik nicht dargelegt ist"). Deshalb hat **Block B (Erklärbarkeit)** Vorrang und
> zieht sich als Querschnitt durch alle technischen Aufgaben. Werkzeug dafür: der `/explain <Thema>`-Befehl.

**Status-Legende:** ☐ offen · ◐ in Arbeit · ☑ erledigt · ⏸ später/Blocker
**Stand:** 2026-06-19

---

## Block A — Zeitkritisch / Außenkommunikation

### A1 · Arbeitstitel an Prof. Wählisch schicken (HEUTE) ◐
- Wählisch will **mehrere Ideen** sehen und bei der nächsten Konsultation darüber sprechen.
- Kandidaten liegen fertig in `arbeitstitel.md` (1 Favorit + 2 Alternativen + Platzhalter-Referenz).
- ☑ **Mail-Entwurf erstellt:** `waehlisch_titel_mail.md` (3 Kandidaten + Rationale, warum „Engine" nicht im Titel).
- [ ] **Offen:** durchlesen/anpassen → **selbst absenden**.

### A2 · Exposé (1 Seite) + Gespräch für Prof. Färber (Zweitprüfer) ◐
- Färber hat **gestern zugesagt**, will ein **Exposé** + ein **Gespräch**.
- Anker aus `zweitpruefer_anfrage.md`: Fit über LLM-Serving-Performance/Effizienz, nicht Netzwerktiefe.
- ☑ **Exposé-Entwurf erstellt + per Workflow überarbeitet:** `exposee.md` (5-Dimensionen-Review: Faktentreue/Fit/Sprache/Struktur/Angreifbarkeit → H2-Overclaim raus, negative Aussage primär, Färber-Vokabular, Geplant/Erhoben getrennt).
- [ ] durchlesen/anpassen → **selbst an Färber senden** (Zahlen sind Zwischenstand, final nach ~23.6.).
- [ ] **Gesprächstermin** vorschlagen/abstimmen.
- Hängt teils an Block B (das Exposé ist die Kurzform dessen, was Anton auch erklären können muss).

---

## Block B — Verständnis & Erklärbarkeit ⭐ (Querschnittsziel)

> Ziel: Anton kann jeden Punkt einem skeptischen Prüfer in eigenen Worten erklären. Pro Thema ein
> Häkchen „kann ich erklären". Vorgehen: `/explain <Thema>` → durchlesen → in eigenen Worten
> nacherzählen → erst dann Häkchen. Quellen liegen in `../setup/` (v.a. `messprotokoll.md`,
> `mess_kommandos.md`) und im Code unter `../measurements/`.

- [ ] **B1 · Gesamt-Setup / Messinfrastruktur:** Vantage Point AWS EC2 Frankfurt, warum von dort,
      Cold-Start-Prinzip (jede Messung neue Verbindung, kein Pooling), 8 Slots/Tag, n=100, interleaved.
- [ ] **B2 · Layer 1 (Infrastruktur):** was DNS/Ping(TCP+ICMP)/TLS/Traceroute messen, was „RTT zum Host"
      bedeutet, warum nur der EC2-Lauf zählt (nicht der macOS-Dev-Lauf).
- [ ] **B3 · Layer 2 (Paketebene):** was tcpdump/PCAP macht, was „Eichung des Connect-Timers" heißt
      (Wire-SYN→SYN-ACK ≈ App-Messung auf ~0,1 ms) — und was die Eichung **nicht** abdeckt (ttft/ttfa).
- [ ] **B4 · Layer 3 (API-Latenz):** Submetriken (tcp/tls/ws-Handshake) + ttft/ttfa/total; die
      Metrik-Asymmetrie (STT: ttfp connect-exklusiv; LLM/TTS: ttft/ttfa connect-inklusiv) — **die war
      die zentrale Verwirrungsquelle**, hier muss Anton sattelfest sein.
- [ ] **B5 · Bibliotheken / Befehle / Skripte:** welche Tools (httpx, websockets, raw socket, tcpdump,
      chrony …), welcher Befehl misst was (`mess_kommandos.md`), grober Aufbau der Skripte in
      `../measurements/`. So viel, dass Anton ein Skript am Bildschirm grob durchgehen kann.
- [ ] **B6 · Der Kernbefund C1 in einem Satz:** „Drei LLMs hängen am selben Cloudflare-Edge in Frankfurt
      (~1 ms, gemessen + ASN-belegt), antworten aber bis zu 6,5× unterschiedlich schnell → der Unterschied
      kann nicht die Netznähe sein." Plus der ehrliche Caveat (Backend = HW+Modell, Modellgrößen-Confound).

---

## Block C — Audit-Auflagen vor der Auswertung (H1–H4, M1)

> Aus dem Voll-Audit 2026-06-18 (GO-mit-Auflagen). **Alles Doku/Reporting, keine Neumessungen.** Der
> Doku-Teil ist am 19.6. bereits in die lebenden Docs eingearbeitet; hier offen ist, was **in der
> Auswertung selbst** beachtet/umgesetzt werden muss. C1 ist von keinem Punkt inhaltlich bedroht.

- [ ] **H1 · Headline-Zahlen:** 75/268/476 ms = Predeploy-Pilot (nicht reproduzierbar). Maßgeblich
      Voll-Kampagne **~68/280/440 ms (~6,5×)**. Finale Zahlen erst **nach Kampagnenende** einsetzen.
- [ ] **H2 · Eichungs-Reichweite:** Nur der **Connect-Timer** ist paket-validiert; ttft/ttfa nutzen
      denselben Mechanismus, sind aber nicht direkt geeicht. Nie „alle L3-Zahlen geeicht" formulieren.
- [ ] **H3 · Fehler-/Timeout-Filter:** Kein `error_kind`-Enum im Code. **Nicht** `error=='timeout'`
      (verfehlt 158/161). Roh-String per Teilstring bucketieren (`ReadTimeout`=tts_openai, `http_503`, `timeout`).
- [ ] **H4 · L1-Datensatz:** `../data/layer1/` im Repo = macOS-Dev-Lauf (~17–21 ms). In der Auswertung
      **nur EC2-L1** (ts 2026-06-16) bzw. `l1_rtt_per_ip.md` verwenden.
- [ ] **M1 · E2E-Formel:** sequenzielle Pipeline = `connect_total + stt_ttft` (LLM startet erst auf finalem
      Transkript). ttfp-Summe unterschätzt STT um ~3,7–3,9 s → nur als „STT-Standalone-Responsiveness".
- [ ] **ttl_ms** existiert nicht → durch `total_ms` bzw. `(total−ttft)/output_tokens` ersetzen.

---

## Block D — Layer 2 (Stand klären — kein Blocker)

> **Wichtig zur Einordnung:** Die **Kern-Eichung von Layer 2 ist erledigt** (16.6.) und ist einer der
> *stärksten* Validitätsbelege (Contribution C2): App-`tcp_handshake_ms` = Wire-SYN→SYN-ACK auf ~0,1 ms.
> „Layer 2 noch machen" stimmt also nur teilweise — die **Eichung steht**, validiert ist der Connect-Timer.

- [ ] **D1 · Verständnis (gehört zu B3):** Anton kann erklären, was geeicht wurde und was nicht.
- ⏸ **D2 · Richere Layer-2-Analyse (optional, später):** IAT/Retransmits während echter Calls auswerten.
      **Kein Blocker** für Auswertung/Abgabe — nur „nice to have", falls Zeit bleibt.

---

## Block E — Folien für Prof. Wählisch

> Wählisch wünscht Folien, „wo alles 'n bisschen draufsteht" — ausführlich aufarbeiten. Format (LaTeX
> Beamer vs. Markdown) **noch offen**, entscheiden wir später. Inhalt-Gerüst (aus HANDOFF §5.6):

- [ ] **E0 · Format entscheiden** (LaTeX Beamer / Markdown-Slides / PDF). → im Chat.
- [ ] **E1 ·** Drei-Schichten-Architektur + Layer-2-Eichung (Connect-Timer!).
- [ ] **E2 ·** Edge/Host-Klassifikation (Cloudflare-Grenze, C2).
- [ ] **E3 ·** C1-Kernbeleg: LLM @ identische Edge-RTT, trotzdem ~6,5× Spreizung.
- [ ] **E4 ·** Ehrliche Limitationen (Modellgrößen-Confound, STT kein Engine-Beleg, Diurnal = Snapshot).
- Die Folien sind zugleich die **Generalprobe für Block B** — was auf die Folie kommt, muss Anton erklären können.

---

## Block F — Auswertung vorbereiten (schon jetzt anfangen)

> Kampagne läuft noch (~23.6.), finale Zahlen also noch nicht. Aber: Auswerte-Gerüst + **Diagramm-
> Prototypen** lassen sich schon mit dem 16-Slot-Zwischenstand (`../data/audit_20260618/ec2_data/`) bauen.
> Diszipliniert nach `../setup/messprotokoll.md` (A4-Aggregation, Bootstrap-CI, IP-Feld-Regel).

- [ ] **F1 ·** Daten von EC2 ziehen / Zwischenstand sichten; Auswerte-Notebook/Skript-Gerüst anlegen.
- [ ] **F2 ·** Statistik-Disziplin festklopfen: Median der Slot-Mediane (A4) + Bootstrap-95%-CI;
      Latenz nur success-only; Verfügbarkeit eigene Achse; Mann-Whitney/Bootstrap für „X schneller als Y".
- [ ] **F3 ·** Diagramm-Prototypen (mit Zwischendaten, klar als vorläufig markiert): LLM-ttft pro Provider,
      connect-Submetriken, Edge-RTT-Beleg, Verfügbarkeit. Kein KI-Look (sachlich, Zahlen, keine Deko-Emojis).
- [ ] **F4 ·** Stichpunkte zur Interpretation entlang C1/C2/C3 sammeln (mit Kompass-Caveat).

---

## Block G — Betrieb & Abschluss

- ⏸ **G1 · ~23.6.: Kampagne stoppen** — `crontab -r` auf EC2 + Instanz `i-0f8f6d2414cecebb8` stoppen (Kosten).
- ⏸ **G2 ·** Danach Aufräumen (AWS-Key, Console-PW, Validierungs-Instanz `i-045a2d0eeb338b290`) — `../NEUANFANG.md §7`.
- ☐ **Laufender Check:** Slot-Zahl (~+8/Tag) + Rev.ai-Guthaben im Blick (`../HANDOFF.md §1`).

---

## Vorgeschlagene Reihenfolge (Diskussionsbasis)

1. **A1 Arbeitstitel-Mail** (heute fällig, schnell erledigt).
2. **A2 Exposé Färber** (terminiert durch seine Zusage; deckt sich inhaltlich mit Block B).
3. **Block B Erklärbarkeit** parallel hochziehen — zahlt auf Konsultation *und* Exposé *und* Folien ein.
4. **F1–F3 Auswertungs-Gerüst + Prototypen** (vorankommen, solange Kampagne läuft).
5. **E Folien** (sobald B sitzt und erste Prototypen da sind).
6. **C** wird bei der echten Auswertung scharf (finale Zahlen nach ~23.6.).

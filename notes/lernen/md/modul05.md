# Modul 5 — Setup, Cold-Start & Kampagne

**Ziel:** Das gesamte Messdesign erklären — Vantage Point, Cold-Start, Kampagnenstruktur und die Reproduzierbarkeits-Anker — so, dass jeder Punkt einem skeptischen Prüfer in eigenen Worten verteidigbar ist.

> **Hinweis zu allen Zahlen:** Alle Kampagnen-Zahlen sind **A4-Mediane über 56 von 56 Slots** (Vollkampagne, abgeschlossen; success-only); die **Bootstrap-Konfidenzintervalle** stehen noch aus. Die Punktschätzer sind **final**, die **Ordnung ist stabil**.

## 5.1 Begriffe

| Begriff | Definition (in diesem Projekt) |
|---------|-------------------------------|
| **Vantage Point** | Der Mess-Standort, also der Ort/Rechner, von dem aus gemessen wird. Hier: AWS EC2 in Frankfurt. |
| **Instanz** | Eine virtuelle Maschine bei einem Cloud-Anbieter (AWS). Es gibt verschiedene Typen. |
| **burstable** | Instanz-Typ (z.B. `t2`/`t3`), der die CPU über ein Guthaben-System (**CPU-Credits**) bereitstellt und bei Erschöpfung drosselt. |
| **CPU-Credit-Throttling** | Drosselung der Rechenleistung bei aufgebrauchtem CPU-Guthaben → verfälscht ms-Timer. |
| **`cpu_steal`** | Vom Hypervisor weggenommene Rechenzeit; flach = keine Drosselung. Beleg gegen Throttling. |
| **Cold-Start** | Jede Messung baut eine **neue** TCP+TLS-Verbindung auf und schließt sie danach. Misst die „Erste-Eindruck"-Latenz. |
| **Connection-Pooling / Keep-Alive** | Wiederverwenden einer offenen Verbindung für mehrere Anfragen. Hier **bewusst NICHT** verwendet. |
| **Slot** | Ein festes Mess-Fenster zu einer festen UTC-Stunde (8 pro Tag, alle 3 h). |
| **interleaved (verschränkt)** | Reihenfolge innerhalb eines Slots: jede Runde **einmal** der Reihe nach durch alle 9 Endpunkte (Round-Robin), Startreihenfolge rotiert. |
| **UTC** | Koordinierte Weltzeit — zeitzonen- und sommerzeit-frei (kein DST-Sprung). |
| **diurnal pattern** | Tagesgang der Last; betrifft v.a. die US-Backends. |
| **`run_meta`** | Metadaten-Datensatz pro Slot (1× je Slot, erste Zeile der Slot-Datei) — der Reproduzierbarkeits-Anker. |
| **Perzentil (p95/p99)** | Schwellwert in der sortierten Verteilung: unter p95 liegen 95 % aller Werte. Beschreibt den langsamen „Tail". |

## 5.2 Vantage Point — EC2 Frankfurt

- **Ort:** AWS EC2, Region `eu-central-1` (Frankfurt), Instanz `i-0f8f6d2414cecebb8`. Frankfurt ist ein zentraler EU-Internet-Knoten.
- **Warum überhaupt EU:** Die **Forschungsfrage ist die EU-Perspektive** — also misst der Client aus Europa.
- **Software-Stack:** Ubuntu, **echtes OpenSSL 3.x** (TLS-Version belastbar), Zeit per **chrony** synchron, alles in **UTC**.
- **Limitation (ehrlich deklarieren):** Es gibt **nur diesen einen** Vantage Point (Frankfurt). Die RTT-/Edge-Zahlen sind FRA-spezifisch — ein anderer EU-Standort sähe andere Edge-Distanzen. **Aber:** Der Kernbefund (Latenzspreizung bei **konstanter** Netz-Distanz → durch Netznähe **nicht erklärbar**; HW+Modell-Confound, daher nicht „Engine" als belegte Ursache) ist davon **nicht betroffen**, weil gleiche Distanz von überall gleich bleibt. Single-VP = deklarierte Grenze, Kernaussage robust.

## 5.3 Warum keine burstable-Instanz (Prüf-Frage 1)

- **Problem burstable:** `t2`/`t3` laufen auf **CPU-Credits**. Ist das Guthaben aufgebraucht, drosselt AWS die CPU (**CPU-Credit-Throttling**). Dann springen ms-Latenz-Timer **ohne Netz-Ursache** → genau die unerklärte Varianz, die der Prof am alten Lauf (lief auf `t3.small`) bemängelt hat.
- **Lösung:** **`c6i.large`** — non-burstable, garantierte CPU (2 vCPU, 4 GiB). Reicht, weil die Mess-Last **netzwerk-gebunden**, nicht rechen-intensiv ist.
- **Beleg statt Behauptung:** Pro Slot wird die **`cpu_steal`-Time** mitgeloggt. Im Pilot **flach `37 → 37`** über den Slot → **kein Throttling**, empirisch belegt.

> **Prüf-Antwort:** „Burstable-Typen drosseln bei Credit-Erschöpfung die CPU, was meine ms-Timer ohne Netz-Ursache verfälscht hätte. `c6i.large` hat garantierte CPU; dass nicht gedrosselt wurde, belege ich über die flache `cpu_steal`-Time je Slot."

## 5.4 Cold-Start, kein Connection-Pooling (Prüf-Frage 2)

- **Definition:** Jede einzelne Messung baut eine **neue TCP- und TLS-Verbindung** auf und schließt sie wieder. Damit misst man die „Erste-Eindruck"-Latenz inkl. `tcp_handshake` und `tls_handshake`.
- **Warum:** Der **Verbindungsaufbau zum Backend** ist aus EU-Sicht gerade der **interessante Anteil** (Distanz zum US-Backend). So startet ein Nutzer eine neue Voice-Session.
- **Warum kein Pooling:** Pooling würde eine offene Verbindung wiederverwenden → ab dem **zweiten** Call fiele der Aufbau weg und würde **genau den Teil verstecken**, den man messen will. Kaltstart ist also Absicht, keine Ineffizienz.

> **Prüf-Antwort:** „Ich messe Cold-Start, weil der Verbindungsaufbau zum Backend aus EU-Sicht der relevante Latenz-Anteil ist. Pooling würde ihn ab Call 2 wegmitteln und genau das verstecken, was ich messe."

## 5.5 Kampagnenstruktur — 7 × 8 × n=100, interleaved

**Drei Varianzquellen, drei Design-Achsen:** Run-Jitter → viele Wiederholungen (`n`); Tageszeit → mehrere Slots; Wochentag/Wochenende → 7 Tage.

| Achse | Wert |
|-------|------|
| Dauer | **7 Tage** (volle Woche inkl. Wochenende) |
| Slots/Tag | **8**, alle 3 h: `00 / 03 / 06 / 09 / 12 / 15 / 18 / 21h` UTC |
| n je Slot & Endpunkt | **100** |
| Slots gesamt | 7 × 8 = **56** |
| Messungen/Endpunkt | 56 × 100 = **5.600** |
| Endpunkte | **9** (3 STT, 3 LLM, 3 TTS) |
| **Gesamt** | 56 × 100 × 9 = **50.400** Calls |
| **Ausgewertet** | **56 von 56 Slots** (Vollkampagne, abgeschlossen; A4-Mediane, success-only) |

**Interleaved (verschränkt) statt block:**
- Jede Runde **einmal** der Reihe nach durch alle 9 Endpunkte (Round-Robin), **100 Runden**; **Startreihenfolge rotiert** je Runde (`shift = rnd % len(eps)`).
- **Warum nicht block** (erst 100× A, dann 100× B): Ein Block-Verfahren würde einen **vermeintlichen Anbieter-Unterschied** vorgaukeln, der in Wahrheit nur ein **Zeit-/Last-Effekt** zwischen den Blöcken ist. Interleaved lässt alle 9 dieselbe Zeit-Verteilung der Netzbedingungen sehen → **fairer Cross-Provider-Vergleich**.
- **Warum Rotation:** Ohne Rotation säße ein Anbieter dauerhaft auf derselben (bevorzugten/benachteiligten) Position; Rotation verteilt die Positionen gleichmäßig.
- **Nebeneffekt:** Zwischen zwei Calls **desselben** Anbieters liegen 8 andere → rate-limit-freundlich.

## 5.6 Warum UTC-Slots (Prüf-Frage 3)

- **Zeitzonen- und sommerzeit-frei:** UTC kennt **keinen DST-Sprung** (Sommerzeit-Umstellung). In lokaler Zeit wäre der Tagesgang an einem Umstellungstag verschoben und nicht mehr sauber mit den anderen Tagen vergleichbar.
- **Reproduzierbar:** Jeder `03h`-Slot meint über alle 7 Tage **exakt denselben** Moment im Tageszyklus → der **Diurnal-Effekt** ist sauber vergleichbar.
- **Volle 24-h-Abdeckung:** Der Diurnal-Effekt betrifft die **US-Backend-Last**. Die Slots müssen das **US-Tageshoch** (US-Ostküste-Nachmittag ≈ 18–22 UTC) **und** das **US-Nachttief** (≈ 06–10 UTC) treffen — nicht nur EU-Bürozeiten.
- **Slot-`tag` mitschreiben:** Gruppierung erfolgt **nach `tag`** (z.B. `03h`), nicht nach Timestamp-Stunde → verhindert den „Phantom-Slot" bei leicht verspäteten Läufen.

> **Prüf-Antwort:** „UTC ist zeitzonen- und sommerzeit-frei, also springt mein Tagesgang nicht. So ist jeder Slot über alle 7 Tage derselbe Moment im Tageszyklus und der Diurnal-Effekt sauber vergleichbar — inklusive US-Tageshoch und -Nachttief."

## 5.7 Warum 5.600/Endpunkt (Prüf-Frage 4)

- **n=100 je Slot** ist komfortabel für **Median/p50/p90** je Slot — aber für hohe Perzentile zu wenig.
- **Hohe Perzentile (p95/p99)** beschreiben den langsamen **Tail** der Verteilung (die interessanten Ausreißer) und brauchen **viele** Daten, sonst sind sie Rauschen.
- **Faustregel** (Detail in Modul 13): Ein Perzentil `q` ist erst stabil, wenn **`n · (1 − q) ≥ 5–10`**. Für p99 heißt das hunderte bis tausende Werte.
- **Konsequenz:** p95/p99 werden **nur gepoolt** über alle 56 Slots berechnet — und die **5.600/Endpunkt** geben dieser gepoolten Schätzung genug Substanz. Die hohe Zahl dient also nicht dem Median (den hätte man billiger), sondern der **Belastbarkeit der hohen Perzentile**.

> **Prüf-Antwort:** „5.600 brauche ich nicht für den Median, sondern für belastbare hohe Perzentile. Nach der Faustregel `n·(1−q) ≥ 5–10` reichen 100 je Slot für p99 nicht; gepoolt über 56 Slots ergeben 5.600/Endpunkt genug Tail-Substanz."

## 5.8 Reproduzierbarkeits-Anker: `run_meta`

Pro Slot **ein** `run_meta`-Record (1× je Slot, **erste Zeile** der Slot-Datei) macht jeden Slot reproduzier- und zuordenbar. Inhalt (verifiziert in `measurements/layer3/run.py`):

| Feld | Wozu |
|------|------|
| `git_commit` (+ `git_dirty`) | Exakter Code-Stand je Slot; `dirty` = ungespeicherte Änderungen |
| `requirements_sha` (**Lockfile-Hash**) | Reproduzierbare Software-Umgebung (festgenagelte Bibliotheks-Versionen) |
| `instance_id` / `instance_type` / `ami_id` | Welche Maschine gemessen hat |
| `cpu_steal_start` (+ `cpu_steal_end` im `run_end`) | **Beleg gegen burstable-Throttling** (s. 5.3); Start im `run_meta`, Ende im `run_end` |
| `openssl` (`ssl.OPENSSL_VERSION`) | TLS-Version belastbar (LibreSSL-Slots verwerfbar) |
| `chrony` (`chronyc tracking`) | Zeitbasis-Schnappschuss |

> **Datei-Aufbau je Slot:** `run_meta` (1. Zeile) → ein Record je Call → `run_end` (letzte Zeile). Ablage: `data/layer3/campaign/<tag>_<ts>.jsonl`.

## 5.9 Code eingefroren

- Sobald die Messphase begann, wurde der **Mess-Code eingefroren** — während der laufenden Kampagne keine Änderungen mehr.
- **Maßgeblicher Freeze-Commit: `f9e6dc8`.** Der Layer-3-Mess-Code (`llm.py`/`tts.py`/`stt.py`/`run.py`/`config.py`) ist über die relevanten Versionen **identisch** (dazwischen nur Layer-2-Eichung + Doku, keine Layer-3-Datei geändert).
- **Warum:** Ändert man mitten in der Messung den Code, weiß man hinterher nicht, ob ein Daten-Unterschied vom Server oder von der eigenen Änderung kommt. Eingefrorener Stand + `git_commit` im `run_meta` macht jede Messung **einer eindeutigen Code-Version zuordenbar**.

## Prüf-Fragen

1. Warum keine burstable-Instanz?
2. Warum Cold-Start?
3. Warum UTC-Slots?
4. Warum 5.600/Endpunkt?

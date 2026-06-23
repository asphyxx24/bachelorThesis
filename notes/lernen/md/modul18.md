# Modul 18 — Stand & offene Punkte

**Ziel:** Den aktuellen Projektstatus sauber zusammenfassen — so, dass du einem skeptischen Prüfer in zwei Minuten ruhig sagen kannst, wo das Projekt steht, was noch läuft, was offen ist und was ausdrücklich nicht mehr nötig ist.

## 18.1 Worum es geht

Dies ist ein **Status-Modul**, kein Methoden- oder Befund-Modul. Es liefert eine ehrliche Bestandsaufnahme. Zwei Dinge:

1. Die **Messphase** ist abgeschlossen (Vollkampagne, 56/56 Slots).
2. Die **Auswertung** wird bereits vorbereitet.

Die zentrale Disziplin: die maßgeblichen Zahlen beruhen auf der **Vollkampagne (56 von 56 Slots, A4, success-only)** — die Werte stehen, offen ist nur noch das **Bootstrap-CI**. Die Datenbasis (welcher Datensatz, welche Aggregation) sagst du immer aktiv dazu — sonst wirkt es, als würden Werte ohne deklarierte Grundlage als feststehende Ergebnisse verkauft.

**Begriffe vorab:**

| Begriff | Bedeutung im Projekt |
|---------|----------------------|
| **Vantage Point** | Fester Beobachtungsstandort aller Messungen — AWS EC2 in `eu-central-1` (Frankfurt). |
| **Kampagne** | Geplante Mess-Serie über mehrere Tage. |
| **Slot** | Ein Messdurchlauf zu einer festen UTC-Uhrzeit. 8 Slots/Tag, je `--n 100` pro Endpunkt. |
| **Audit** | Systematische Selbstprüfung von Methodik und Auswertung. |
| **Exposé** | Kurze schriftliche Skizze der Arbeit (~1 Seite) für den Zweitprüfer. |
| **Code eingefroren** | Code steht auf einem festen, dokumentierten Commit und wird nicht mehr verändert. |

## 18.2 Die Kampagne (abgeschlossen, 56/56) — und was das für die Zahlen heißt

- **Plan:** 7 Tage × 8 UTC-Slots (`00/03/06/09/12/15/18/21h`) × `n=100` = **56 Slots = 5.600/Endpunkt = 50.400 Calls**.
- **Stop-Termin:** ungefähr **23. Juni**; danach wird die EC2-Instanz `i-0f8f6d2414cecebb8` planmäßig gestoppt (Kosten).
- **Aktueller Stand:** **56 von 56 geplanten Slots** — die Vollkampagne ist abgeschlossen (56/56).

**Folgerung (genau das ist die Antwort an den Prüfer):** Die genannten Werte beruhen auf der **Vollkampagne (56 von 56 Slots, A4 = Median der Slot-Mediane, success-only)** — der maßgebliche Datensatz. Offen ist nur noch das **Bootstrap-CI** (ausstehend). Die **Ordnung** der Ergebnisse (wer schneller/langsamer) ist über die Slots **stabil** — der Richtung und den Werten traust du, die formale Unsicherheitsangabe (CI) reichst du nach.

**Wichtige Trennung:** Nur **Layer 3** (API-Latenz) läuft slotweise über die Tage. **Layer 1** (DNS, RTT, TLS, Traceroute) war eine **einmalige Momentaufnahme am 16.6.**, kein Slotbetrieb. Diese Verwechslung aktiv vermeiden.

## 18.3 Arbeitstitel offen

Der Arbeitstitel ist **noch nicht final gewählt**. Kandidaten liegen in `notes/arbeitstitel.md` (Favorit + zwei Alternativen). Bewusst tauchen **„Engine" und „Backend" NICHT im Titel** auf:

- Die wasserdichte Aussage des Projekts ist die **negative**: *Netznähe erklärt die Latenzspreizung nicht.*
- Der Schritt zu „Backend" trägt einen **Confound** (Vermengung mehrerer Ursachen): der schnellste Anbieter (Groq) hat zugleich das kleinste Modell **und** spezielle Hardware (LPU).
- Daher bleibt der Titel **neutral-deskriptiv** und behauptet keine Ursache, die nicht sauber trennbar ist.

Die finale Wahl steht aus und wird dem Betreuer vorgelegt.

## 18.4 Zweitprüfer Färber / Juli

- **Zweitprüfer:** Prof. Färber ist angefragt, hat **Interesse signalisiert** und ein **Exposé** gewünscht.
- **Exposé sendefertig** (Versand an Färber steht aus, vgl. `arbeitsplan.md` A2). Ein **Gespräch ist für Juli geplant.**
- Vorbehalt wie überall: die Zahlen im Exposé beruhen auf der **Vollkampagne (56 von 56 Slots, A4, success-only)**; das **Bootstrap-CI** wird nachgereicht.

## 18.5 Audit-Auflagen in der Auswertung

Aus dem Voll-Audit (2026-06-18, Urteil **GO-mit-Auflagen**) stammen Auflagen, kurz **H1–H4** plus einige MEDIUM-Punkte.

- **Wesensart:** durchweg **Doku/Reporting** — *wie* etwas dargestellt und ausgewertet wird — **keine** Hinweise auf falsche Messungen. C1 ist von keinem Punkt inhaltlich bedroht.
- **Stand:** der **Doku-Teil ist bereits in die lebenden Docs eingearbeitet**.
- **Offen:** die **Anwendung in der eigentlichen Auswertung**. Beispiele dessen, was in der Analyse beachtet werden muss:

| Auflage | Was in der Auswertung zu tun ist |
|---------|----------------------------------|
| **H1** | Headline-Zahlen auf den maßgeblichen Datensatz stützen (56 von 56 Slots, A4, success-only); Bootstrap-CI noch ausstehend. |
| **H2** | Nur der Connect-Timer ist paket-geeicht; `ttft`/`ttfa` nicht direkt — nie „alle L3-Zahlen geeicht" sagen. |
| **H3** | Fehler-/Timeout-Filter über Roh-String (`ReadTimeout` etc.) bucketieren, **nicht** `error=='timeout'`. |
| **H4** | In der Auswertung nur **EC2-Layer-1** (ts 2026-06-16) bzw. `l1_rtt_per_ip.md` verwenden, nicht den macOS-Dev-Lauf. |

## 18.6 Folien (Block E)

Für Prof. Wählisch stehen **Folien noch aus** (Block E). Sie sollen Setup, Methodik und Ergebnisse ausführlich darstellen. Inhalt-Gerüst:

1. Drei-Schichten-Architektur + Layer-2-Eichung (Connect-Timer).
2. Edge/Host-Klassifikation (Cloudflare-Grenze, C2).
3. C1-Kernbeleg: LLM @ identische Edge-RTT, trotzdem ~7,3× (gepoolt 8,3×) Spreizung im `ttft`.
4. Ehrliche Limitationen (Modellgrößen-Confound, STT kein Engine-Beleg, Diurnal = Snapshot).

Die Folien sind zugleich die **Generalprobe für die Erklärbarkeit**: was auf eine Folie kommt, muss in eigenen Worten erklärbar sein.

## 18.7 Was ausdrücklich NICHT mehr nötig ist

Das ist der wichtigste Status-Punkt für die Gesprächsruhe:

- **Keine Neumessungen.**
- **Kein Code-Umbau.**

Der **Code ist eingefroren** (Commit `f9e6dc8`). Grund: nur so messen alle Slots mit **exakt derselben Prozedur** → die Serie bleibt vergleichbar. Ab jetzt geht es nur noch um **Auswertung, Statistik und Reporting**.

Die offenen Audit-Auflagen ändern daran **nichts** — sie betreffen ausschließlich **Darstellung und Auswertung**, nicht die Erhebung. Auf die Prüfer-Frage „muss da noch einmal gemessen werden?" ist die Antwort ein klares **Nein**, mit genau dieser Begründung.

## Prüf-Fragen

1. Bis wann läuft die Kampagne, und was bedeutet das für die Zahlen?
2. Welche größeren To-dos stehen noch offen (Titel, Zweitprüfer, Folien, Auswertung)?
3. Was ist ausdrücklich nicht mehr nötig — und warum?

# Modul 1 — Vertrauensproblem & Neuanfang

**Ziel:** Einem Skeptiker erklären können, *warum* das Projekt neu aufgebaut wurde — so, dass es als **Stärke** rüberkommt, nicht als Fehler-Eingeständnis.

## 1.1 Was der Prof gesagt hat

Zwei Aussagen, Reihenfolge wichtig:

1. **„Im Kern reicht das schon."** Die Richtung stimmt, die Arbeit besteht — keine Notlage.
2. **„Ich vertraue den Daten nicht."** Weil **Methodik, Setup und Struktur nicht dargelegt** waren. Konkret bemängelt:
   - kein nachvollziehbares Mess-Setup,
   - keine erklärte Struktur,
   - drei Anbieter mit ~1 ms Layer-1-Latenz, unerklärt.

## 1.2 Korrektheit vs. Reproduzierbarkeit

Der zentrale Begriff:

| Begriff | Frage | War das der Vorwurf? |
|---------|-------|----------------------|
| **Korrektheit** | Stimmt die Zahl? | **Nein** |
| **Reproduzierbarkeit** | Kann ein Dritter aus deiner dokumentierten Prozedur zur selben Zahl kommen? | **Ja** |

Eine Zahl ohne dokumentierte, reproduzierbare Prozedur ist wissenschaftlich **kein Befund** — selbst wenn sie zufällig stimmt. Das „3 Anbieter mit ~1 ms"-Beispiel: Die Zahl war vermutlich korrekt, aber *unerklärt* — und unerklärt sieht sie aus wie ein Messfehler.

## 1.3 Warum Neuanfang statt nur Doku nachreichen

Bewusste Entscheidung **fürs eigene Verständnis**: alles Schritt für Schritt selbst aufbauen, sodass jede Zahl auf eine dokumentierte Prozedur zurückführbar ist. Daraus das Leitprinzip:

> **Erst Methodik schriftlich, dann Code, dann messen.**

Steht die Methodik vor dem Code, ist sie per Konstruktion dokumentiert — Reproduzierbarkeit ist dann kein Anhängsel, sondern die Reihenfolge selbst.

## 1.4 Behalten vs. verworfen

- **Verworfen:** die alten Rohdaten (liegen in `archived/`).
- **Behalten:** das *Wissen* — der Reframe „Backend statt Geografie", die Mängelliste A1–A14 (als Spezifikation fürs bessere Setup), die Provider-Rationale.

**Merksatz:** *Du hast nicht repariert, du hast nachvollziehbar gemacht.*

⚠️ **Stolperstein im Gespräch:** Sag **nicht** „ich musste Messwerte neu messen" — das klingt nach „die alten Zahlen waren falsch" (Korrektheits-Framing). Sag: Der Neuanfang war fürs Verständnis und für Reproduzierbarkeit; dass die Methodik dabei schärfer wurde, ist ein Nebeneffekt, kein Fehler-Eingeständnis.

## Prüf-Fragen

1. Was heißt „ich vertraue den Daten nicht" konkret — und warum ist das *kein* Vorwurf, du hättest falsch gerechnet?
2. Was stellt das Vertrauen wieder her — und warum hätte „nur Doku nachreichen" weniger überzeugt?

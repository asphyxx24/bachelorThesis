# Workflow-Guide: Bachelorarbeit mit Claude Code

## Philosophie: Verstehen, nicht nur delegieren

Diese Commands helfen dir schneller zu arbeiten — aber der Anspruch ist höher:
Du sollst verstehen was passiert, nicht nur Ergebnisse bekommen.

Deshalb gibt es drei Arbeitsbereiche. Die meisten Leute überspringen den dritten.
Das ist der Fehler.

---

## Die drei Arbeitsbereiche

### 1. Planung — Wo stehe ich, was ist als nächstes?

Bevor du arbeitest, musst du wissen wo du stehst.

| Command | Wann benutzen | Was passiert |
|---------|--------------|--------------|
| `/coach` | Start jeder Session | Liest den Repo-Zustand, gibt ehrliches Feedback, nennt einen konkreten nächsten Schritt |
| `/status` | Wenn du schnell den Überblick brauchst | Fakten: Dateien, Provider, offene TODOs |
| `/thesis-check` | Wöchentlich | Wissenschaftliches Review: roter Faden, kritische Lücken, was fehlt noch |
| `/prof` | Vor Betreuer-Treffen | Simuliert Prof. Wählisch — stellt Fragen aus dem tatsächlichen Projektstand |

**Empfohlene Wochenroutine:**
- Montag: `/coach` → Was steht diese Woche an?
- Freitag: `/thesis-check` → Wo stehe ich wissenschaftlich?
- Vor jedem Meeting mit Wählisch: `/prof` → Bin ich bereit?

---

### 2. Ausführung — Die eigentliche Arbeit

Wenn du weißt was zu tun ist, helfen diese Commands beim Ausführen.

| Command | Wann benutzen | Was passiert |
|---------|--------------|--------------|
| `/analyze` | Daten auswerten | Code-Vorschläge für Notebooks, Statistiken, Plots |
| `/write <Abschnitt>` | Thesis-Text schreiben | Hilft einen Abschnitt zu strukturieren und zu formulieren |

**Typischer Ablauf für eine Analyse-Session:**
1. `/coach` → "Analysiere zuerst Layer 3 Latenzen von Deepgram"
2. `/analyze` → gibt Notebook-Code
3. Code ausführen, Ergebnisse sehen
4. `/write Ergebnisse` → schreibt den Ergebnisabschnitt dazu

---

### 3. Erklärung — Verstehen was passiert

Der wichtigste Bereich. Wird am häufigsten übersprungen.

| Command | Wann benutzen | Was passiert |
|---------|--------------|--------------|
| `/explain <Thema>` | Immer wenn etwas unklar ist | Erklärt das Konzept und verbindet es mit dem Projekt |

**Beispiele:**
```
/explain transcript_len=0
/explain p99
/explain Cold-Start vs Warm-Start
/explain TLS Handshake
/explain Forschungsbeitrag vs Benchmarking
/explain Warum Cold-Start statt Warm-Start?
/explain Was misst connect_ms genau?
```

Keine schlechten Fragen. Wenn etwas unklar ist: fragen.
Am Ende der Thesis solltest du alles, was du abgibst, selbst erklären können.

---

## Quick Reference

```
Orientierung:     /coach            → Wo stehe ich? Was ist als nächstes?
Überblick:        /status           → Fakten: Dateien, Provider, TODOs
Wissenschaft:     /thesis-check     → Ist die Thesis methodisch solide?
Betreuer-Prep:    /prof             → Wie würde Wählisch fragen?

Analyse:          /analyze          → Notebook-Code für Datenauswertung
Schreiben:        /write <Abschnitt>→ Thesis-Abschnitte formulieren

Verstehen:        /explain <Thema>  → Was bedeutet X?

Session-Ende:     /handoff          → Arbeitsstand in HANDOFF.md schreiben
```

---

## Kontextpersistenz: Wie der Kontext über Sessions hinweg erhalten bleibt

```
CLAUDE.md     → stabile Projektfakten, auto-geladen bei jedem Start
HANDOFF.md    → dynamischer Stand (via @HANDOFF.md in CLAUDE.md eingebunden)
```

Beim nächsten Chat-Start sind beide automatisch da. Du musst nichts sagen.
Am Session-Ende: `/handoff` tippen → HANDOFF.md wird aktualisiert.

---

## Was AI hier kann und was nicht

**Kann:**
- Den Projektstand aus dem Repo lesen und einschätzen
- Code für Analysen schreiben und erklären
- Thesis-Abschnitte entwerfen (als Ausgangspunkt)
- Fragen stellen, die du dir selbst nicht gestellt hättest
- Konzepte erklären, die du nicht kennst

**Kann nicht:**
- Entscheiden ob dein Scope realistisch ist — das bist du
- Den Prof ersetzen — `/prof` ist Vorbereitung, kein Ersatz
- Wissen was du wirklich weißt und was du nur gelesen hast
- Die Thesis schreiben — Entwürfe ja, fertige Abgabe nein

Die Grenze: Wenn du eine Antwort von Claude nimmst ohne sie zu verstehen,
wirst du beim Betreuer-Meeting nicht mithalten können.

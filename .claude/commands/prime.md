Lies den aktuellen Projektstand und gib einen kurzen Session-Briefing.

Lies diese Quellen:
1. HANDOFF.md (letzter Stand, aktuelle Fokus-Aufgabe, offene Schritte)
2. `git log --oneline -10` (letzte Commits)
3. `git diff --stat` (uncommitted Änderungen)
4. Zähle Dateien in data/layer1/, data/layer2/, data/layer3/ (Datenstand)
5. notes/implementation_plan.md (offene Phasen)

Gib dann aus:

## Session-Briefing [Datum]

**Letzter Stand:** [1-2 Sätze aus HANDOFF.md]

**Uncommitted:** [Änderungen oder "sauber"]

**Datenstand:**
- Layer 1: X Dateien
- Layer 2: X Dateien
- Layer 3: X Dateien

**Aktuelle Phase:** [aus implementation_plan.md — welche Phase ist dran?]

**Fokus diese Session:** [konkrete nächste Aufgabe aus HANDOFF.md]

Halte das Briefing unter 15 Zeilen. Keine Erklärungen, nur Fakten.

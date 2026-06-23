Lies den aktuellen Projektstand und gib einen kurzen Session-Briefing.

Lies diese Quellen:
1. HANDOFF.md (letzter Stand, aktuelle Fokus-Aufgabe, offene Schritte; v.a. den Audit-Auflagen-Abschnitt §4)
2. `git log --oneline -5` (letzte Commits)
3. `git diff --stat` (uncommitted Änderungen)
4. `data/audit_20260618/VERDICT.md`, falls vorhanden (jüngstes Voll-Audit, gitignored, Urteil GO-mit-Auflagen)
   — daraus nur die noch OFFENEN Auflagen ziehen (v.a. H1 bis H4), nicht die ganze Liste.

Gib dann aus:

## Session-Briefing [Datum]

**Letzter Stand:** [1-2 Sätze aus HANDOFF.md TL;DR]

**Uncommitted:** [Änderungen oder "sauber"]

**Aktuelle Phase:** [aus HANDOFF.md — welche Phase ist dran?]

**Fokus diese Session:** [konkrete nächste Aufgabe aus HANDOFF.md]

Wenn die Phase Auswertung/Statistik/Folien ist, zusätzlich (sonst weglassen):

**Offene Audit-Auflagen:** [aus VERDICT.md die noch ungefixten HIGH-Befunde in je 1 Zeile; mindestens H1 nennen:
Headline-LLM-ttft 75/268/476 ms ist Predeploy-Pilot, nicht reproduzierbar aus der Kampagne; maßgeblich
Voll-Kampagne (56 von 56 Slots, A4) ~67/279/487 ms (~7,3×, gepoolt 8,3×); C1-Ordnung davon unberührt. Falls
VERDICT.md fehlt: "Audit-Verdict gitignored, nicht im Repo — H1-Zahlen-Wording vor dem Schreiben prüfen."]

**Offene Entscheidungen:** [aus HANDOFF.md, je 1 Zeile: Arbeitstitel final wählen; Zweitprüfer-Antwort
Prof. Färber abwarten; finale Headline-Zahlen aus der Vollkampagne (56/56, abgeschlossen) einsetzen]

**Auswertungs-Disziplin (SSOT `setup/messprotokoll.md`):** Aggregation A4 (Median der Slot-Mediane, nicht
gepoolt) + Bootstrap-CI; IP-Feld-Regel + C1-Logik beachten; Latenz nur success-only, Verfügbarkeit eigene Achse;
nur EC2-L1 (nicht der macOS-Dev-Lauf in `data/layer1/`); `ttl_ms` existiert nicht; Timeouts per Teilstring
(`ReadTimeout`) bucketieren, nicht `error=='timeout'`.

Halte den Pflichtteil (bis Fokus) unter 12 Zeilen, knapp und faktisch. Die Zusatzzeilen nur in der
Auswertungs-/Statistik-/Folien-Phase ausgeben. Keine Erklärungen, nur Fakten.

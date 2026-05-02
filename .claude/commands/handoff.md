Lies den aktuellen Projektstand:
- CLAUDE.md
- HANDOFF.md (falls vorhanden)
- analysis/ — welche Notebooks gibt es, was wurde zuletzt analysiert?
- git log --oneline -5 (die letzten Commits)

Schreibe dann einen Handoff-Eintrag in HANDOFF.md. Ersetze den Inhalt vollständig mit einem aktuellen Stand.

Format:

```markdown
# Handoff — Aktueller Arbeitsstand

> Diese Datei wird von `/handoff` am Session-Ende aktualisiert.
> Sie wird automatisch in jeden neuen Chat geladen (via CLAUDE.md).

## Letzter Stand

[Datum + 2–3 Sätze: Was wurde in dieser Session gemacht?]

## Aktuelle Fokus-Aufgabe

[Was ist konkret als nächstes dran — eine Aufgabe, nicht eine Liste]

## Letzte Entscheidungen

[Entscheidungen aus dieser oder der letzten Session, die den Kurs beeinflussen]

## Offene Fragen / Blockaden

[Was ist unklar, was wartet auf externe Faktoren, was muss noch geklärt werden]
```

Frag mich vor dem Schreiben kurz: "Was war der Fokus dieser Session und was ist als nächstes geplant?" — damit der Eintrag stimmt und nichts Wichtiges fehlt.

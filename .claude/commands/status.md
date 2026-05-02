Lies das aktuelle Projekt und gib einen präzisen Statusbericht. Lies folgende Quellen:

1. CLAUDE.md (Gesamtkontext)
2. notes/anbieter_auswahl.md (Provider-TODOs)
3. notes/layer2_first_capture.md (Layer-2-Stand)
4. measurements/config.py (konfigurierte Provider)
5. .env.example (welche API-Keys vorhanden sind)
6. data/layer3/ — zähle die JSONL-Dateien und schätze den Zeitraum (älteste/neueste Datei)
7. data/layer1/ — zähle die JSONL-Dateien

Dann gib aus:

## Projektstand [Datum heute]

**Datenlagen:**
- Layer 1: X Dateien, Zeitraum Y–Z
- Layer 2: X PCAP(s)
- Layer 3: X Dateien, ca. N Records, Zeitraum Y–Z

**Provider-Coverage:**
- Konfiguriert (config.py): [liste alle 9]
- Gemessen (Layer 3): [welche haben tatsächlich Daten]
- Fehlende API-Keys: [aus .env.example + anbieter_auswahl.md TODOs]

**Offene TODO-Blöcke** (aus notes/):
- [ ] ... (nur nicht-abgehakte Items)

**Methodische Baustellen** (aus CLAUDE.md):
- ...

**Empfohlene nächste Schritte** (priorisiert, max. 3):
1. ...
2. ...
3. ...

Halte den Report auf das Wesentliche. Keine langen Erklärungen.

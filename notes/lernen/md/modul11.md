# Modul 11 — Provider-Matrix & „warum US?"

**Ziel:** Verteidigen, warum genau diese 9 Anbieter — und warum überwiegend US-gehostet, ohne dass das ein Auswahl-Fehler ist.

## 11.1 Pipeline & die 9 Endpunkte

> Sprache rein → **STT** → Text → **LLM** → Antwort → **TTS** → Sprache raus

Pro Kategorie 3 Anbieter = 9 Endpunkte. Bauplan jeder Kategorie: **US-Anbieter + EU-naher Kontrast**.

| Kategorie | US-Anbieter | EU-naher Kontrast |
|-----------|-------------|-------------------|
| **STT** | Deepgram, Rev.ai | **Azure** (Italy North) |
| **LLM** | OpenAI, Groq | **Mistral** (Frankreich) |
| **TTS** | Deepgram, OpenAI | **Azure** (Italy North) |

## 11.2 Warum genau diese 9

Drei Kriterien: (1) marktreif/kommerziell, (2) echte **Streaming-API**, (3) roher Protokollzugang (kein SDK, das die Messung verfälscht). Plus je ein EU-naher Anbieter, um Geografie *testen* zu können.

## 11.3 Warum überwiegend US — Befund, nicht Bias

Für STT/TTS gibt es in dieser Qualitäts-/Reifeklasse **praktisch keine EU-gehosteten kommerziellen Streaming-Anbieter**. Wer aus der EU baut, **muss** US-Engines nutzen.

**Kein Sampling-Bias**, weil: Ein Bias wäre, US absichtlich zu bevorzugen *trotz* guter EU-Alternativen. Hier wurden EU-Anbieter *gesucht* — es gibt keine passenden. Die Auswahl bildet die **reale Marktlage** ab → „überwiegend US" ist selbst ein **Eingangsbefund** (gehört in Limitations/Diskussion). Stützt die Forschungsfrage: Die Provider-Wahl wird nicht durch Geografie/Datenresidenz bestimmt, sondern durch Engine-Qualität.

## 11.4 Rolle von Mistral & Azure (Geografie-Kontrollpunkte)

- **Mistral (FR):** einziger marktreifer EU-LLM, bewusst gesetzt — macht die **Geografie-Inversion** sichtbar (langsamer als US-Groq, beide am FRA-Edge).
- **Azure (Italy North):** echter EU-naher Host (~11 ms, kein CDN) — Beleg, dass niedrige RTT auch ein echter naher Host sein kann; schnellstes TTS.

Ohne diese zwei → nur US-Anbieter, Geografie-Frage gar nicht stellbar.

## 11.5 Modell-Pinning

Modell-Version festgenagelt (z.B. `gpt-4o-mini-2024-07-18`, `llama-3.1-8b-instant`, `mistral-small-2603`), sonst stiller **Modell-Drift** hinter gleichem Namen. Zusätzlich `effective_model` (vom Server zurückgemeldet) pro Call geloggt → Wechsel sample-genau sichtbar.

## 11.6 Heterogenität ist Befund, kein Mangel

Die 9 funktionieren unterschiedlich (Edge/Host, Protokolle, Regionen). Homogenisieren wäre falsch: (1) Heterogenität ist die Realität; (2) sie *ermöglicht* erst den C1-Beleg (gleiche LLM-Edge = Kontrollexperiment); (3) nicht jeder Anbieter muss jede Frage beantworten.

| Frage | Wer trägt bei |
|-------|---------------|
| **A — C1 (Kausal):** Netz vs. Backend? | LLM + OpenAI-TTS; **STT nicht** |
| **B — deskriptiver Vergleich** | alle 9 |
| **C — E2E-Pipeline** | alle 3 Kategorien |

> **Kernsatz:** Nicht *trotz*, sondern teils *wegen* der Unterschiede behalten. Nicht „vergleichbar/nicht", sondern: welche Frage beantwortet welcher Datensatz.

## Prüf-Fragen

1. Warum genau diese 9 — Kriterien + gemeinsamer Bauplan jeder Kategorie?
2. Warum überwiegend US — und warum *kein* Sampling-Fehler, sondern Befund?
3. Welche Rolle spielen Mistral und Azure — was ginge ohne sie nicht?

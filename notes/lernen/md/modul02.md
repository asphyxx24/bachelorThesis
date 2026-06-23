# Modul 2 — Die Forschungsfrage

**Ziel:** Die Frage wortgetreu wiedergeben, ihre *Offenheit* als Stärke verteidigen, und belegen, ab wann Latenz ein Problem ist.

## 2.1 Der Wortlaut

> *In welchem Maße erklären **Netzwerk- und Infrastruktureigenschaften** (RTT, Protokoll, Hosting-Region) — im Vergleich zur **Backend-Verarbeitung der Engine** — die **Latenzunterschiede** zwischen kommerziellen Cloud-AI-APIs (STT, LLM, TTS) aus **EU-Perspektive**, und wie wirkt sich die **Provider-Wahl** auf die **Gesamtlatenz einer sequenziellen Cold-Start-Voice-Pipeline** aus?*

Schlüssel-Bauteil: **„in welchem Maße … im Vergleich zu …"** → die Frage vergleicht **Anteile** (Netz vs. Backend). Keine Ja/Nein-Frage, keine vorgeschriebene Richtung.

## 2.2 Offenheit = Stärke

Eine Frage ist wissenschaftlich nur sauber, wenn **beide** Antworten gültig wären:

- „Netz erklärt mehr" → gültig.
- „Netz erklärt weniger als das Backend" → gültig (und das Ergebnis).

Das Gegenteil wäre eine **Suggestivfrage** („Wie sehr beweist die Netznähe die Latenz?") → **Bestätigungsfehler** (confirmation bias): man kann sich beim Messen nur selbst bestätigen.

> **Glaubwürdigkeits-Trumpf:** Gerade weil deine Frage *gegen dich* hätte ausgehen können (Netz hätte dominieren können), ist „Backend dominiert" ein echtes Ergebnis — kein eingebautes.

## 2.3 Ab wann ist Latenz ein Problem? (Anker statt Bauchzahl)

Früher: willkürliche „1-Sekunde"-Schwelle, widersprach der eigenen Literatur (Mangel A5). Jetzt belegte Anker:

| Quelle | Aussage | Rolle |
|--------|---------|-------|
| **Stivers et al. (2009), PNAS** | Antwort-Lücken im Median ~200 ms, kulturübergreifend | **Soll-Wert** (natürlicher Gesprächstakt) |
| **Miller (1968) / Nielsen (1993)** | <0,1 s „sofort", <1 s „Gedankenfluss", <10 s „Aufmerksamkeit" | Interaktions-Schwellen |
| **ITU-T G.114** | ≤150 ms bevorzugt, 150–400 ms akzeptabel, >400 ms inakzeptabel | **Toleranzgrenze** |

## 2.4 Die Brücke zur Kernfrage

Die Strecke EU → Edge misst nur ~1 ms — **weit** innerhalb der 150 ms von G.114. Also ist **nicht das Netz** der Engpass im Konversationsbudget, sondern die Backend-Hunderte-ms. Der Relevanz-Anker motiviert direkt die Kernfrage (Modul 3).

## Prüf-Fragen

1. Warum ist die Offenheit der Frage gut für die Glaubwürdigkeit — was wäre das faule Gegenteil?
2. Ab wann ist Latenz spürbar/ein Problem — nenne zwei Anker mit Größenordnung. Bonus: Warum war „1 Sekunde" ein Problem?

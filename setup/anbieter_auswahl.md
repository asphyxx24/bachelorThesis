# Anbieter-Auswahl

> Angelegt: 2026-06-14 · Teil des Neuaufbaus (s. `../NEUANFANG.md`)
>
> Diese Datei legt fest, **welche Anbieter** wir für **welche Dienste** messen — und **warum**.
> Die Begründung pro Wahl ist bewusst ausführlich, weil genau das (nachvollziehbare Auswahl)
> der Punkt ist, an dem der Prof bisher Vertrauen vermisst hat.

## Pipeline-Scope

Vollständige Echtzeit-Voice-Pipeline mit **drei Kategorien**, sequenziell:

```
Sprache rein  →  [STT]  →  Text  →  [LLM]  →  Antwort-Text  →  [TTS]  →  Sprache raus
```

Pro Kategorie **3 Anbieter** → **9 Mess-Endpunkte** insgesamt.

## Auswahl-Matrix

| Kategorie | Anbieter | Modell | Region (deklariert) | Protokoll |
|-----------|----------|--------|---------------------|-----------|
| **STT** | Deepgram | Nova-3 | USA (Multi-DC, DNS-Round-Robin) | WebSocket |
| **STT** | Rev.ai | English | USA | WebSocket |
| **STT** | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| **LLM** | OpenAI | gpt-4o-mini | USA (GPU) | HTTPS + SSE |
| **LLM** | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS + SSE |
| **LLM** | Mistral | mistral-small-2603 | EU / Frankreich | HTTPS + SSE |
| **TTS** | Deepgram | Aura-2 | USA (Multi-DC, DNS-Round-Robin) | HTTPS Streaming |
| **TTS** | OpenAI | tts-1 | USA | HTTPS Streaming |
| **TTS** | Azure | Standard Neural | Italien (Italy North) | HTTPS Streaming |

> „Region (deklariert)" = die vom Anbieter angegebene Hosting-Region. Wo die Verbindung **physisch**
> terminiert (Anycast/Edge), wird im Layer-1-Schritt separat aufgelöst und kann abweichen.

## Begründung je Kategorie

### STT — Deepgram, Rev.ai, Azure
- **Deepgram (Nova-3):** Marktführend bei Streaming-STT-Latenz, US-gehostet über mehrere Rechenzentren
  mit kurz-TTL-DNS-Round-Robin (rotiert `md1`/`sac1`/`sv1`, **kein** Anycast/GeoDNS) → guter
  Kontrast „weit weg, aber schnell". Die RTT-Streuung (~102–148 ms) erklärt sich aus dem je Messung
  verbundenen DC; deshalb wird die verbundene Ziel-IP pro Run mitgeloggt (s. `messprotokoll.md`, A5).
- **Rev.ai (English):** Zweiter US-Anbieter, reifes English-Streaming-Modell, **roher WebSocket-Zugang
  ohne SDK** → methodisch konsistent zu Deepgram/Azure. *(Ersetzte ursprünglich AssemblyAI, dessen API
  Echtzeit-Pacing erzwang — damals, als alle STT gedumpt wurden, ein Inkonsistenz-Argument. **Seit
  2026-06-16 pacen wir ohnehin alle drei STT einheitlich** (1×-Realtime, für `ttfp`-Fairness —
  s. `messprotokoll.md`); das Pacing-Argument gegen AssemblyAI ist damit obsolet, Rev.ai bleibt wegen
  reifem Modell, rohem WS-Zugang und bereits geladenem Guthaben.)*
- **Azure (Standard Neural):** Der EU-nahe Gegenpol (Italy North), echtes EU-RZ (~11 ms RTT, kein CDN).
  Wichtig als geografisch naher STT-Vergleichspunkt. *(Hinweis: Auf der fairen Metrik `ttfp` ist Azure
  **nicht** langsamer als das US-Deepgram — gleichauf. Die im Dump beobachtete „STT-Langsamkeit" war
  Bulk-Verarbeitung, kein Engine-/Geo-Nachteil; der C1-Kernbeleg ruht auf der LLM-Edge-Achse, nicht auf STT —
  s. `messprotokoll.md` → „STT-Primärmetrik" + „Korrekte C1-Logik".)*

### LLM — OpenAI, Groq, Mistral
- **OpenAI (gpt-4o-mini):** US-GPU-Referenz, der De-facto-Standard.
- **Groq (llama-3.1-8b-instant):** US, aber spezielle LPU-Hardware → testet, ob Backend-Architektur
  (nicht Geografie) die Latenz dominiert.
- **Mistral (mistral-small):** Der **EU-Anbieter** (Frankreich). Wichtig als geografisch naher
  Vergleichspunkt — und für die Verfügbarkeits-/Output-Dimension relevant.

### TTS — Deepgram, OpenAI, Azure
- **Deepgram (Aura-2)** & **OpenAI (tts-1):** US-Streaming-TTS.
- **Azure (Standard Neural):** **Schnellstes TTS** (`ttfa` ~96 ms) trotz US-Konkurrenz (OpenAI ~917 ms) —
  empirisch sehr robust. Das ist der **zweite** C1-Beleg (Kernbeleg ist die LLM-Edge-Achse, s. `messprotokoll.md`).
  Die within-Azure-Gegenüberstellung STT (~1 s bis erstes Wort) vs. TTS (~96 ms) bleibt höchstens eine
  **Workload-Beobachtung** (5-s-Audio rein vs. Kurzsatz raus), **nicht** „reine Engine-Geschwindigkeit".

## Warum überwiegend US-Anbieter? (Das ist Teil des Befundes, kein Mangel)

Für STT und TTS existieren in dieser **Qualitäts-/Reife-Klasse praktisch keine EU-gehosteten
kommerziellen Anbieter** mit Streaming-API. Wer aus der EU eine produktive Voice-Pipeline baut, **muss**
auf US-Engines zurückgreifen. Genau das stützt die Forschungsfrage: Die Provider-Wahl wird **nicht**
durch Geografie/Datenresidenz dominiert, sondern durch die verfügbare Engine-Qualität. Der einzige
ausgereifte EU-LLM-Vertreter (Mistral) ist daher bewusst gesetzt; Azure dient als EU-naher
Infrastruktur-Gegenpol für STT/TTS.

→ Die „EU-Anbieter fehlen"-Realität ist also ein **Eingangsbefund**, der in der Limitations- und
Diskussions-Sektion explizit benannt wird.

## Offene Punkte für später

- Modell-Versionen/Endpunkte exakt fixieren und mit Datum festhalten (Reproduzierbarkeit).
- Genaue API-Endpunkt-Hostnames je Anbieter sammeln (Grundlage für Layer-1-Auflösung).
- Authentifizierung/API-Keys je Anbieter (welche Accounts, welche Limits).

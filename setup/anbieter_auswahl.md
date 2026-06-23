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
  Kontrast „weit weg, aber schnell". Die RTT-Streuung (~101–148 ms je nach getroffenem DC) erklärt sich aus dem
  je Messung verbundenen Rechenzentrum; deshalb wird die verbundene Ziel-IP pro Run mitgeloggt (s. `messprotokoll.md`, A5).
  Bestätigt per-IP über die Kampagne (56 von 56 Slots (A4), 6 IPs, alle US: AS6461 Zayo ×3 + AS174 Cogent ×3;
  s. `../data/audit_20260618/{l1_rtt_per_ip.md, asn_per_ip.md}`). Bemerkenswert: der langsamere `ttft`-Modus läuft
  über die Cogent-IPs (38.68.64.131/.132), die die *niedrigere* RTT (~101 ms) haben → der langsame Modus ist
  Backend/DC, nicht Netz (direkter C1-Beleg innerhalb eines Anbieters).
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
- **Groq (llama-3.1-8b-instant):** US, aber spezielle LPU-Hardware → testet, ob das **Backend insgesamt
  (Inferenz-HW + Modellgröße/-Architektur), nicht Geografie** die Latenz dominiert. *(Caveat: Groq variiert
  HW UND Modellgröße (8B) gemeinsam → „Backend/Engine" als Bündel; die im Sinn von C1 („Backend statt Geografie")
  tragende Aussage ist die **negative**: die Netznähe erklärt die Spreizung nicht. OpenAI, Groq und Mistral
  terminieren alle bei Cloudflare Frankfurt @ ~1 ms (100 % des LLM-Traffics gemessen + ASN-belegt, AS13335;
  s. `../data/audit_20260618/{l1_rtt_per_ip.md, asn_per_ip.md}`).)*
- **Mistral (mistral-small):** Der **EU-Anbieter** (Frankreich). Wichtig als geografisch naher
  Vergleichspunkt — und für die Verfügbarkeits-/Output-Dimension relevant.

### TTS — Deepgram, OpenAI, Azure
- **Deepgram (Aura-2)** & **OpenAI (tts-1):** US-Streaming-TTS.
- **Azure (Standard Neural):** **Schnellstes TTS** (`ttfa` ~94 ms) — empirisch sehr robust. Das ist der
  **zweite** C1-Beleg (Kernbeleg ist die LLM-Edge-Achse, s. `messprotokoll.md`). Präzisierung: OpenAI-TTS
  terminiert bei **Cloudflare Frankfurt** (162.159.140.245 / 172.66.0.243, AS13335, ~1 ms connect — dieselben IPs
  wie OpenAI-LLM; s. `../data/audit_20260618/asn_per_ip.md`) und ist damit eine **zweite identical-edge-Instanz**
  (`ttfa` ~942 ms, ~941 ms connect-exklusiv = reines Backend), die C1 stützt. „Trotz US-Konkurrenz" gilt daher nur gegenüber
  **Deepgram-TTS** (`ttfa` ~516 ms, echter US-connect ~280 ms). Die within-Azure-Gegenüberstellung STT (~1 s) vs. TTS (~94 ms)
  bleibt höchstens eine **Workload-Beobachtung**, **nicht** „reine Engine-Geschwindigkeit".

## Warum überwiegend US-Anbieter? (Das ist Teil des Befundes, kein Mangel)

Für STT und TTS existieren in dieser **Qualitäts-/Reife-Klasse praktisch keine EU-gehosteten
kommerziellen Anbieter** mit Streaming-API. Wer aus der EU eine produktive Voice-Pipeline baut, **muss**
auf US-Engines zurückgreifen. Genau das stützt die Forschungsfrage: Die Provider-Wahl wird **nicht**
durch Geografie/Datenresidenz dominiert, sondern durch die verfügbare Engine-Qualität. Der einzige
ausgereifte EU-LLM-Vertreter (Mistral) ist daher bewusst gesetzt; Azure dient als EU-naher
Infrastruktur-Gegenpol für STT/TTS.

→ Die „EU-Anbieter fehlen"-Realität ist also ein **Eingangsbefund**, der in der Limitations- und
Diskussions-Sektion explizit benannt wird.

## Warum an dieser heterogenen Auswahl festhalten — die Unterschiede SIND der Befund

Die neun Anbieter funktionieren technisch **unterschiedlich**: manche terminieren an einem CDN-Edge
(~1 ms), manche an einem echten Host (Azure ~11 ms, US-Anbieter ~140 ms); verschiedene Protokolle
(WebSocket / SSE / HTTPS-Streaming), verschiedene TLS-Versionen, verschiedene Hosting-Regionen. Es läge
nahe, die Auswahl zu „homogenisieren" (nur gleich erreichbare Anbieter). Das wäre ein **Fehler** — aus drei Gründen:

1. **Heterogenität ist Realität, nicht Störung.** Wer aus der EU eine produktive Voice-Pipeline baut, hat
   genau diese gemischte Landschaft vor sich. Eine künstlich homogenisierte Auswahl würde eine Welt messen,
   die es nicht gibt. Die Unterschiede sind Teil dessen, was die Arbeit *beschreibt*.
2. **Gerade die Heterogenität ermöglicht den Kernbeleg.** Dass OpenAI/Groq/Mistral zufällig alle am selben
   Cloudflare-Edge terminieren, ist die Voraussetzung für das „natürliche Kontrollexperiment" zu C1 (gleiche
   Netzlage, trotzdem ~7,3× (gepoolt 8,3×) Latenz → Backend). Hätte man nach „gleichem Setup" gefiltert, wäre dieser Beleg nie entstanden.
3. **Nicht jeder Anbieter beantwortet jede Frage — und das ist sauber so.** Die Arbeit stellt drei verschiedene
   Fragen; die Auswahl bedient sie unterschiedlich:

| Frage | Worum es geht | Welche Daten tragen bei |
|---|---|---|
| **A — C1 (Kausal):** Erklärt Netz oder Backend die Latenz*spreizung*? | braucht „identical-edge"-Vergleich **und** echte Spreizung | **LLM** (3× gleiche Edge, ~7,3×) voll · **OpenAI-TTS** (gleiche Edge, `ttfa` ~942 ms) als 2. Beleg · **STT gar nicht** |
| **B — Deskriptiver Vergleich:** Wie schnell/zuverlässig ist jeder Anbieter, wie sieht sein Setup aus? | nur saubere Messung *pro* Anbieter | **alle 9** voll |
| **C — E2E-Pipeline:** Wie groß ist die Gesamt-Antwortlatenz? | alle Stufen der Kette | **alle 3 Kategorien** zwingend |

Konkret: Über einen Anbieter, der am Edge terminiert, lässt sich keine Netz-vs-Backend-Aussage treffen — das
**benennt** man pro Anbieter, statt ihn rauszuwerfen. STT trägt zu C1 (Frage A) nichts bei (auf der fairen
Metrik `ttfp` sind die vergleichbaren Anbieter gleichauf, und keiner sitzt an einer *kontrollierten gemeinsamen*
Edge), bleibt aber für den deskriptiven Vergleich (B) und die Pipeline-Gesamtlatenz (C) **voll dabei**.

> **Kernsatz fürs Gespräch:** Die Anbieter wurden nicht *trotz* ihrer Unterschiede behalten, sondern teils
> *wegen* ihnen. Die wissenschaftlich saubere Haltung ist nicht „vergleichbar / nicht vergleichbar", sondern:
> *welche* Frage beantwortet *welcher* Datensatz — und welche eben nicht. Heterogenität ist Befund, kein Mangel.

## Offene Punkte für später

- Modell-Versionen/Endpunkte exakt fixieren und mit Datum festhalten (Reproduzierbarkeit).
- Genaue API-Endpunkt-Hostnames je Anbieter sammeln (Grundlage für Layer-1-Auflösung).
- Authentifizierung/API-Keys je Anbieter (welche Accounts, welche Limits).

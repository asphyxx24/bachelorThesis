# Modul 3 — C1 „Backend statt Geografie" (der Kern) ⭐

**Ziel:** Die Kernaussage, den stärksten Beleg und die ehrliche Grenze verteidigen. Das ist die Prüfungsstelle, an der die ganze Arbeit hängt.

## 3.1 Die Kernaussage — negativ formuliert

Umgangssprachlich „Backend statt Geografie". Die **wasserdichte** Form ist die **negative**:

> **„Netznähe erklärt die Latenzspreizung *nicht*."**

- Die **negative** Aussage ist direkt aus den Daten beweisbar.
- Die **positive** Aussage („das Backend ist schuld") ist eine Schlussfolgerung mit Störfaktor (3.6).

Im Gespräch immer zuerst die negative Aussage verteidigen — sie ist uneinnehmbar.

## 3.2 Begriffe

- **Edge / CDN-Edge:** Knoten (z.B. Cloudflare), der die Verbindung *nahe Frankfurt* terminiert, nicht am US-Server. Du redest mit einer Maschine ~1 ms entfernt.
- **ASN (Autonomous System Number):** Kennung eines Betreibernetzes. **AS13335 = Cloudflare** — belegt, nicht vermutet.

## 3.3 Der schärfste Beleg: LLMs als natürliches Kontrollexperiment

Alle drei LLM-Anbieter terminieren bei Cloudflare FRA (AS13335, ~1 ms) — für **100 % des Traffics** gemessen + ASN-belegt:

| Anbieter | Region | Edge | RTT | `ttft` |
|----------|--------|------|-----|--------|
| Groq | USA | Cloudflare FRA | ~1 ms | **~67 ms** |
| Mistral | EU/FR | Cloudflare FRA | ~1 ms | **~279 ms** |
| OpenAI | USA | Cloudflare FRA | ~1 ms | **~487 ms** |

Netzvariable **konstant**, trotzdem **~7,3×** (gepoolt 8,3×) Streuung.

> **Schlüsselsatz:** Ist die Netzdistanz für alle drei identisch (~1 ms), kann sie 7,3× nicht erklären. Die Differenz entsteht hinter der Edge — im Backend.

## 3.4 Geografie endgültig ausgeschlossen

1. **Per-IP invariant** — kein Artefakt einer guten/schlechten IP.
2. **Geografie invertiert:** EU-Mistral ist *langsamer* als US-Groq. Die Geografie-Hypothese sagt „näher = schneller" — beobachtet wird das Gegenteil → **K.o.**

**Einwand „die Edge verdeckt das Backend":** Stimmt — aber die negative Aussage braucht das Backend nicht zu *sehen*. Sie braucht nur: der Teil *vor* dem Vorhang (EU-Nähe) ist für alle gleich. Zusatz: Auch der Weg *hinter* dem Vorhang (CF→US) ist für Groq und OpenAI gleich, sie differieren trotzdem ~370 ms → präzise: **„nicht die EU-Edge-Nähe"**, nicht „gar kein Netz".

## 3.5 Zahlen-Stolperstein (H1)

| Datensatz | Werte | Status |
|-----------|-------|--------|
| Predeploy-Pilot | 75 / 268 / 476 ms | NICHT verwenden (reproduziert aus keinem Kampagnendatensatz) |
| Voll-Kampagne | ~67 / 279 / 487 ms (~7,3×, gepoolt 8,3×) | **maßgeblich** (56 von 56 Slots, A4, success-only; Bootstrap-CI noch ausstehend) |

## 3.6 Belege-Übersicht (nicht symmetrisch über die Kategorien!)

Ein Beleg ist nur sauber, wenn die Netzlage **konstant** ist („identical-edge").

| Beleg | Kategorie | identical-edge? | Stärke |
|-------|-----------|-----------------|--------|
| 3 LLMs gleiche Edge, ~7,3× | LLM | ✅ | **stark (Haupt)** |
| OpenAI-TTS gleiche Edge, ~942 ms | TTS | ✅ | **stark (Zweit)** |
| Azure schnellstes TTS | TTS | ❌ (andere Netzlage) | nur Illustration |
| Deepgram-interne Inversion | STT/TTS | ✅ | Nebenbeleg |
| STT allgemein | STT | — | **kein Beleg** |

**STT trägt C1 nicht** (sagst du *aktiv*): auf der fairen Metrik keine Spreizung (Azure ≈ Deepgram), keine kontrollierte gemeinsame Edge. Aber STT ist **nicht nutzlos** — nur für die Headline blind; für deskriptiven Vergleich + E2E-Pipeline voll dabei.

## 3.7 Der Confound — warum „Engine" nicht in den Titel

Groq ist *gleichzeitig* kleinstes Modell **und** spezielle Hardware (LPU). Untrennbar → **Confound**. Deshalb: **„Backend (HW + Modell)"**, nie „Rechenleistung allein". „Engine" im Titel = Overclaim → bleibt draußen. Der Titel bleibt bei der negativen Aussage.

## Prüf-Fragen

1. Warum ist der LLM-Beleg schärfer als der TTS-Beleg?
2. Warum trägt STT nichts zu C1 bei — und warum heißt das nicht „nutzlos"?
3. Warum ist „Mistral (EU) langsamer als Groq (US)" ein K.o. für Geografie?
4. Warum darf „Engine" nicht in den Titel — was ist der Confound?

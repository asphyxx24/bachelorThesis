> Quelle: ultracode STT-Methodik-Recherche (Workflow wltinc76u) — 11 Agenten, web-gestützt gegen offizielle Anbieter-Docs, adversarial verifiziert. Run 2026-06-16.

# Entscheidungs-Bericht: Faire STT-Latenzmessung (Deepgram Nova-3 / Rev.ai / Azure Speech)

**Kernproblem in einem Satz:** Die aktuelle STT-Metrik `ttft = t_first_final − t_first_chunk` misst nicht die Engine-Geschwindigkeit, sondern *Engine + die anbieterspezifische Stille-/Endpointing-Politik* — und der Code löst die Finalisierung bei den drei Anbietern *ungleich* aus. Beides zusammen untergräbt genau die Hälfte des Kernbefunds C1 (STT/TTS-Inversion bei Azure).

**Was die echten Daten zeigen (aus `/tmp/campaign_summary.txt`):**
- Azure STT: `ttft` p50 = 1722 ms, p90 = 1731, p99 = 1741 → praktisch konstant (Spannweite < 30 ms über 400 Calls). Das ist das Signaturmuster eines **festen serverseitigen Stille-Timeouts**, nicht variabler Rechenzeit.
- Deepgram STT: `ttft` p50 = 605 ms, p99 = 3735 → echte variable Engine-Zeit (breite Verteilung).
- Rev.ai STT: `ttft` p50 = 1355 ms, p99 = 1499 → relativ eng, also ebenfalls teils politik-getrieben, aber weniger extrem als Azure.
- Zum Vergleich TTS: Azure ttfa p50 = 96 ms (schnellster), Deepgram 516, OpenAI 917 → **das ist die Inversion**: Azure langsamster STT, schnellster TTS.

---

## 1) Was kann jeder Anbieter? (verifiziert aus der Recherche)

| Fähigkeit | Deepgram Nova-3 | Rev.ai (machine) | Azure Speech (Italy North) |
|---|---|---|---|
| **Endpointing-Schwelle konfigurierbar?** | **Ja** — `endpointing=<ms>` (Default 10 ms), abschaltbar via `endpointing=false` ¹ | **Nein** — kein Stille-/Pause-/VAD-Parameter; nur `max_segment_duration_seconds` (5–30 s) als Obergrenze ² | **Teils** — `Speech_SegmentationSilenceTimeoutMs` (100–5000 ms, SDK-Default 500 ms), aber **nur als SDK-Property dokumentiert**, nicht für den rohen WebSocket (den die Arbeit nutzt) ³ |
| **Echtes Force-Finalize?** | **Ja** — `{"type":"Finalize"}` flusht gepuffertes Audio sofort, umgeht Endpointing ⁴ | **Bedingt** — `EOS` liefert finale Hypothese + schließt; *funktional* ein Flush, aber kein mid-stream Force ² | **Nein dokumentiert** — leere Audio-Message ist nur Stream-Ende; Finalisierung folgt weiter dem Stille-Timeout ³ |
| **Interim/Partials verfügbar?** | **Ja** — `interim_results=true` (Default false; **im Code aktuell `false`** ⁵) | **Ja** — Partials werden gesendet; `detailed_partials=true` für Zeitstempel ² | **Ja** — `speech.hypothesis`-Messages (Recognizing) ³ |

Quellen: ¹ developers.deepgram.com/docs/endpointing · ² docs.rev.ai/api/streaming/requests · ³ learn.microsoft.com/.../how-to-recognize-speech · ⁴ developers.deepgram.com/docs/finalize · ⁵ verifiziert in `config.py:68` und `api_endpunkte.md:19` (`interim_results=false`).

**Klartext zu den Doku-Lücken:**
- **Rev.ai hat keine angleichbare Endpointing-Schwelle.** Es gibt schlicht keinen Parameter, mit dem man Rev.ai auf denselben Stille-Wert wie Deepgram/Azure setzen könnte. → Eine Variante "gleiches Endpointing bei allen drei" ist mit Rev.ai **nicht sauber machbar**.
- **Azure-Timeout über rohes WebSocket: nicht verlässlich setzbar.** Microsoft dokumentiert den Parameter nur fürs SDK. Theoretisch ginge er über die `speech.context`-Message (die der Code in `_azure_config_msg` schon sendet), aber das ist *undokumentiert/unsupported* — nur durch eine Drittanbieter-Integration belegt. → Nicht als gesicherter Hebel verwenden.
- **`priority` (Rev.ai) ist an die deprecated Engine `machine_v2` gebunden** und auf der heutigen `machine`/Reverb-Engine nicht garantiert wirksam. → Nicht als Engine-Lever verlassen, nur dokumentieren.

---

## 2) Drei konkrete faire Mess-Varianten

### Variante A — First-Partial-Latenz (`ttfp`) [endpointing-frei]
- **Was wird gemessen:** Zeit bis zum *ersten vorläufigen Transkript* (erstes Lebenszeichen der Engine), `ttfp = t_first_partial − t_first_chunk`. Partials kommen **vor** jeder Stille-Erkennung → die Endpointing-Politik fliegt komplett raus.
- **Exakte Config je Anbieter:**
  - Deepgram: `interim_results=true` setzen (aktuell `false`!); erstes `Results`-Event mit `is_final:false` nehmen.
  - Rev.ai: keine Änderung am Stream nötig; erste Message vom Typ `partial` nehmen (optional `detailed_partials=true`).
  - Azure: erste `speech.hypothesis`-Message nehmen (statt nur `speech.phrase` zu lesen).
- **Fair über alle 3?** Ja — alle drei liefern Partials, keiner braucht einen anbieterspezifischen Trick.
- **Passt zur Forschungsfrage?** Ja, und macht die STT-Seite *symmetrisch zur TTS-Seite*: TTS-`ttfa` ist ohnehin "Zeit bis erstes Audio" (reine Engine-Reaktion). First-Partial ist das STT-Pendant — beide messen "Zeit bis erstes Engine-Lebenszeichen".
- **Code-Änderungen:** Mittel. In allen drei `_io_*`-Funktionen einen zweiten Zeitstempel `t_first_partial` loggen; bei Deepgram `interim_results=true` in `config.py`/`api_endpunkte.md`.
- **Schwäche:** Partials sind Zwischenstände niedriger Konfidenz, nicht das verwertbare Endergebnis. Allein zu schwach als alleinige These-Stütze.

### Variante B — Force-Finalize bei allen + Final-Latenz (`ttft_final`) [angeglichenes Ende-Signal]
- **Was wird gemessen:** Final-Transkript-Latenz, aber mit *einheitlichem* Stream-Ende-Signal statt nativem Endpointing.
- **Exakte Config je Anbieter:**
  - Deepgram: `{"type":"Finalize"}` + `{"type":"CloseStream"}` (Code macht das bereits).
  - Rev.ai: `EOS` (Code macht das bereits — das ist Rev.ais dokumentierter Flush).
  - Azure: hier liegt das Problem. Eine leere Audio-Message ist *kein* Force-Finalize → Azure wartet weiter sein Timeout ab (= die konstanten 1722 ms). Es gibt für rohes WebSocket **keinen verlässlichen Flush**. Der robusteste Pfad: den festen Offset transparent ausweisen (das gemessene konstante Plateau ist nachweislich Politik, nicht Engine).
- **Fair über alle 3?** **Nur teilweise.** Deepgram und Rev.ai lassen sich angleichen; Azure nicht (keine dokumentierte Flush-Aktion im rohen WS). Genau deshalb darf der jetzige Code — Deepgram-`Finalize` gegen Azure-Leeraudio — **nicht** als fairer Final-Vergleich verkauft werden. Das ist die zweite Unfairness aus dem Problem (Apples-to-Oranges auf Protokollebene).
- **Passt zur Forschungsfrage?** Bedingt — als *sekundäre* "Turn-Latenz unter nativer Politik", ehrlich als Engine+Politik-Mix etikettiert.
- **Code-Änderungen:** Klein (Code sendet die Signale schon). Wichtig ist die *Etikettierung*, nicht neuer Code.

### Variante C — Kontroll-Experiment: Azure-Timeout variieren [empirischer Confound-Beweis]
- **Was wird gemessen:** Eine kleine Zusatzserie, in der man bei Azure verschiedene Segmentation-Timeouts (z.B. 300 / 500 / 1000 ms) zu setzen versucht und prüft, ob `ttft` mitskaliert.
- **Exakte Config:** `segmentationSilenceTimeoutMs` über die `speech.context`-Message (undokumentierter Pfad — vorher empirisch verifizieren, ob er greift).
- **Fair über alle 3?** Betrifft nur Azure; ist kein Vergleich, sondern ein *Beweis*.
- **Passt zur Forschungsfrage?** Stark — wenn `ttft` mit dem gesetzten Timeout mitwandert, ist *empirisch belegt*, dass die 1722 ms Politik und nicht Engine sind. Falls der Pfad nicht greift: Der konstante CV von 0,9 % über 400 echte Calls ist selbst schon ein starker Beleg für ein festes Timeout.
- **Code-Änderungen:** Klein, aber Pfad unsicher → als optionales Experiment, nicht als Pflicht.

**(Optional, Variante D — Batch/Pre-Recorded-API)** als reine Engine-Zeit-Referenz (Deepgram Pre-Recorded `/v1/listen`, Rev.ai Async `/jobs`, Azure Fast Transcription). Alle drei existieren und arbeiten schneller als Echtzeit, ohne Streaming-Endpointing. **Aber:** anderes Produkt/Regime (kein ttft, andere Hardware/Queue, nicht echtzeit-relevant) → nur als nachrangiger Cross-Check, **nicht** als Ersatz der Streaming-Primärmetrik.

---

## 3) Empfehlung

**Primär A (First-Partial) + sekundär B (Final unter angeglichenem Signal), beide getrennt berichtet — plus C als Kontroll-Beweis, soweit der Azure-Pfad greift.**

Begründung:
1. **A beseitigt den Confound, statt ihn zu notieren.** Endpointing ist *keine* Engine-Eigenschaft, sondern Stille-Politik. Da C1 eine *Engine*-Aussage ist, muss die Metrik Engine isolieren — First-Partial tut das per Konstruktion. Deepgram schreibt das in seiner eigenen Doku sogar so vor ("Use only interim transcripts … finals conflate transcript latency with EOT latency").
2. **A macht STT und TTS symmetrisch.** Beide Hälften der Inversion ruhen dann auf "Zeit bis erstes Engine-Token" — methodisch eine Achse statt zweier inkompatibler.
3. **Getrennt berichten statt eine Zahl.** Etablierter Konsens (Artificial Analysis, Gladia): pro Meilenstein (Partial / Final) eigene Spalten, nie verschmolzen. Das ist genau der Sprung von "etikettieren" (so steht es heute in `messprotokoll.md:298`) zu "messtechnisch beseitigen".

**Trade-offs ehrlich:**
- **A allein ist nicht genug** (Partials sind low-confidence) → B liefert die "echte" Final-Latenz, muss aber ehrlich als Engine+Politik-Mix etikettiert werden.
- **B bleibt für Azure nicht perfekt angleichbar** (kein dokumentierter Flush im rohen WS). Das ist eine echte Grenze — aber sie wird *kontrolliert* (über A umgangen, über C belegt), nicht verschwiegen.
- **Rev.ai hat keine Endpointing-Schwelle** → eine "gleiches Endpointing bei allen" Variante ist gar nicht baubar. A umgeht das, weil First-Partial keinen Endpointing-Parameter braucht.
- **Bezugspunkt:** `ttfp` wird ab erstem Audio-Chunk gemessen (Stream-Start, 1×-realtime getaktet — s. Korrektur 1 im Status unten), nicht ab einem externen VAD-Endpunkt wie bei Artificial Analysis/Daily.co. Das ist eine *bewusste, zu deklarierende Abweichung* — im Geist gleich (getrennte Milestones, endpointing-frei), im Bezugspunkt verschieden. Nicht behaupten, es sei "deckungsgleich" mit AA.
- **Aufwand:** moderat. Hauptarbeit: zweiten Zeitstempel in den drei `_io_*`-Funktionen, `interim_results=true` bei Deepgram, getrennte Spalten in der Auswertung. Eine **Neumessung** der STT-Kampagne ist nötig, da die alten Daten Deepgram mit `interim_results=false` haben.

**Wichtig für C1:** Auch unter A/B bleibt Azures STT-Nachteil real bestehen — der Stille-Timeout ist *nur im aktuellen Setup* ein Confound, nicht der Grund für Azures TTS-Vorteil. Die Inversion ist also methodisch verteidigbar erhaltbar; sie wird durch die Bereinigung *härter*, nicht weicher.

---

## 4) Verteidigbarkeit gegenüber Prof. Wählisch

**Ein-Satz-Verteidigung:** "Ich berichte die First-Partial-Latenz als Engine-Geschwindigkeits-Metrik — endpointing-unabhängig und vom Anbieter (Deepgram-Doku) selbst als die korrekte Latenzgröße vorgeschrieben — und zusätzlich die Final-Latenz unter angeglichenem Stream-Ende-Signal, explizit als Mix aus Engine und nativer Turn-Detection-Politik etikettiert; den bisherigen Deepgram-only-Finalize-Vorteil habe ich entfernt bzw. transparent gemacht."

Warum das trägt:
- **Es löst genau seine Beanstandung** ("er vertraut den Daten nicht, weil Methodik nicht dargelegt"). Hier wird der Confound nicht nur benannt, sondern *gemessen weg* (A) und *empirisch belegt* (C).
- **Es ist Stand der Technik**, nicht erfunden: getrennte Partial/Final-Spalten (Artificial Analysis), per-Milestone-Reporting (Gladia: "always report P50/P95/P99 per milestone instead of one blended number"), Politik-als-Konfiguration (Daily.co/pipecat).
- **Die Doku-Grenzen werden offen benannt** (Rev.ai kein Endpointing-Parameter; Azure-Timeout im rohen WS nicht dokumentiert setzbar) und mit der *fairsten verfügbaren* Alternative (A) beantwortet — das ist genau der Umgang mit Unsicherheit, den ein strenger Gutachter sehen will.

**Wo der Gutachter ansetzen könnte — und die Antwort darauf:**
- *"First-Partial ist nicht das nutzbare Ergebnis."* → Stimmt, deshalb zusätzlich Final-Latenz (B), klar als Politik-Mix etikettiert.
- *"Dein Bezugspunkt weicht von AA/Daily.co ab."* → Bewusst deklariert (ab Stream-Start statt ab VAD-Endpunkt), weil ein Dump kein natürliches Sprechende hat; im Geist identisch.
- *"Azure-Timeout hast du nicht angeglichen."* → Nicht verlässlich möglich im rohen WS (nur SDK-dokumentiert); deshalb über First-Partial umgangen und über die Kontroll-Messung/den CV von 0,9 % als festes Timeout belegt.

---

**Konkrete nächste Schritte (Code):**
1. `config.py:68` und `api_endpunkte.md:19`: `interim_results=false` → `true`.
2. In `_io_deepgram`, `_io_revai`, `_io_azure` (`stt.py:89–153`) jeweils `t_first_partial` loggen (Deepgram: erstes `Results` mit `is_final:false`; Rev.ai: erste `partial`-Message; Azure: erste `speech.hypothesis`-Message) und als `ttfp_ms` in den Record schreiben.
3. `messprotokoll.md:298–299` von "so etikettieren" auf "First-Partial als endpointing-freie Primärmetrik, Final-Latenz sekundär als Politik-Mix" anheben.
4. STT-Kampagne neu fahren (alte Deepgram-Daten unbrauchbar wegen `interim_results=false`).
5. Optional: kleine Azure-Timeout-Variationsserie (Variante C) als empirischer Beleg.

**Relevante Dateien:** `/Users/praktika/Documents/anton/bachelorThesis/measurements/layer3/stt.py` · `/Users/praktika/Documents/anton/bachelorThesis/measurements/layer3/config.py` (Z. 67–73) · `/Users/praktika/Documents/anton/bachelorThesis/setup/api_endpunkte.md` (Z. 19) · `/Users/praktika/Documents/anton/bachelorThesis/setup/messprotokoll.md` (Z. 290–302).

---

## Status 2026-06-16 — implementiert, adversarisch geprüft, korrigiert

Schritte 1–3 erledigt; danach **ultracode-Gegenprüfung** (23 Befunde, alle bestätigt) → zwei kritische
Korrekturen eingearbeitet. Maßgeblich ist die **korrigierte** Fassung unten (sie ersetzt die erste
„Azure ist der schnellste STT"-Lesart, die **falsch** war).

**Korrektur 1 — Realtime-Pacing statt Dump.** Beim Audio-Dump sendet Deepgram vor dem Final **kein** Interim
→ Deepgrams `ttfp` wäre sein **Final** (anderer Meilenstein als Azures/Rev.ais Teilwort) → der Cross-Provider-
Vergleich wäre apples-to-oranges und **gegen Deepgram** verzerrt. **Fix:** Audio bei allen drei im
**1×-Realtime-Takt** senden, Senden/Empfangen parallel (`asyncio.gather`). Dann liefern **alle** ein echtes
erstes Interim (verifiziert: `ttfp_is_final=False` bei allen). Code: `stt.py` `_paced_send` + `CHUNK_SECONDS`.

**Korrektur 2 — C1 NICHT über ein Cross-Provider-`ttfp`-Ranking.** `ttfp` enthält ~1 RTT; auf der STT-Achse
sitzt Azure in-Region (~11 ms) vs. US (~138 ms) → ein nackter `ttfp`-Rang bevorzugt **Geografie**, nicht Engine.
„Azure ist der schnellste STT" als Engine-Aussage ist daher **unzulässig** (Eigentor: stützt eher „Geografie
schlägt Engine"). **Korrekte C1-Logik:** Die **Inversion *innerhalb* von Azure** (gleiche RTT: STT-`ttft`
langsam, TTS-`ttfa` schnell → Differenz **muss** Backend sein) bleibt der Kern-Beleg; `ttfp` ist das
**Diagnose-Werkzeug**, das Azures STT-Langsamkeit als Endpointing **zerlegt** (`ttft − ttfp`), **nicht** ein
Tempo-Ranking. → konsistent mit `CLAUDE.md` C1; Inversion bleibt, wird durch `ttfp` sauberer erklärt.

**Smoke-Test (paced, n=1/Provider, Mac — nur Illustration, nicht Vantage-Point):**

| Provider | RTT (FRA) | `ttfp` (erstes Interim) | `ttft` (final, paced) | erstes Wort (`ttfp_is_final`) |
|----------|-----------|-------------------------|-----------------------|-------------------------------|
| Azure (EU) | ~11 ms | ~1093 ms | ~5074 ms | „good" (False) |
| Deepgram (US) | ~138 ms | ~1045 ms | ~4812 ms | „Good" (False) |
| Rev.ai (US) | ~138 ms | ~1563 ms | ~5264 ms | „good" (False) |

> Endpointing-Wartezeit wird in der Auswertung als `ttft − audio_upload_ms` isoliert (alle Rohzeiten je Call
> gespeichert: `ttfp_ms`, `ttft_ms`, `audio_upload_ms`, `ttfp_is_final`, `ttfp_text`). Der `ttft`-Konstanz-
> Beleg (Pilot: CV 0,9 %) wird als „**stark konsistent mit festem Timer**" formuliert (nicht „Fingerabdruck"),
> verstärkt durch Deepgrams CV ~104 % bei identischem Input → Konstanz ist provider-spezifisch.

**Offen:** Schritt 4 (STT-Kampagne neu fahren, n=100, paced), Schritt 5 (optional Azure-Timeout-Variationsserie C).

# Modul 16 — Limitationen & ehrliche Gesamtstory

**Ziel:** Souverän sagen können, was die Arbeit **nicht** kann — die Schwächen offen benennen, ohne die Kernaussage (C1 „Backend statt Geografie") zu kippen. Vor einem Skeptiker wie Prof. Wählisch ist das das wichtigste Modul: Wer seine Grenzen kennt, wirkt glaubwürdiger als wer sie wegredet.

> **Alle Zahlen sind final (Vollkampagne, abgeschlossen (56/56), A4 = Median der Slot-Mediane, success-only).** Bootstrap-CI noch ausstehend.

## 16.1 Die zentrale Unterscheidung (das ganze Modul hängt daran)

Es gibt zwei grundverschiedene Arten, mit einer Grenze umzugehen. Hier entscheidet sich, ob man souverän oder überheblich klingt.

| Begriff | Was es ist | Wirkung auf C1 | Beispiel |
|---------|-----------|----------------|----------|
| **Eingeräumte Limitation** | ehrliche Einschränkung der **Reichweite** einer Aussage | **kippt C1 nicht** — stärkt sogar das Vertrauen | „Die RTT-/Edge-Zahlen sind FRA-spezifisch." |
| **Overclaim** (eine zu weit getriebene Generalisierung) | Behauptung, die **über die Daten hinausgeht** | wäre angreifbar, würde C1 gefährden | „Engines sind **immer** schneller", „Rechenleistung allein erklärt alles" |

- **Eingeräumte Limitation** = schränkt die *Reichweite* ein, ohne die Kernaussage zu kippen.
- **Verteidigbare Generalisierung** heißt: **nicht** in den Overclaim rutschen. Man bleibt bei der **negativen, datengestützten** Aussage: **„Netznähe erklärt die Latenzspreizung nicht."** Das ist wasserdicht, weil es exakt das ist, was die Daten zeigen — ohne eine darüber hinausgehende Ursache zu behaupten.

**Merksatz fürs Gespräch:** Eine Limitation zugeben ist Stärke; eine Generalisierung übertreiben ist Schwäche. Souveränität = das Erste offen tun, das Zweite konsequent vermeiden.

## 16.2 Kurz-Erinnerung: Was ist die Kernaussage (C1)?

**C1 — „Backend statt Geografie":** Aus EU-Sicht dominiert die **Backend-Verarbeitung** (Hardware + Modell), nicht die Netznähe. `Backend` = Bündel aus Modellgröße/-Architektur + Inferenz-HW (z. B. Groq-LPU) + Serving-Stack.

> **Wasserdichte Form = die NEGATIVE Aussage:** *„Netznähe erklärt die Spreizung nicht."* Alles, was darüber hinausgeht („Engine-Rechenleistung allein"), trägt den Modellgrößen-Confound (s. 16.4) und wäre ein Overclaim.

## 16.3 Single Vantage Point (nur Frankfurt) — warum C1 trotzdem robust ist

**Vantage Point** = der Beobachtungsstandort, von dem aus gemessen wird. Hier: **eine** AWS-EC2 in `eu-central-1` (Frankfurt). Alle Messungen kommen von genau diesem Ort.

**Die Limitation (ehrlich):** Die konkreten **RTT-** (Round-Trip-Time = Hin-und-Rück-Laufzeit eines Pakets) und **Edge-Zahlen** (Edge = CDN-Randknoten, an dem die Verbindung endet) sind **FRA-spezifisch**. Ein anderer EU-Standort (Madrid, Warschau) sähe andere Edge-Distanzen.

**Warum das C1 NICHT tötet — der entscheidende Punkt:** C1 ruht **nicht** auf einem Distanz-Vergleich, sondern auf einer Messung bei **konstanter Netzdistanz**:

- OpenAI, Groq und Mistral terminieren **alle** beim selben Cloudflare-Edge in FRA — **~1 ms RTT**, alle in `AS13335` (autonomes System = Netzbereich unter einer Verwaltung, hier Cloudflare). Für **100 %** des LLM-Traffics gemessen + ASN-belegt.
- Bei dieser **identischen** Netzdistanz streut die `ttft` (Time-to-First-Token = vom Absenden bis zum ersten Antwort-Token) trotzdem um **~7,3× (gepoolt 8,3×)**: ~67 ms (Groq) → ~279 ms (Mistral) → ~487 ms (OpenAI). *(56 von 56 Slots, A4.)*

**Das Robustheits-Argument:** Die Spreizung ist bei **konstanter** Netzdistanz gemessen und damit distanz-unabhängig. Sie ist zudem **per-IP invariant** (der Edge-Shuffle zwischen den beiden CF-Adressen hat **0 Effekt** auf Reihenfolge und Abstand) — also erklärt die Netznähe sie nicht. Da die ~7,3×-Spreizung eine Backend-Eigenschaft bei ~1-ms-Edge ist, gilt sie **aus jeder EU-Perspektive**. Geografie ist hier sogar **invertiert**: EU-Mistral ist langsamer als US-Groq.

→ **Single Vantage Point = eingeräumte Limitation** (schränkt nur die Reichweite der reinen Distanz-Zahlen ein), C1 davon **nicht** betroffen.

## 16.4 Confounds — vermengte Ursachen (HW + Modell)

**Confound** (Störgröße) = ein Faktor, der so mit dem interessierenden Faktor verkoppelt ist, dass man ihre Wirkungen nicht sauber trennen kann.

- **Modellgröße und Hardware sind gekoppelt:** Groq hat das **kleinste Modell** **und** läuft auf einer **LPU** (Language Processing Unit, ein für Sprachmodelle spezialisierter Recheneinheit-Typ). Man kann nicht sagen, *welcher* der beiden Faktoren den Vorsprung bringt.
- **Der Software-Stack ist nicht isoliert** — in den Serving-Code der Anbieter sieht man nicht hinein.

**Konsequenz = Sprach-Disziplin:** Immer **„Backend (Hardware + Modell)"** sagen, **nie** „Rechenleistung allein". Letzteres wäre ein Overclaim. Die verteidigbare Form bleibt die negative Aussage: jedenfalls **nicht** die Netznähe.

## 16.5 STT ist KEIN Engine-Beleg (ehrlich)

`STT` (Speech-to-Text = Sprache→Text) ist eine der drei Kategorien. Sie trägt C1 bewusst **nicht**:

1. **Keine Spreizung auf der fairen Metrik:** Auf `ttfp` (Time-to-First-**Partial** = bis zum ersten live erkannten Wort) ist Azure **nicht** der langsamste, sondern **gleichauf mit Deepgram**. Kleine `ttfp`-Unterschiede dürfen nicht überinterpretiert werden.
2. **Keine gemeinsame kontrollierte Edge:** Bei STT gibt es keine konstante Netzdistanz wie das ~1-ms-Cloudflare-Edge bei den LLMs — also keine saubere Trennung Engine vs. Geografie.

> **Wichtig:** Die frühere These „Azure verliert STT wegen Endpointing" war ein **Dump-Artefakt (Bulk-Compute)** — sie wird **gestrichen** und **nicht** als Backend-Beleg geführt. Die within-Azure-STT/TTS-Gegenüberstellung bleibt höchstens **Workload-Beobachtung**, nicht „reine Engine-Geschwindigkeit".

## 16.6 Out of Scope: Qualität

**Out of scope** = bewusst nicht Teil der Untersuchung.

- **Gemessen wird NUR:** Latenz (Geschwindigkeit) + Verfügbarkeit (wie oft eine Anfrage erfolgreich beantwortet wird).
- **NICHT gemessen:** Transkript-Qualität (erkennt die STT die Wörter korrekt?) und Audio-/Sprachausgabe-Qualität (klingt die TTS gut?).

→ Auf „Welcher Anbieter ist der beste?" lautet die ehrliche Antwort: am schnellsten/verfügbarsten — gemessen; am besten in der Qualität — **nicht** gemessen.

## 16.7 Diurnal = Snapshot (unbestätigt)

**Diurnal** = der Tagesgang, die Schwankung der Latenz über den Tagesverlauf (v. a. wegen wechselnder US-Backend-Last).

- Die Kampagne **soll** den Tagesgang über 7 Tage × 8 Slots abdecken.
- Mit **56 von 56** Slots ist der Tagesgang vollständig abgedeckt, bleibt aber ein **Snapshot** über die Kampagnen-Woche — Tag × Slot sind noch **nicht orthogonal** (nicht sauber gekreuzt), und die Bootstrap-CI steht noch aus. → **Noch keine belastbare Tageszeit-Inferenz.**

→ Reine Reichweiten-Limitation; sie schrumpft mit dem vollständigen 56-Slot-Datensatz (Vollkampagne, abgeschlossen (56/56)), bleibt aber bis zur Bootstrap-CI vorsichtig zu formulieren.

## 16.8 Mess-Floor / Stack-Overhead (eingeräumte Baseline-Grenze)

Die feinste, aber für einen technischen Prüfer wichtigste Grenze: Die **App-Timer** (Stoppuhren im Mess-Programm) haben einen **Boden**, der **nicht „Netz"** ist — ein Teil der gemessenen Zeit stammt aus dem Messen selbst und dem Software-Stack.

| Quelle des Floors | Was sie kostet | Warum sie NICHT „Netz" ist |
|-------------------|----------------|----------------------------|
| `tls_handshake` (TLS 1.3 = Transport-Verschlüsselung v1.3) | ~3,5–5 ms | **krypto-CPU-dominiert**, nicht „1 RTT" — das ist Rechenzeit, nicht Wegezeit |
| rev.ai mit **TLS 1.2** (ältere Version) | + 1 ganze RTT zusätzlich | älteres Handshake-Protokoll braucht eine Extra-Runde |
| SSE-Parsing | kleine Verzögerung | Zerlegen der Server-Sent-Events (vom Server gestreamte Ereignis-Häppchen) |
| Python-GIL (Global Interpreter Lock = Sperre, die nur 1 Thread gleichzeitig Bytecode ausführen lässt) | kleine Verzögerung | App-/Stack-Effekt, kein Netzpfad |

**Folge:** Bei **sehr kleinen** Werten (Edge ~1 ms) ist ein spürbarer Teil **Mess- und Stack-Floor**, nicht reine Netz- oder Backend-Zeit. Das räumen wir ein.

**Warum es C1 nicht untergräbt:** Die Backend-Unterschiede der LLMs (~67 vs. ~487 ms) sind **um Größenordnungen größer** als dieser Floor (wenige ms Krypto-CPU) — sie lassen sich nicht mit dem Stack-Boden wegerklären.

## 16.9 Die ehrliche Gesamtstory (Zusammenfassung)

| Limitation | Typ | Kippt C1? |
|------------|-----|-----------|
| Single Vantage Point (nur FRA) | eingeräumt | **nein** — Spreizung bei konstanter Distanz, Reihenfolge invariant |
| Confounds (HW + Modell gekoppelt) | eingeräumt | **nein** — deshalb negative Aussage statt „Rechenleistung allein" |
| STT kein Engine-Beleg | ehrlich gestrichen | **nein** — C1 ruht auf LLM-Edge + TTS, nicht auf STT |
| Qualität out of scope | Scope-Grenze | **nein** — C1 ist eine Latenz-Aussage |
| Diurnal = Snapshot | eingeräumt (vorläufig) | **nein** — schrumpft mit dem 56-Slot-Datensatz, vorsichtig bis zur Bootstrap-CI |
| Mess-Floor / Stack-Overhead | eingeräumt | **nein** — Effektgröße ≫ Floor |

→ Alle Grenzen offen einräumen. Keine kippt die Kernaussage, weil diese **bewusst negativ und datengestützt** formuliert ist: **„Netznähe erklärt die Latenzspreizung nicht."** Diese Form hält jedem Angriff stand, weil sie nicht mehr behauptet, als die Daten zeigen.

## Prüf-Fragen

1. Warum ist „Single Vantage Point" für C1 nicht tödlich?
2. Unterschied „eingeräumte Limitation" vs. „verteidigbare Generalisierung"?

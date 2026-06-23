# Modul 17 — Prüfer-Einwände & Ein-Satz-Antworten

**Ziel:** Die wahrscheinlichsten Wählisch-Fragen reflexartig in *einem* Satz beantworten — und danach bei Bedarf vertiefen. Karteikarten zum Auswendig-Üben, jede an die konkreten Projektdaten gebunden.

## 17.0 Wie dieses Modul funktioniert

Dieses Modul vermittelt **keinen neuen Stoff**, sondern trainiert **Reflexe**. Ein skeptischer Prüfer bohrt nicht überall gleich tief, sondern an den wenigen Stellen, die ihm verdächtig vorkommen oder die er anders erwartet hätte. Diese Stellen kennen wir, weil Prof. Wählisch sie beim ersten Durchgang selbst benannt hat (Kern-Kritik: „drei Anbieter mit ~1 ms, nicht erklärt"). Für jede solche Frage gibt es hier:

1. die **wahrscheinliche Prüfer-Frage**,
2. eine **knappe, schlagfertige Ein-Satz-Antwort** (auswendig), und
3. eine **Vertiefung** (Begriffe + Projektbezug), falls nachgehakt wird.

> **⚠️ Zahlen sind final** (**Vollkampagne, abgeschlossen (56/56)**, Aggregation **A4** = Median der Slot-Mediane, success-only). **Bootstrap-CI noch ausstehend** — im Gespräch ruhig dazusagen, das signalisiert Sauberkeit, nicht Schwäche.

## 17.1 Die Karteikarten (Frage → Ein-Satz-Antwort)

| # | Prüfer-Frage | Ein-Satz-Antwort |
|---|--------------|------------------|
| 1 | „Drei Anbieter mit ~1 ms?" | Das ist die **Edge-Klassifikation** (RTT ≤ 2 ms + CDN-ASN + Traceroute), **pro IP über 56 Slots belegt** → gemessene Infrastruktur, kein Messfehler; das **Backend** wird **separat** gemessen und ergibt die **~7,3×-Spreizung (gepoolt 8,3×)**. |
| 2 | „STT ist doch langsam?" | Gemessen wird auf der fairen Metrik **`ttfp`** (vor dem Endpointing), und **gepact** ist Azure ~**gleichauf mit Deepgram (~1045 ms)** → Azure ist **nicht** der langsamste. |
| 3 | „Warum 5.600 / wie aggregiert?" | **7 Tage × 8 Slots × 100 = 5.600** pro Endpunkt; Headline = **Median der Slot-Mediane** + **gepoolte Gegenprobe** + **Bootstrap-CI**. |
| 4 | „macOS vs. EC2?" | Es zählt **nur der EC2-Lauf** (OpenSSL 3.x); der macOS-Lauf ist **markiert und ausgeschlossen**. |
| 5 | „Connect-vs-`ttft`-Asymmetrie?" | STT misst ab dem **Audio-Chunk**, LLM/TTS ab dem **Request** — bewusst so, damit das **E2E den connect nicht doppelt zählt**. |
| 6 | „Nur Modellgröße?" | Ja, das ist **genau der Confound** → deshalb die **negative** Aussage; die **invertierte Geografie** (EU-Mistral langsamer als US-Groq) zeigt **unabhängig von der Modellgröße**, dass es **nicht** die Netznähe ist. |

## 17.2 Karte 1 — „Drei Anbieter mit ~1 ms?"

**Begriffe.**
- **RTT** (Round-Trip-Time): Zeit, die ein Paket zum Server und zurück braucht. ~1 ms = Server praktisch „nebenan".
- **Edge:** äußerer Rand des Anbieter-Netzes, an dem dein Verbindungsaufbau ankommt — **nicht** der Rechen-Server.
- **CDN** (Content-Delivery-Network): weltweites Netz aus Zwischenstationen, das Anfragen am nächstgelegenen Punkt annimmt.
- **ASN** (Autonomous System Number): eindeutige Nummer eines Netzbetreibers; hier `AS13335` = Cloudflare.

**Warum das kein Messfehler ist.** Die niedrige RTT ist eine **echte Eigenschaft des Netzes bis zum Edge**. OpenAI, Groq und Mistral terminieren **alle** bei **Cloudflare Frankfurt** (`AS13335`, ~1 ms). Das ist mit **drei unabhängigen Kriterien** klassifiziert (RTT ≤ 2 ms **und** CDN-ASN **und** Traceroute) aus der **einmaligen L1-Momentaufnahme vom 16.6.**; die **per-IP-ASN-/connect-RTT-Abdeckung** der LLMs ist zusätzlich **über die 56 L3-Slots** belegt (100 % des LLM-Traffics; RTT je Provider ~1 ms: groq 1,3 / mistral 1,1 / openai 1,2 ms).

**Der Trick: Trennung.** Die niedrige RTT (Netz bis zum Rand) ist **gut erklärt** und damit nicht mehr verdächtig. Die eigentliche **Verarbeitungs-Latenz** wird mit einer **anderen Metrik** (`ttft`) gemessen und liegt ganz woanders: LLM-`ttft` streut **~67 → 279 → 487 ms ≈ 7,3×** (groq < mistral < openai; final A4, 56 Slots) — gleiches Netz, also kann die Differenz nicht Netznähe sein.

## 17.3 Karte 2 — „STT ist doch langsam?"

**Begriffe.**
- **STT** (Speech-to-Text): Umwandlung gesprochener Sprache in Text — erster Schritt der Pipeline.
- **`ttfp`** (Time-to-first-Partial): Zeit bis zum **ersten live erkannten Wort**, gerechnet **ab dem ersten Audio-Chunk** (connect-exklusiv).
- **Partial:** vorläufiges Zwischenergebnis, das die Erkennung schon während des Sprechens ausgibt.
- **Endpointing:** Erkennen des Satzendes (Entscheidung „du bist fertig") — eine Warte-Heuristik, **nicht** reine Erkennungsgeschwindigkeit.
- **Pacing (1×-Realtime):** Audio wird mit einfacher Echtzeit-Geschwindigkeit eingespeist, sonst liefern manche Anbieter (z.B. Deepgram) gar keine Interims.

**Warum Azure nicht langsam ist.** Auf der fairen Metrik `ttfp` — also **vor** dem Endpointing und **gepact** — liegt Azure **~gleichauf mit Deepgram (~1045 ms)**, ist also **nicht** der langsamste.

**Ehrlichkeit.** STT wird **bewusst NICHT** als Backend-Beleg geführt: auf der fairen Metrik zeigt sich **kein** klarer Engine-Effekt. Die frühere These „Azure-STT-Endpointing-Inversion" war ein **Dump-Artefakt (Bulk-Compute)** und wurde **gestrichen**.

## 17.4 Karte 3 — „Warum 5.600 / wie aggregiert?"

**Die Rechnung.** **7 Tage × 8 UTC-Slots × n=100 = 5.600** Messungen pro Endpunkt (× 9 Endpunkte = 50.400 gesamt).

**Begriffe.**
- **Slot:** fester Messzeitpunkt; 8 über den Tag verteilt (`00/03/06/09/12/15/18/21h`), damit Tageszeit-Effekte nicht alles verzerren.
- **Endpunkt:** konkreter Anbieter-Dienst (z.B. LLM-OpenAI).
- **Median:** mittlerer Wert einer sortierten Reihe (50 % darunter, 50 % darüber) — robuster gegen Ausreißer als der Mittelwert.
- **Median der Slot-Mediane:** erst je Slot den Median, dann über die Slots wieder den Median → ein unruhiger Slot dominiert nicht.
- **Gepoolte Gegenprobe:** zur Kontrolle alle Messungen in einen Topf werfen und prüfen, ob ähnliche Werte herauskommen.
- **Bootstrap-CI:** Konfidenzintervall (Sicherheits-Spanne), gewonnen durch wiederholtes zufälliges Ziehen aus den eigenen Daten.

**Headline-Regel.** Die Schlagzeilen-Zahl ist der **Median der Slot-Mediane** + **gepoolte Gegenprobe** + **Bootstrap-95%-CI** (Aggregation A4, `setup/messprotokoll.md` §Aggregation).

## 17.5 Karte 4 — „macOS vs. EC2?"

**Worum es geht.** Von welchem Standort wurde gemessen? **macOS** = lokaler Dev-Rechner; **EC2** = gemieteter AWS-Server in Frankfurt (`eu-central-1`), der **maßgebliche** Vantage Point.

**Die Antwort.** Es zählt **nur der EC2-Lauf** (OpenSSL 3.x). Im Datenbestand liegt zusätzlich ein **macOS-Dev-Lauf** mit deutlich höheren RTTs (~17–21 ms), weil er von einem anderen Ort / Netz lief — der ist **markiert und ausgeschlossen** (sonst Äpfel-mit-Birnen). Maßgeblich ist die **einmalige L1-Momentaufnahme vom 16.6. vom EC2** (RTT ~1 ms CF / ~11 ms Azure / ~140 ms US).

> **Begriff OpenSSL:** Software-Bibliothek, die den verschlüsselten Verbindungsaufbau (TLS) abwickelt; auf dem Server in neuerer Version (3.x). Der Punkt fürs Gespräch: Du **kennst** die Doppelung und schließt sie **aktiv** aus.

## 17.6 Karte 5 — „Connect-vs-`ttft`-Asymmetrie?"

**Begriffe.**
- **Connect:** Verbindungsaufbau (TCP + TLS, ggf. WebSocket-Upgrade), **bevor** eine Anfrage gestellt wird.
- **`ttft`** (Time-to-first-Token) beim LLM bzw. **`ttfa`** (Time-to-first-Audio) bei TTS: Zeit bis zum ersten Antwortstück, gerechnet **ab Request-Absenden** (connect-inklusiv).
- **Token:** kleine Texteinheit (ungefähr ein Wortteil).

**Warum die Asymmetrie Absicht ist.**
- **STT** misst `ttfp` **ab dem Audio-Chunk** (connect-**exklusiv**) — uns interessiert die reine Erkennungsgeschwindigkeit.
- **LLM/TTS** messen **ab dem Request** über eine **frische** Verbindung (connect-**inklusiv**).

**E2E zählt connect genau einmal.** In der Gesamtkette trägt **STT** den connect **+** seine Erkennungszeit, **LLM/TTS** tragen **nur** ihre jeweilige Antwortzeit → der Verbindungsaufbau wird **nicht doppelt** gezählt.

> **Caveat (Audit M1):** Für die *sequenzielle* E2E-Formel braucht es `connect_total + stt_ttft` (LLM startet erst auf dem finalen Transkript); die `ttfp`-Summe gilt nur als „STT-Standalone-Responsiveness".

## 17.7 Karte 6 — „Nur Modellgröße?"

**Begriffe.**
- **Modellgröße:** Anzahl der Parameter eines LLM — grob, wie groß/rechenintensiv es ist.
- **Confound (Störgröße):** ein Faktor, der zwei Erklärungen vermischt, sodass man die Ursache nicht sauber zuordnen kann. Hier: Groq = **kleinstes** Modell **und** spezielle HW (LPU).

**Warum der Einwand uns nicht trifft.** Wir **streiten ihn nicht ab**, sondern bauen ihn ein. Wir behaupten **nicht** „Engine-Rechenleistung allein", denn das könnte an der Modellgröße hängen. Wir behaupten die **negative, unangreifbare** Aussage:

> **Netznähe erklärt die Spreizung nicht.**

Das beweist die **invertierte Geografie** **unabhängig** von der Modellgröße: Wäre Netznähe die Ursache, müsste das **in Frankreich** gehostete **Mistral** näher und schneller sein als das **in den USA** laufende **Groq**. Tatsächlich ist **EU-Mistral langsamer als US-Groq** → die geografische Ordnung ist **invertiert**, Netznähe scheidet als Erklärung aus, egal wie groß die Modelle sind.

> **Formulierungs-Disziplin:** Immer **„Backend (HW+Modell) statt Geografie"**, nie „Engine-Rechenleistung allein".

## Prüf-Fragen

1. „Drei Anbieter mit rund einer Millisekunde?" — deine Ein-Satz-Antwort.
2. „STT ist doch langsam?" — deine Ein-Satz-Antwort.
3. „Warum 5.600 Messungen / wie aggregiert?" — deine Ein-Satz-Antwort.
4. „macOS vs. EC2?" — deine Ein-Satz-Antwort.
5. „Connect-vs-ttft-Asymmetrie?" — deine Ein-Satz-Antwort.
6. „Nur Modellgröße?" — deine Ein-Satz-Antwort.

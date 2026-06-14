# Figur 5 — Paket-Timeline + Inter-Arrival-Time (PCAP, Layer 2)

![](02_packet_timeline_azure_stt.png)

![](02_packet_timeline_deepgram_stt.png)

## Worum es geht

Diese Figur seziert einen einzelnen Verbindungsaufbau paketgenau aus dem PCAP-Mitschnitt und belegt damit, dass `connect_ms` sauber gemessen ist. Sie zeigt, dass die auffällige ~358-ms-Lücke bei Azure eine **Client-Wartezeit** ist — der eigene Mess-Client schickt das Audio verzögert ab —, **kein Server-Processing**. Und sie zeigt, dass Deepgram (US-geroutet, hohe RTT) gar keine solche Lücke hat, weil dort die Vor-Audio-Zeit schlicht der RTT-dominierte 3-RTT-Handshake ist. Wichtig zur Einordnung: `app_data_start` (446 ms bei Azure) ist nicht `connect_ms` (~49 ms). Die App ist bereits bei ~49 ms sendebereit; dass sie das Audio erst bei ~446 ms losschickt, ist Client-Verhalten, nicht Connect-Zeit.

## Was auf der Figur zu sehen ist

Beide Bilder folgen demselben **dreiteiligen** Aufbau (drei vertikal getrennte Panels): **(A1)** ein Handshake-Zoom, **(A2)** die volle, *ungebrochene* lineare Zeitachse bis zum ersten Audio, **(B)** ein **Inter-Arrival-Stem** mit Log-Achse. Farbe kodiert immer die **Paketrichtung**, nicht den Provider: Blau (`#1f6fb2`) = Client→Server (Upload), Orange-Braun (`#c44e1b`) = Server→Client (Download). Gefüllte Kreise = Pakete mit Payload, hohle Kreise mit weißem Kern = reine ACKs ohne Nutzdaten. Je Panel zwei waagrechte y-Spuren: oben „Client→Server", unten „Server→Client".

**Panel (A1) — Handshake-Zoom (linear, TCP/TLS getrennt):**
- Zeigt nur die ersten ~55 ms (Azure) bzw. ~330 ms (Deepgram, RTT-dominiert), damit der Handshake groß und lesbar ist; jedes Paket ist ein Punkt auf seiner Richtungsspur, chronologisch ab SYN bei 0 ms.
- Dezente Hintergrundbänder benennen die drei Phasen **getrennt**: „TCP-Handshake (1 RTT)", „TLS-1.3-Handshake (1 RTT)", „WS-Upgrade / Session-Init".
- Gepunktete vertikale Linien markieren die Schlüsselpakete **SYN, SYN-ACK, ClientHello, ServerHello** (per Leader-Linie auseinandergezogen, weil SYN-ACK ~18,5 ms und ClientHello ~19,2 ms fast deckungsgleich liegen).
- Ein grauer Doppelpfeil zeigt die Inter-Arrival-Zeit SYN→SYN-ACK quantitativ: „Δ 18,5 ms = 1 RTT" (Azure) bzw. „148,4 ms = 1 RTT" (Deepgram) — die direkte Antwort auf die Prof-Vorgabe „Inter-Arrival sichtbar".

**Panel (A2) — volle, ungebrochene Zeitachse (das Kernbild):**
- Dieselbe lineare Achse „Zeit seit SYN [ms]", aber bis zum ersten Audio-Paket (~470 ms Azure / ~510 ms Deepgram) — **ohne Bruch**, sodass die Abstände maßstabsgetreu bleiben.
- Eine **grün gestrichelte** Linie markiert `connect_ms` (App sendebereit, ~49 ms Azure / ~425 ms Deepgram), eine **blau gestrichelte** Linie `app_data_start` (~446 ms / ~478 ms) — bewusst getrennt.
- Bei **Azure** klafft zwischen beiden Linien ein **buchstäblich leerer Raum ohne ein einziges Paket** — die ~358-ms-Client-Sendelücke, beschriftet „~358 ms CLIENT wartet — kein Server-Processing". Dass dort keine Pakete liegen, ist der Beweis: der Server tut nichts, der Client sendet nur verzögert.
- Bei **Deepgram** fehlt diese Lücke; (A2) ist als „lückenloser, RTT-dominierter Aufbau" beschriftet — `connect_ms` und `app_data_start` liegen dicht beieinander, jede Pause davor ist genau eine RTT.

**Block (B) — Inter-Arrival-Stem (Log-Achse):**
- x-Achse: „Paket-Index (chronologisch, ab SYN)" — jedes Paket ein Punkt in Reihenfolge.
- y-Achse: „Inter-Arrival Δt zum Vorpaket [ms, log]" — der zeitliche Abstand jedes Pakets zum vorigen, **logarithmisch**, damit Sub-ms-Burst-Pakete und Hunderte-ms-Lücken im selben Bild lesbar sind.
- Graue Stiele tragen die Punkte; Punktfarbe wieder = Richtung. Eine grün gestrichelte Referenzlinie zeigt „1 RTT ≈ 18 ms" (Azure) bzw. „≈ 148 ms" (Deepgram).
- Die langen Lücken werden zu **umkreisten Ausreißern** mit Leader-Linie: Bei Azure zwei Kreise — rot „Client-Sendelücke (sendebereit ~49 ms, Audio erst ~446 ms)" und braun „Server-Processing (Warten aufs Transkript)". Bei Deepgram **nur ein** brauner Kreis „Server-Processing" — explizit beschriftet „nur Server-Processing als Ausreißer — KEINE Client-Sendelücke".

## Die Messwerte (mit Zahlen)

Alle Setup-Zahlen stammen aus `data/layer2/analysis_summary.json` bzw. werden im Plot-Skript direkt aus dem PCAP nachgerechnet (`_milestones`); je Provider liegt genau ein Mitschnitt vor (n=1, aufgenommen 2026-06-08 16:27 aus AWS eu-central-1). Die Layer-3-`connect_ms`-Werte sind dagegen Mediane der Juni-Kampagne.

**Azure STT** (`capture_azure_stt_20260608_1627.pcap`, 199 Pakete):
- TCP-Handshake (SYN→SYN-ACK) = **18,46 ms** = 1 RTT.
- TLS: ClientHello 19,24 ms → ServerHello 31,96 ms ≈ **13 ms** = 1 RTT.
- Letztes Setup-Paket bei ~**86,81 ms**; erstes Audio-Paket (`app_data_start`) bei **445,99 ms** → Client-Sendelücke ≈ **358 ms**.
- Layer-3-`connect_ms` (Juni-Median) ≈ **49–50 ms** — also ein sauberer ~3-RTT-Handshake (TCP + TLS + WS-Upgrade, je 1 RTT). `app_data_start` (446 ms) ≠ `connect_ms` (49 ms).
- Server-Processing (Warten aufs Transkript nach dem Audio-Upload) ≈ **776 ms** — erscheint als der zweite, separate Ausreißer im Stem.

**Deepgram STT** (`capture_deepgram_stt_20260608_1627.pcap`, 199 Pakete):
- TCP-Handshake = **148,44 ms** = 1 RTT.
- TLS: ClientHello 149,41 ms → ServerHello 299,62 ms ≈ **150 ms** = 1 RTT.
- `app_data_start` bei **478,17 ms**; die größte Vor-Audio-Lücke (ClientHello→ServerHello) ist exakt **1 RTT (≈150 ms)** — also der TLS-Handshake selbst, **keine** Client-Wartezeit.
- Layer-3-`connect_ms` (Juni-Median) ≈ **425 ms** (≈3 RTTs × ~140 ms + Overhead).
- Server-Processing ≈ **2991 ms** (Streaming-STT liefert das Final-Transkript spät; Deepgram-Schleifen-Tail).

## Was man daraus ableitet (der Befund)

Der nicht-triviale Befund: **`connect_ms` misst, was es behaupten soll** — die Zeit bis „App kann senden", und nichts anderes. Azures `connect_ms` von ~49 ms ist ein echter, sauberer 3-RTT-Handshake; die spätere ~358-ms-Lücke ist **Client-Wartezeit** (der Mess-Client schickt das Audio verzögert los) und gehört **nicht** ins Connect. Hätte man die Lücke fälschlich Azure-Servern zugeschrieben (die alte Mai-Fehlinterpretation „~224 ms Server-Anteil"), wäre die ganze Latenzzerlegung verfälscht. Die paketgenaue Sicht falsifiziert diese Fehldeutung.

Der Deepgram-Kontrast schärft das Argument: Bei Deepgram **gibt es** keine Client-Lücke, die größte Vor-Audio-Pause **ist** ein RTT. Das trennt sauber die zwei Latenzquellen — Netzwerk/Geografie (RTT, sichtbar bei Deepgram) vs. nicht-netzwerkbedingte Wartezeiten (Client-Artefakt bei Azure, Server-Processing bei beiden). Genau diese Trennung stützt die Forschungsfrage „Netzwerk vs. Backend-Verarbeitung": Erst wenn Connect, RTT, Client-Wartezeit und Server-Processing paketweise auseinandergehalten sind, lässt sich die Anteilsfrage seriös stellen. Die Figur liefert dabei den methodischen Beleg für die Zerlegung; die inhaltliche Anteilsaussage (Backend-Verarbeitung dominiert aus EU-Sicht) ruht auf den Kampagnen-Medianen und ist eine Anteils-, keine Kausalaussage.

## Rolle im Gespräch

Diese Figur ist der **Methodik-Beleg** im Set und beantwortet drei explizite Prof-Vorgaben sichtbar: (1) TCP- und TLS-Handshake **getrennt** dargestellt, (2) **Inter-Arrival-Time** sowohl visuell als auch quantitativ (Stem + Δ-Pfeile), (3) Betrachtung **ab SYN-ACK / paketweise** (zwei Richtungsspuren, jedes Paket ein Punkt). Sie kommt im Argument unmittelbar nach der Connect-Submetrik-Tabelle: Wo dort die Zahlen behauptet werden, liefert hier das PCAP den paketgenauen Nachweis, dass die Zerlegung stimmt — und entschärft präventiv den Verdacht, `connect_ms` enthalte versteckt Server-Zeit.

## Grenzen / ehrliche Caveats

- **n=1 pro Provider.** Es ist genau ein Mitschnitt — eine **strukturelle Illustration**, keine Verteilung. Die Lückendauern (358 ms, 776 ms, ~2991 ms) sind Einzelwerte, nicht Mediane; die robusten Mediane liefert Layer 3 (Kampagnen-Figuren).
- Die **Client-Sendelücke ist ein Artefakt des Mess-Clients**, nicht von Azure. Sie sagt nichts über Azures Server-Geschwindigkeit aus — sie zeigt nur, dass der Mess-Code das Audio nicht sofort nach Connect abschickt. Sie ist bewusst als Client-Wartezeit benannt, weil sie Azures Backend sonst zu Unrecht belasten würde.
- Die Figur zeigt **nicht das Backend selbst**, nur die Netzwerkränder. „Server-Processing" ist hier die Zeit zwischen letztem hochgeladenen Audio und erstem Transkript-Paket — sie enthält ggf. Restübertragung und protokollbedingtes Warten, nicht nur reine Rechenzeit.
- Anycast/Vantage-Point-Caveat: Deepgrams RTT (148 ms im PCAP) schwankt leicht gegenüber dem Kampagnen-RTT (~138 ms), weil Anycast je nach Pfad anders routet.

## Wenn der Prof fragt

**„Woher wissen Sie, dass die 358 ms Client- und nicht Server-Zeit sind?"**
Weil in dem Intervall **keine Pakete fließen** — weder rein noch raus (siehe leeres Panel A2 und der lückenlose Stem davor). Der TLS-Handshake ist bei ~32 ms abgeschlossen, die App ist bei `connect_ms` ~49 ms sendebereit; das erste Audio-Paket geht aber erst bei ~446 ms raus. Ein Server, der rechnet, würde nichts senden — aber hier sendet auch der Client nicht, obwohl er könnte: Es ist der Client, der mit dem Senden wartet. Das echte Server-Processing (Warten aufs Transkript) ist der **zweite**, separate braune Ausreißer im Stem, der erst nach dem Audio-Upload auftritt.

**„Wieso hat Deepgram keine solche Lücke?"**
Weil Deepgram über die USA/Anycast geroutet wird und damit eine ~140-ms-RTT hat. Dadurch füllt der reine 3-RTT-Handshake (TCP 148 ms + TLS 150 ms + WS-Upgrade) die Vor-Audio-Zeit von selbst — die größte Pause **ist** ein RTT (der TLS-Handshake), keine Client-Wartezeit. Bei Azure ist die RTT mit ~10–18 ms so klein, dass der Handshake fast nichts kostet und die Client-Wartezeit als isolierter Block sichtbar wird. Genau dieser Kontrast trennt Netzwerk- von Nicht-Netzwerk-Latenz.

**„Ein einzelner Mitschnitt — ist das belastbar?"**
Als Verteilungsaussage nein, und so wird er auch nicht verkauft. Die Figur belegt **strukturell**, dass die `connect_ms`-Zerlegung paketmechanisch stimmt; die Größenordnungen decken sich mit den Layer-3-Medianen der Kampagne (Azure-Connect ~49 ms, Deepgram ~425 ms). Die quantitativen Latenzaussagen der Arbeit stehen auf den Kampagnen-Medianen, nicht auf diesem einen PCAP.

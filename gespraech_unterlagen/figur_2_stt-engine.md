# Figur 2 — Engine schlägt Geografie (STT)

![](03_stt_cdf.png)

![](03_stt_connect_anteil.png)

## Worum es geht

Die beiden Teilbilder zeigen den Kernbefund der Arbeit am Beispiel der Spracherkennung (STT): Der geografisch entfernte US-Provider Deepgram liefert das erste Transkript rund dreimal schneller als der EU-nahe Provider Azure. Die Zerlegung in Netzwerk- gegen Verarbeitungsanteil belegt, dass dieser Unterschied nicht aus der Geografie kommt, sondern aus der Backend-Verarbeitung. Das ist eine Anteils-, keine Kausalaussage: Region und Engine eines Providers sind im Paket konfundiert (n=1 EU-Provider je Kategorie), die Figur falsifiziert lediglich die Annahme, die Region erkläre die Latenz hinreichend.

## Was auf der Figur zu sehen ist

**Teilbild A — CDF (`03_stt_cdf.png`):**
- **x-Achse:** `ttft_ms` (Time to First Token) in Millisekunden, lineare Skala von 0 bis 3500 ms. `ttft_ms` ist hier connect-EXKLUSIV: gemessen ab dem ersten gesendeten Audio-Chunk bis zum ersten finalen Transkript, also NACH dem Verbindungsaufbau (im Messcode `t_first_final - t_first_chunk`). Der vollständige STT-Cold-Start ist deshalb `connect_ms + ttft_ms` (siehe Teilbild B).
- **y-Achse:** kumulativer Anteil der Läufe von 0,0 bis 1,0 (empirische Verteilungsfunktion). Ein Punkt (x, y) bedeutet: ein Anteil y aller Läufe hatte ein TTFT ≤ x.
- **Drei Kurven (S-Kurven):** grün = Azure (n=5.600), blau = Deepgram (n=5.598), orange = Rev.ai (n=5.029). Je weiter links eine Kurve liegt, desto schneller der Provider. Im zentralen Bereich (Median) liegen die drei Kurven klar getrennt — sie bilden drei „Latenzklassen". An den Rändern (Tails) überlappen die Wertebereiche sehr wohl (siehe Caveats).
- **Horizontale Referenzlinien:** gepunktet bei y=0,50 (p50/Median), gestrichelt bei y=0,95 (p95), strichpunktiert bei y=0,99 (p99), am rechten Rand beschriftet. Wo eine Kurve die p50-Linie schneidet, liegt ihr Median.
- **Form-Detail:** Die Deepgram-Kurve (blau) hat bei y≈0,25 eine kleine Stufe/Schulter (Knick um ~500 ms), bevor sie steil ansteigt — ein Hinweis auf eine bimodale Komponente (Anycast-RTT-Schwankung). Azure (grün) und Rev.ai (orange) steigen steil und kompakt an (geringe Streuung).
- **Titel:** nennt die drei Mediane (Deepgram ~575 / Rev.ai ~1420 / Azure ~1715 ms).

**Teilbild B — gestapelte Balken (`03_stt_connect_anteil.png`):**
- **x-Achse:** die drei STT-Provider (azure, deepgram, revai), kategorial.
- **y-Achse:** Median Cold-Start-Latenz in ms, linear von 0 bis ~2000+.
- **Stapelbalken mit zwei Segmenten:** blau (unten) = `connect_ms` (Netzwerk: TCP+TLS+WS-Handshake), orange (oben) = `ttft_ms` (im Plot als „Server-Processing" beschriftet — diese Beschriftung ist eine Brutto-Größe, siehe Caveats). Der Gesamtbalken ist die STT-Cold-Start-Summe `connect_ms + ttft_ms`.
- **Annotationen:** über jedem Balken die Gesamthöhe (Azure 1765 ms, Deepgram 1000 ms, Rev.ai 2017 ms); im blauen Segment der Prozent-Anteil des Netzwerks am Cold-Start (Azure 3 %, Deepgram 43 %, Rev.ai 30 %).

## Die Messwerte (mit Zahlen)

Quelle: `analysis/tables/03_stt_statistics.csv` (Spalte p50 = Median), Juni-Kampagne.

| Provider | Region / RTT | connect_ms (p50) | ttft_ms (p50) | Cold-Start (Summe) | n | connect-Anteil |
|---|---|---|---|---|---|---|
| Deepgram | US, ~138 ms | 424,9 | 574,6 | ~1000 ms | 5.598 | ~43 % |
| Rev.ai | US, ~144 ms | 597,5 | 1419,6 | ~2017 ms | 5.029 | ~30 % |
| Azure | EU (Italy North), ~10 ms | 49,5 | 1715,2 | ~1765 ms | 5.600 | ~3 % |

- Der TTFT-Median (Teilbild A) liest sich direkt aus der Spalte `ttft_ms`: 574,6 / 1419,6 / 1715,2 ms.
- Der connect-Median ist `connect_ms`: 49,5 (Azure) / 424,9 (Deepgram) / 597,5 (Rev.ai).
- Azure hat den mit Abstand niedrigsten Connect (EU-Nähe, ~3 RTTs × ~10 ms + Overhead ≈ 49 ms), aber den höchsten TTFT.
- Deepgrams TTFT-Spalte hat ein std von 511,3 ms und ein max von 18.721,8 ms — das ist der lange Tail (Anycast-/Server-Schwankung), der den Median aber kaum berührt; deshalb arbeitet die Figur mit dem Median, nicht dem Mittelwert (586,3 ms).
- Über die Gesamtkampagne (alle Layer-3-Provider) wurden 50.400 Messungen erhoben, 0 % NaN; davon entfallen 16.227 auf die drei STT-Provider.

## Was man daraus ableitet (der Befund / der Fortschritt)

Die intuitive Erwartung lautet: Der EU-nahe Provider (Azure, RTT ~10 ms) müsste den US-Provider (Deepgram, RTT ~138 ms) schlagen. Das Gegenteil tritt ein — Deepgram liefert das erste Token in ~575 ms, Azure erst in ~1715 ms. Teilbild B zeigt, wo der Unterschied entsteht: Der Netzwerkanteil am Azure-Cold-Start beträgt nur ~3 %, der Rest (~97 %) entfällt auf die Verarbeitung nach dem Connect. Bei Deepgram ist der Netzwerkanteil ~43 %.

Zerlegt man die Differenz: Azure spart gegenüber Deepgram beim Netzwerk ca. −375 ms (49 statt 425 ms connect), verliert aber bei der Verarbeitung ca. +1140 ms (1715 statt 575 ms ttft) — netto +765 ms langsamer. Die geografische Nähe wirkt also wie erwartet (Azure connectet schneller), aber ihr Beitrag ist klein gegen die Verarbeitungsdifferenz.

Das ist der Fortschritt zur Forschungsfrage „Netzwerk vs. Backend": Die STT-Inversion **falsifiziert** die Hypothese, die Hosting-Region erkläre die Latenz hinreichend. Wäre die Region der dominierende Faktor, müsste der RTT-nähere Provider gewinnen; er verliert um ~765 ms netto, also reicht die Region als Erklärung nicht aus. Die Figur beweist damit NICHT, dass „die Engine alles erklärt" — Region und Backend sind je Provider untrennbar gekoppelt. Der Befund ist nicht trivial, weil er der naheliegenden „so nah wie möglich hosten"-Heuristik widerspricht und für die Provider-Wahl in einer EU-Pipeline praktisch relevant ist.

## Rolle im Gespräch

Diese Figur ist der **Kern-Beleg (C1)** der Arbeit. Sie steht früh im Argument, direkt nach der RTT-Klassen-Figur, die zeigt, dass Azure netzwerkseitig tatsächlich näher ist. Erst dadurch wird die Inversion überraschend: Es ist unabhängig belegt, dass Azure das schnellere Netz hat — und trotzdem bei STT verliert. Die TTS-Figur (Azure gewinnt dort bei TTFA mit ~67 ms, vor Deepgram 557 und OpenAI 954 ms) ist das Gegenstück desselben Providers und schließt die Inversion zum „Engine schlägt Geografie"-Argument: derselbe Provider verliert bei STT und gewinnt bei TTS, was eine rein geografische Erklärung ausschließt.

## Grenzen / ehrliche Caveats

- **Anteils-, keine Kausalaussage.** Pro Kategorie gibt es nur n=1 EU-Provider (Azure). Region und Backend sind konfundiert: Azures EU-Hosting und Azures STT-Backend kommen im Paket. Die Figur zeigt, dass die Region die Latenz NICHT hinreichend erklärt — sie beweist nicht, dass das Backend alles erklärt. Deshalb spreche ich von „Backend-Verarbeitung", nicht kausal von „der Engine".
- **„97 % Server-Processing" ist eine Brutto-Größe.** Das orange `ttft_ms`-Segment heißt im Plot „Server-Processing", enthält bei Azure aber auch eine CLIENT-Sendelücke: Die App ist nach connect bereits sendebereit (~49 ms), sendet das erste Audio aber erst bei ~446 ms (letztes Setup-Paket ~87 ms → erstes Audio ~446 ms, ~358 ms Lücke). Diese ~358 ms sind Client-Wartezeit (`app_data_start` ≈ 446 ms ≠ `connect_ms` ≈ 49 ms), kein Server-Rechnen. Aus dem PCAP geschätzt entfallen ~776 ms auf reines Server-Processing (Azure). Bei Deepgram gibt es KEINE solche Client-Lücke — die Pre-Audio-Zeit IST der 3-RTT-Handshake (TCP 148 + TLS 150 + WS, je 1 RTT); der lange Deepgram-Tail (~2991 ms im vollen `total_ms`) ist Server-/Close-bedingt. `ttft_ms` ist also der für den Nutzer spürbare Anteil nach connect, nicht 1:1 die Server-CPU-Zeit.
- **Metrik-Asymmetrie.** Der STT-Cold-Start ist `connect_ms + ttft_ms`, weil STT-ttft connect-EXKLUSIV gemessen ist. Bei LLM/TTS sind ttft/ttfa connect-INKLUSIV (der Verbindungsaufbau ist enthalten). Die Balken-Definition ist also kategorie-spezifisch und darf nicht naiv auf andere Kategorien übertragen werden; gerade deshalb zählt die E2E-Summe `stt_connect + stt_ttft + llm_ttft + tts_ttfa` den Connect-Anteil korrekt und nicht doppelt.
- **„Drei getrennte Klassen" heißt Slot-Median-Trennung.** Präzise: In allen 56 Slots liegt der Deepgram-Slot-Median unter dem Azure-Slot-Median. Die Roh-Wertebereiche (Tails, z. B. Deepgram-max 18.721,8 ms) überlappen sehr wohl. Die CDF-Kurven berühren sich an den Rändern — die Trennung gilt für die zentrale Masse, nicht für jeden Einzellauf.
- **`connect_ms` cross-Provider nur für direkte Provider vergleichbar.** Alle drei STT-Provider hier sind direkt erreichbar; bei Cloudflare-fronted Providern (4/9 der Gesamtmatrix) misst `connect_ms` den Edge, nicht das Backend. Der Vergleich in dieser Figur ist davon nicht betroffen.
- **Rev.ai-Detail.** Rev.ais höherer connect (~598 ms) enthält eine TLS-1.2-Penalty von ~153 ms (zusätzliche ~1 RTT gegenüber den TLS-1.3-Providern). Das erklärt einen Teil seines schlechten netzwerkseitigen Abschneidens, ändert aber nichts am Verarbeitungsbefund.

## Wenn der Prof fragt

**„Sie messen einen einzigen EU-Provider — wie können Sie da auf das Backend schließen?"**
Korrekt, das ist eine Anteils-, keine Kausalaussage. Der Anspruch ist bewusst schwächer und sauber: Die Inversion falsifiziert die Hypothese, die Region erkläre die Latenz hinreichend. Wäre die Region dominant, müsste der RTT-nähere Provider (Azure, ~10 ms) gewinnen — er verliert um ~765 ms netto. Region und Backend sind konfundiert; ich behaupte nicht, das Backend erkläre alles, sondern dass die Geografie nicht reicht. Das ist mit n=1 EU-Provider belegbar, weil eine Falsifikation nur ein Gegenbeispiel braucht. Der zweite Beleg ist die TTS-Inversion: derselbe Provider (Azure) gewinnt dort, was eine rein geografische Erklärung endgültig ausschließt.

**„Ist Azures 97 %-Balken wirklich Serverzeit?"**
Nein, nicht ganz — das ist die ehrliche Stelle. Der Balken ist `ttft_ms`, der spürbare Anteil nach connect. Aus dem PCAP weiß ich, dass davon ~358 ms eine Client-Sendelücke sind (App sendebereit bei ~49 ms, erstes Audio erst ~446 ms) und ~776 ms echtes Server-Processing. Das ändert die Richtung des Befunds nicht — Azures Verarbeitungsanteil bleibt dominant —, aber die „97 %" sind die Brutto-Größe nach connect inklusive Client-Wartezeit, nicht reine Server-CPU.

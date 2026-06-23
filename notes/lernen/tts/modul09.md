Modul neun. Speech-to-Text, die Partial-Metrik und das Echtzeit-Pacing.


Worum es geht.

Bei Speech-to-Text musst du erklären können, warum die naheliegende Metrik unfair ist, womit du sie ersetzt, warum dazu zwingend Echtzeit-Pacing gehört, und welche ehrlichen Grenzen die neue Metrik hat. Das ist zugleich die Geschichte, wie ein Mess-Artefakt fast zu einer falschen These geworden wäre.


Drei Begriffe vorab.

Ein Partial, auch Interim genannt, ist eine vorläufige Wort-Vermutung, die die Engine schon zurückschickt, während du noch sprichst. Wie ein Live-Untertitel, bevor der Satz fertig ist. Ein Final ist das endgültige Transkript, das die Engine schickt, wenn sie ein Segment für abgeschlossen hält. Und Endpointing, oder Finalisierung, ist die Entscheidung der Engine, wann ein Segment final ist, meist über Stille-Erkennung.


Das Problem. Die Final-Metrik ist unfair.

Die naheliegende Metrik wäre die Zeit bis zum ersten Final, kurz Time to First Final. Genau das ist unfair. Wann ein Anbieter final sagt, hängt von seiner Finalisierungs-Politik ab, nicht nur von der Engine-Geschwindigkeit, und die drei Anbieter finalisieren unterschiedlich. Die Final-Metrik mischt also zwei Dinge in einer einzigen Zahl: die Engine-Geschwindigkeit, die du messen willst, und die Endpointing-Politik, die du nicht messen willst. Als reiner Engine-Vergleich ist sie damit unbrauchbar.


Ein Lehrstück in Ehrlichkeit. Die Azure-Korrektur.

Im alten Lauf, dem sogenannten Dump, war die Final-Zeit von Azure auffällig konstant bei rund tausendsiebenhundertzweiundzwanzig Millisekunden. Die erste Deutung war: Azure hat ein festes Stille-Fenster von tausendsiebenhundert Millisekunden. Das war falsch. Was wirklich passierte: Im Dump wurde das ganze Audio auf einmal reingeworfen, das nennt man Bulk-Verarbeitung. Azure rechnete die komplette fast fünf Sekunden lange Äußerung in einem Rutsch durch. Die tausendsiebenhundert Millisekunden waren also reine Verarbeitungszeit für Bulk-Audio, kein Stille-Timer. Unter echtem Pacing finalisiert Azure schon rund achtundneunzig Millisekunden nach dem letzten Audio-Byte. Die hohe Konstanz belegte nur deterministisches Verhalten bei identischem Input, keinen großen Timer. Konsequenz: Die alte These, Azure verliere bei Speech-to-Text wegen Endpointing, ist gestrichen. Sie war ein Mess-Artefakt. Genau deshalb trägt Speech-to-Text die Kernaussage nicht. Dass du das selbst aufgedeckt und korrigiert hast, ist ein Vertrauens-Plus.


Die Lösung. Die Partial-Metrik.

Statt zu versuchen, die Finalisierung zwischen den Anbietern anzugleichen, was technisch nicht geht, weil kein Anbieter den nötigen Parameter über die rohe Verbindung anbietet, misst du davor. Die neue Metrik ist die Zeit bis zum ersten Partial, kurz Time to First Partial, also die Zeit bis zum ersten live erkannten Wort. Das erste Partial kommt vor jeder Finalisierung, ist also endpointing-frei. Damit ist diese Metrik symmetrisch zu den anderen Kategorien: erstes Token beim Sprachmodell, erstes Audio beim Text-to-Speech, erstes Wort bei Speech-to-Text. Überall die Zeit bis zum ersten Ausgabe-Element. Die Final-Metrik bleibt nur noch sekundär.


Warum Echtzeit-Pacing zwingend ist.

Pacing heißt: Du streamst das Audio im Eins-fach-Echtzeit-Takt, also so schnell, wie es wirklich gesprochen würde, etwa hundertachtundzwanzig Millisekunden pro Audio-Block, und Senden und Empfangen laufen parallel. Warum nicht einfach alles auf einmal schicken? Weil dann der Vergleich unfair wird. Im Dump-Modus liefert zum Beispiel Deepgram vor dem Final gar kein Partial. Du hättest für Deepgram also gar keine Partial-Zeit und müsstest Meilensteine vergleichen, die es bei einem Anbieter gar nicht gibt. Nur bei echtzeit-eintreffendem Audio liefern alle drei Anbieter echte Zwischenergebnisse. Das ist sogar verifiziert: Bei fünfundzwanzig von fünfundzwanzig Messungen pro Anbieter war das erste Wort tatsächlich ein echtes Zwischenergebnis und kein Final. Pacing ist also die Voraussetzung dafür, dass die Partial-Zeit über alle drei überhaupt fair vergleichbar ist.


Das Ergebnis. Azure und Deepgram gleichauf.

Azure aus Europa hat eine Round-Trip-Zeit von rund elf Millisekunden und eine Partial-Zeit von rund tausendfünfundvierzig Millisekunden. Deepgram aus den USA hat eine Round-Trip-Zeit von rund hundertzweiundvierzig Millisekunden und eine Partial-Zeit von rund tausendsechsundvierzig Millisekunden. Beide sind also praktisch gleichauf. Rev.ai liegt mit rund tausendvierhundertvierundneunzig Millisekunden höher. Azure ist damit nicht der langsamste. Das ist der Befund, der die alte Azure-verliert-These endgültig kippt.


Drei ehrliche Grenzen der Partial-Metrik.

Erstens, der dominante Pacing-Boden. Unter Echtzeit-Pacing trifft das erste Wort, Good, bei allen Anbietern zur etwa gleichen Zeit im Stream ein, nach rund acht Zehntelsekunden. Die Partial-Zeit ist also ungefähr: gemeinsamer Pacing-Boden von rund acht Zehntelsekunden, plus ein Netz-Roundtrip, plus die Engine-Reaktion. Der Boden dominiert den Absolutwert und kürzt sich in den Differenzen zwischen den Anbietern heraus. Die Partial-Zeit ist deshalb ein Indikator dafür, ob die Engine zügig reagiert, kein feines Ranking. Kleine Unterschiede darf man nicht überinterpretieren, nur große, wie die rund vierhundertfünfzig Millisekunden Vorsprung gegenüber Rev.ai, sind ein echtes Signal.

Zweitens, kaum geografie-empfindlich. Genau das erklärt, warum Azure mit elf Millisekunden und Deepgram mit hundertzweiundvierzig Millisekunden dieselbe Partial-Zeit haben: Der Pacing-Boden überdeckt den kleinen Roundtrip-Anteil.

Drittens, die Emissions-Kadenz, also wann das erste Zwischenergebnis kommt, ist Anbieter-Politik, nicht reine Engine-Zeit.


Der eingebaute Netz-Roundtrip. Wie man Netz von Backend trennt.

Eine typische Prüfer-Falle lautet: Ist die Partial-Zeit nicht auch netzabhängig? Die ehrliche Antwort: Ja, um genau einen Roundtrip. Die Partial-Zeit ist bauartbedingt Audio raus, Zwischenergebnis zurück, enthält also einen eingebauten Netz-Roundtrip plus die Engine-Reaktion. Sie ist keine reine Rechenzeit. Aber das ist kein Problem, weil der Netz-Anteil bekannt und herausrechenbar ist. Du kennst die Round-Trip-Zeit aus Layer eins separat, am Edge rund eine Millisekunde, in den USA rund hundertvierzig Millisekunden, und kannst sie abziehen. Deine Antwort auf die Falle: Ja, die Partial-Zeit enthält genau einen Roundtrip, und den kenne ich aus Layer eins, also kann ich ihn vom Engine-Anteil trennen. Genau dafür ist die Drei-Schichten-Architektur da.

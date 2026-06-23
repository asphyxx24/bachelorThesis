Modul acht. Layer drei und die Metrik-Asymmetrie.


Worum es geht.

Dieses Modul ist das Herzstück der ganzen Mess-Methodik, und es ist gleichzeitig der häufigste Prüf-Punkt. Hier geht es darum, wie genau in Layer drei die Latenz einer einzelnen Cold-Start-Anfrage zerlegt und gemessen wird. Vier Dinge musst du danach sattelfest erklären können. Erstens, wie der Verbindungsaufbau in atomare Submetriken zerfällt und was dabei der Wegwerf-Socket ist. Zweitens, die sogenannte Metrik-Asymmetrie, also warum bei Speech-to-Text die Uhr anders startet als beim Sprachmodell und beim Text-to-Speech. Drittens, warum man die End-to-End-Latenz nicht naiv aufsummieren darf, weil man sonst den Verbindungsaufbau doppelt zählt. Und viertens, dass es zwei verschiedene IP-Felder gibt, wofür jedes davon gut ist, und warum man bestimmte Fehler niemals über das eine Feld herausfiltern darf. Zum Schluss noch der Output-Mengen-Confound, also die Falle, dass ein wortkarges Modell scheinbar schnell wirkt, obwohl es nur wenig sagt.

Bevor wir loslegen, ein Hinweis zu den Zahlen. Alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.


Was Layer drei misst, und was Cold-Start bedeutet.

Layer drei misst die Latenz der echten Programmierschnittstellen, also der Application Programming Interfaces, kurz APIs, der neun Anbieter. Eine API ist die Schnittstelle, über die dein Programm den Dienst eines Anbieters aufruft. Layer drei ist die einzige Schicht, die über die volle Adresse misst, also bis zum eigentlichen Verarbeitungs-Backend des Anbieters, und nicht nur bis zum Host wie Layer eins. Damit misst Layer drei die Verarbeitung der Engine.

Der zweite Grundbegriff ist Cold-Start. Cold-Start heißt: Jede einzelne Messung baut eine komplett frische Verbindung auf, eine neue TCP-Verbindung und einen neuen TLS-Handshake, also eine neue verschlüsselte Sitzung. Es gibt kein Connection-Pooling und kein Keep-Alive, das heißt, keine Verbindung wird wiederverwendet. Der Grund ist, dass wir den realen Overhead einer neuen Gesprächssitzung messen wollen, so wie ihn ein Nutzer erlebt, der gerade eine Sprach-Interaktion startet. Würde man eine warme, schon bestehende Verbindung wiederverwenden, würde man genau den Verbindungsaufbau verstecken, der aus EU-Sicht der spannende Teil ist, weil er die Distanz zum oft amerikanischen Backend enthält.


Der Verbindungsaufbau in atomaren Submetriken.

Zuerst der Begriff Submetrik. Eine Submetrik ist ein Teilstück einer größeren Messgröße, also nicht der ganze Verbindungsaufbau als eine einzige Zahl, sondern jede Phase davon einzeln. Früher gab es einen einzigen Sammel-Timer, der hieß connect-Millisekunden und maß den gesamten Verbindungsaufbau als Black-Box, also als eine undurchsichtige Gesamtzahl. Diesen Sammel-Timer hat man bewusst abgeschafft. Der Grund: Eine einzige Zahl sagt dir nicht, ob die Zeit in der Namensauflösung, im TCP-Handshake oder im TLS-Handshake steckt, und genau diese Aufschlüsselung braucht man, um die Schichten miteinander zu verknüpfen.

Stattdessen wird der Aufbau in atomare Teile zerlegt und jeder Teil roh gespeichert. Das erste Teilstück ist die Namensauflösung, gemessen als DNS-Millisekunden. DNS steht für Domain Name System, das ist die Übersetzung eines Hostnamens in eine IP-Adresse. Sie wird getrennt gemessen, weil sie oft zwischengespeichert, also gecacht, ist und dann fast nichts kostet. Das zweite Teilstück ist der TCP-Handshake, gemessen als tcp-handshake-Millisekunden. Das ist die Zeit vom SYN-Paket bis zum SYN-ACK-Paket, also genau ein Netz-Roundtrip, eine Round-Trip-Zeit. Das dritte Teilstück ist der TLS-Handshake, gemessen als tls-handshake-Millisekunden, also vom ClientHello bis zum fertigen Handshake bei der Transport-Verschlüsselung in Version eins Punkt drei, ebenfalls etwa ein Roundtrip. Bei Speech-to-Text kommt der WebSocket-Upgrade als zusätzliche Phase hinzu, weil Speech-to-Text über WebSocket läuft, also über einen dauerhaft offenen Zwei-Wege-Kanal. Ein eigenes ws-upgrade-Feld gibt es im Code aber nicht. Der Upgrade steckt zusammen mit dem TCP-Handshake und dem TLS-Handshake in einer einzigen Zahl, dem ws-connect-Millisekunden auf der echten WebSocket-Verbindung. Der Wegwerf-Socket selbst misst nur die Namensauflösung, den TCP-Handshake und den TLS-Handshake. Ein connect-total gibt es nur noch als abgeleitete Summe dieser Teilstücke, also nur bei Bedarf zusammengerechnet, niemals als eigener Roh-Timer.

Der große Vorteil dieser Zerlegung: Dieselbe atomare Phase ist über alle neun Endpunkte hinweg vergleichbar. Du kannst zum Beispiel den tcp-handshake aller neun Anbieter direkt nebeneinanderlegen. Und dieser tcp-handshake ist genau dieselbe Größe wie der TCP-Ping aus Layer eins. Damit wird die Brücke zwischen den Schichten transparent, statt nur behauptet zu sein. Diese Brücke lautet: Der Verbindungsaufbau entspricht ungefähr der Anzahl der Roundtrips mal dem Ping.


Was der Wegwerf-Socket ist.

Jetzt der zentrale Begriff Wegwerf-Socket. Ein Socket ist der Endpunkt einer Netzwerkverbindung im Betriebssystem, also gewissermaßen die Steckdose, in die ein Programm seine Verbindung steckt. Ein Wegwerf-Socket ist nun eine eigene, zusätzliche Verbindung, die nur zu einem einzigen Zweck geöffnet wird, nämlich um den Verbindungsaufbau sauber in seine Teile zu zerlegen, und die danach sofort wieder geschlossen wird. Sie ist also getrennt von der eigentlichen Mess-Anfrage.

Warum macht man das so umständlich? Weil die eigentliche Mess-Bibliothek, in unserem Fall httpx beim Sprachmodell und beim Text-to-Speech, die einzelnen Phasen des Aufbaus nicht sauber einzeln herausgibt. Sie liefert dir den Inhalt der Antwort, aber nicht atomar DNS, TCP und TLS getrennt. Damit man die Submetriken trotzdem bekommt, öffnet man kurz vor der echten Anfrage diesen separaten Wegwerf-Socket, geht ihn Schritt für Schritt durch, stoppt jede Phase mit der Uhr, und wirft ihn dann weg. Im Code steht das in der Datei connect Punkt py. Dort macht eine Funktion namens connect-submetrics genau das: Sie löst zuerst den Hostnamen auf und stoppt die DNS-Zeit, dann baut sie mit socket-create-connection die TCP-Verbindung auf und stoppt den tcp-handshake, dann legt sie mit wrap-socket die TLS-Schicht darüber und stoppt den tls-handshake, und schließt den Socket sofort wieder.

Ganz wichtig zur Einordnung: Beim Sprachmodell und beim Text-to-Speech ist dieser Wegwerf-Socket nur eine Referenzmessung. Er dient dazu, dass man bei Bedarf den connect-Anteil aus der eigentlichen Messung herausrechnen kann. Die eigentliche, gemessene Latenz, also die Zeit bis zum ersten Token oder bis zum ersten Audio, läuft über die echte Anfrage und enthält den Verbindungsaufbau bereits. Bei Speech-to-Text dagegen läuft der echte Verbindungsaufbau über den WebSocket, und der Wegwerf-Socket ist auch dort nur Layer-eins-Referenz.


Die Metrik-Asymmetrie. Der wichtigste Punkt überhaupt.

Jetzt kommen wir zum Kern, und das ist genau die Stelle, die bisher am meisten verwirrt hat, weshalb sie explizit deklariert wird. Die entscheidende Frage lautet: Ab welchem Zeitpunkt läuft die Uhr für das erste Token oder das erste Audio? Und die Antwort ist eben nicht über alle drei Kategorien gleich. Das nennen wir die Metrik-Asymmetrie.

Bei Speech-to-Text startet die Uhr beim ersten Audio-Chunk, also bei dem ersten Stück Audio, das losgeschickt wird, und das passiert erst, nachdem die Verbindung schon steht. Die primäre Speech-to-Text-Metrik ist die Zeit bis zum ersten Partial, also bis zum ersten live erkannten Wort, gemessen ab dem ersten Audio-Chunk. Das bedeutet: Bei Speech-to-Text ist die Metrik connect-exklusiv. Connect-exklusiv heißt, der Verbindungsaufbau ist nicht enthalten, er wurde vorher abgezogen und steht separat in den Submetriken.

Beim Sprachmodell und beim Text-to-Speech ist es umgekehrt. Die Uhr startet beim Absenden des Requests über eine frische Verbindung. Beim Sprachmodell ist die Metrik die Zeit bis zum ersten Token, beim Text-to-Speech die Zeit bis zum ersten Audio. Beide werden ab dem Moment gemessen, in dem die Anfrage rausgeht. Das bedeutet: Diese beiden Metriken sind connect-inklusiv. Connect-inklusiv heißt, der gesamte Verbindungsaufbau steckt schon mit in der Zahl drin, weil die Uhr eben startet, bevor die Verbindung steht, nämlich beim Absenden über die frische Verbindung.

Im Code sieht man das direkt. In der Datei llm Punkt py wird die Variable t-req, also der Startzeitpunkt, gesetzt, und gleich danach geht im selben Block der client-stream-Aufruf raus, der die Verbindung aufbaut und den Request sendet. Die Uhr läuft also über den Verbindungsaufbau hinweg. Dasselbe Muster steht in tts Punkt py. Bei Speech-to-Text dagegen wird die Uhr erst beim ersten Audio-Chunk gestartet, also nach dem Connect.


Warum diese Asymmetrie. Die Kernantwort.

Das ist die Frage, die der Prüfer mit Sicherheit stellt, denn auf den ersten Blick wirkt es inkonsistent, mal mit und mal ohne Verbindungsaufbau zu messen. Die Antwort ist: Die Asymmetrie bildet die reale Nutzungssituation ab. Wir messen jeweils die vom Nutzer wahrgenommene Wartezeit, und die beginnt in den drei Fällen tatsächlich an unterschiedlichen Punkten.

Bei Speech-to-Text wird der Nutzer-Eindruck ab dem Moment gemessen, in dem das Audio zu fließen beginnt. Der gesamte vom Nutzer wahrgenommene Speech-to-Text-Cold-Start ist dann der connect-total plus die Zeit bis zum ersten Partial. Man trennt also den Verbindungsaufbau bewusst ab, misst die Engine-Reaktion separat und kann beides hinterher wieder zusammensetzen.

Beim Sprachmodell und beim Text-to-Speech dagegen beginnt die wahrgenommene Wartezeit schon mit dem Absenden des Requests. Der Nutzer drückt ab, und ab da läuft seine gefühlte Wartezeit, inklusive des Verbindungsaufbaus. Deshalb ist es hier richtig, connect-inklusiv zu messen. In beiden Fällen misst man also exakt das, was der Nutzer als Wartezeit erlebt, nur dass dieser Startpunkt eben kategorienspezifisch ist. Genau das ist der Grund für die Asymmetrie, und genau so erklärst du sie dem Prüfer.


End-to-End nicht naiv aufsummieren.

Zuerst der Begriff End-to-End, oft abgekürzt mit E zwei E. End-to-End meint die Gesamtlatenz der kompletten sequenziellen Sprach-Pipeline, also von ganz vorne bis ganz hinten: erst hört das System zu mit Speech-to-Text, dann denkt es nach mit dem Sprachmodell, dann antwortet es mit Text-to-Speech. Sequenziell heißt, die Stufen laufen nacheinander, denn das Sprachmodell kann erst auf dem fertigen Transkript starten.

Und jetzt die Falle. Man könnte ja auf die Idee kommen, einfach alle Verbindungsaufbau-Zeiten plus alle Erste-Ausgabe-Zeiten zusammenzuzählen. Genau das ist falsch. Denn beim Sprachmodell und beim Text-to-Speech steckt der Verbindungsaufbau bereits in der gemessenen Zeit drin, weil diese Metriken ja connect-inklusiv sind. Würde man jetzt zusätzlich noch den separat gemessenen Verbindungsaufbau dieser beiden draufaddieren, hätte man den connect bei Sprachmodell und Text-to-Speech doppelt gezählt. Die Zahl wäre künstlich zu groß.

Die korrekte Formel lautet: Speech-to-Text-connect plus Speech-to-Text-Erste-Ausgabe plus Sprachmodell-Erste-Ausgabe plus Text-to-Speech-Erste-Ausgabe. In Worten der Metriken: stt-connect plus stt-Zeit-bis-erstes-Token plus llm-Zeit-bis-erstes-Token plus tts-Zeit-bis-erstes-Audio. Der Trick dahinter ist einfach: Speech-to-Text trägt seinen Verbindungsaufbau plus seine Erste-Ausgabe-Zeit bei, weil seine Metrik ja connect-exklusiv ist und den Aufbau nicht enthält. Das Sprachmodell und das Text-to-Speech tragen dagegen nur ihre Erste-Ausgabe-Zeit bei, weil ihr Verbindungsaufbau in dieser Zahl schon drinsteckt. So zählt der connect für jede Stufe genau einmal, und nie doppelt.

Ein Detail noch, damit es ganz sauber ist. Für die sequenzielle Pipeline trägt Speech-to-Text nicht die Zeit bis zum ersten Partial bei, sondern die Zeit bis zum finalen Transkript, also die sekundäre Speech-to-Text-Metrik. Der Grund: Das Sprachmodell kann eben erst loslegen, wenn das Transkript final ist, nicht schon beim ersten vorläufigen Wort. Die Zeit bis zum ersten Partial ist nur die Standalone-Reaktionsschnelligkeit von Speech-to-Text, sie ist keine realisierbare Pipeline-Latenz.


Die zwei IP-Felder. Eine echte Falle.

Jeder Mess-Datensatz trägt zwei verschiedene IP-Felder, und sie kommen aus unterschiedlichen Quellen. Wer die beiden verwechselt, verfälscht die IP-, Region- und Brücken-Analysen. Deshalb gibt es dafür eine feste Regel.

Das erste Feld ist das top-level-Feld, es heißt einfach resolved-ip, ohne Vorsatz. Es ist der echte Peer der Mess-Anfrage, also die tatsächliche Gegenstelle, mit der die eigentliche Messung wirklich gesprochen hat. Es wird ausgelesen mit getpeername. Getpeername ist ein Betriebssystem-Aufruf auf einem offenen Socket, der zurückgibt, mit welcher IP-Adresse dieser Socket tatsächlich verbunden ist. Wichtig: Dieses top-level-Feld ist null bei Fehlschlägen, also bei einem Timeout oder einem Verbindungsabbruch, weil dann ja gar keine Verbindung zustande kam, von der man die Gegenstelle ablesen könnte. Dieses Feld dient ausschließlich der Schichten-übergreifenden Round-Trip-Zeit-Brücke, also der Verknüpfung der gemessenen Latenz mit der Round-Trip-Zeit aus Layer eins. Und dort gilt die strenge Regel: Verwende nur die Messungen, bei denen das top-level-resolved-ip gleich dem connect-resolved-ip ist. Nur dann hat nämlich die Referenzmessung denselben Server getroffen wie die eigentliche Messung, und nur dann ist der Vergleich sauber.

Das zweite Feld heißt connect-resolved-ip, also das resolved-ip innerhalb des connect-Blocks. Es stammt vom Wegwerf-Socket, genauer von dessen Namensauflösung mit gethostbyname. Dieses Feld ist immer befüllt, auch bei einem Fehlschlag, weil die Namensauflösung praktisch immer gelingt, selbst wenn die eigentliche Verbindung danach scheitert. Dieses Feld benutzt man für die Region-Zuordnung, für die ASN-Klassifikation, also welchem autonomen Netz die IP gehört, und für die Verfügbarkeitsrechnung.

Warum braucht es überhaupt zwei Felder? Wegen Round-Robin. Round-Robin ist ein Verfahren, bei dem ein Hostname reihum auf mehrere verschiedene IP-Adressen aufgelöst wird, mal die eine, mal die nächste. Wenn ein Anbieter Round-Robin macht, kann der Wegwerf-Socket eine andere IP ziehen als die eigentliche Mess-Anfrage kurz danach. Und genau das passiert: Bei Round-Robin weichen die beiden Felder in rund neunundzwanzig Prozent der Fälle voneinander ab. Deshalb darf man sie nicht in einen Topf werfen.


Die Fail-Filter-Falle.

Daraus folgt eine besonders gemeine Falle, vor der du gewarnt sein musst. Man darf Fehlschläge niemals darüber herausfiltern, dass man sagt, das top-level-resolved-ip ist null, also wirf alle Zeilen mit null heraus. Denn bei einem Fehlschlag ist dieses Feld ja gerade null. Wenn du also über null filterst, schmeißt du genau die Timeouts und Verbindungsabbrüche raus, die du für die Verfügbarkeitsrechnung dringend brauchst. Du würdest die Verfügbarkeit also künstlich auf hundert Prozent schönrechnen, weil alle Ausfälle unsichtbar geworden sind.

Die richtige Methode ist: Filtere Fehlschläge immer über das success-Flag oder über den gespeicherten Fehler-String, niemals über das null-Feld. Das success-Flag ist die ausdrückliche Erfolg-oder-Fehlschlag-Markierung, die jeder Datensatz trägt, und der Fehler-String enthält den rohen Grund des Scheiterns. Beides bleibt auch bei einem Ausfall erhalten und macht den Ausfall sichtbar, statt ihn verschwinden zu lassen.


Der Output-Mengen-Confound.

Zum Schluss noch eine konzeptionelle Falle, die unter dem Audit-Punkt A acht geführt wird. Zuerst der Begriff Confound. Ein Confound, auf Deutsch eine Störgröße oder ein Störfaktor, ist eine versteckte dritte Größe, die einen Vergleich verfälscht, weil sie sich mit der eigentlich interessierenden Größe vermischt. Man glaubt, man messe A, in Wahrheit misst man A vermischt mit B.

Hier ist der Confound die Ausgabemenge. Die Metrik total-Millisekunden misst die Zeit, bis die komplette Antwort fertig ist. Diese Zeit skaliert natürlich mit der Länge der Ausgabe: Wer mehr sagt, braucht länger. Die Falle ist also, dass ein wortkarges Modell schnell wirkt, obwohl es nur knapp antwortet und nicht etwa schneller rechnet. Es gewinnt durch Knappheit, nicht durch Tempo. Würde man Anbieter nach total-Millisekunden ranken, könnte ein einsilbiges Modell einen Pseudo-Sieg einfahren.

Die Lösung ist, dass die Zeit bis zum ersten Token und die Zeit bis zum ersten Audio die primären Metriken sind. Diese beiden sind mengen-unabhängig, weil sie nur bis zum allerersten Ausgabe-Element messen, und das erste Token kommt gleich schnell, egal ob danach noch fünf oder fünfzig Tokens folgen. Total-Millisekunden bleibt nur sekundär und wird nur pro Token normalisiert berichtet, also durch die Anzahl der Tokens geteilt, damit die reine Tempo-Komponente sichtbar wird statt der bloßen Menge.

Ein Detail dazu beim Sprachmodell: Die Obergrenze für die Ausgabe, im Code max-tokens auf fünfzig gesetzt, ist ein Cap, also eine Obergrenze, kein Fixwert. Cap heißt, das Modell darf höchstens so viel ausgeben, muss es aber nicht. Deshalb streut die tatsächliche Ausgabemenge trotzdem, und deshalb darf man total-Millisekunden eben nicht roh vergleichen.

Beim Text-to-Speech gibt es eine ganz analoge Sache mit den Audio-Bytes. Dort ist nur der Container gepinnt, also festgelegt, nämlich das Format em-pe-drei, aber nicht die Bitrate. Weil die Anbieter unterschiedliche Bitraten liefern, streut die Zahl der Audio-Bytes um rund das dreikommasechs-fache. Deshalb dienen die Audio-Bytes nur als Erfolgs-Gate, also nur dazu zu prüfen, ob überhaupt sinnvoll Audio ankam, und niemals als Vergleichsmaß zwischen den Anbietern. Auch hier gilt: Die Zeit bis zum ersten Audio bleibt fair, weil sie nur das erste Audio-Byte misst und damit mengen-unabhängig ist, während total-Millisekunden zwischen den Anbietern nicht vergleichbar ist.

Damit hast du die ganze Layer-drei-Metrik beieinander: atomare Submetriken über den Wegwerf-Socket, die Asymmetrie zwischen connect-exklusivem Speech-to-Text und connect-inklusivem Sprachmodell und Text-to-Speech, die korrekte End-to-End-Formel ohne doppelten connect, die zwei IP-Felder mit der Fail-Filter-Falle, und der Output-Mengen-Confound, der die Erste-Ausgabe-Metriken zu den primären macht. Und denk daran, alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.

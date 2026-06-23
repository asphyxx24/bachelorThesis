Modul sieben. Layer zwei. Die Paket-Eichung.


Worum es geht.

In diesem Modul geht es um eine einzige, sehr konkrete Frage. Kann man dem App-Timer trauen, also der Stoppuhr, die im Python-Code läuft und die Verbindungsaufbauzeit misst? Der Professor hat gesagt, er vertraue den Daten nicht. Genau hier setzt Layer zwei an. Wir beweisen mit echten Netzwerkpaketen, dass die Zeit, die der Code misst, mit der Zeit übereinstimmt, die wirklich auf der Leitung vergeht. Das nennt man Eichung oder Kalibrierung. Und genauso wichtig ist die ehrliche Kehrseite. Wir sagen klar, was damit geeicht ist und was eben nicht.

Zuerst ein paar Begriffe, damit der Rest verständlich ist.


Was Eichung oder Kalibrierung bedeutet.

Eichung, auch Kalibrierung genannt, heißt, dass man ein Messinstrument gegen eine vertrauenswürdige Referenz prüft. Man misst dieselbe Sache mit zwei verschiedenen Methoden und schaut, ob beide dasselbe Ergebnis liefern. Wenn ja, ist das Instrument geeicht, man kann ihm vertrauen. Bei einer Küchenwaage würde man ein bekanntes Gewicht auflegen und schauen, ob die Anzeige stimmt. Bei uns ist das Messinstrument der App-Timer im Python-Code, und die vertrauenswürdige Referenz ist die echte Paketmitschrift auf der Netzwerkleitung. Wir wollen zeigen: was der Code misst, ist das, was wirklich passiert.


Was tcpdump und eine PCAP sind.

Tcpdump ist ein Programm, das den gesamten Netzwerkverkehr mitschneidet, der über eine Netzwerkkarte läuft. Man kann es sich vorstellen wie ein Aufnahmegerät, das jedes einzelne Datenpaket aufzeichnet, das der Rechner sendet oder empfängt. Diese Aufzeichnung wird in eine Datei geschrieben, die PCAP heißt, das steht für Packet Capture, also Paketmitschnitt. In der PCAP steht für jedes Paket, wann es kam, woher, wohin, und welche Steuer-Markierungen es trug. Wichtig ist: tcpdump arbeitet unterhalb der Anwendung, direkt am Netzwerk. Es sieht die Wirklichkeit auf der Leitung, unabhängig davon, was der Python-Code glaubt zu messen. Genau deshalb ist es eine glaubwürdige, unabhängige Referenz.


Was ein SYN und ein SYN-ACK sind, also der TCP-Handshake.

Bevor zwei Rechner über das Internet Daten austauschen, müssen sie eine Verbindung aufbauen. Das geschieht über das Protokoll TCP mit einem festen Begrüßungsritual, dem sogenannten Handshake, also Händedruck. Der Client, in unserem Fall die Mess-Instanz in Frankfurt, schickt zuerst ein kleines Paket mit einer gesetzten Markierung namens SYN. SYN steht für synchronize, also synchronisieren, und heißt sinngemäß: Ich möchte eine Verbindung aufbauen. Der Server antwortet mit einem Paket, das zwei Markierungen trägt, SYN und ACK. ACK steht für acknowledge, also bestätigen. Das heißt sinngemäß: Verstanden, und ich möchte ebenfalls verbinden. Die Zeit vom Absenden des SYN bis zum Eintreffen des SYN-ACK ist genau eine Round-Trip-Zeit, also einmal hin und einmal zurück über das Netzwerk. Diese Round-Trip-Zeit ist die Größe, die wir in diesem Modul prüfen. Der App-Timer nennt sie tcp underscore handshake underscore millisekunden. Die Paketmitschrift nennt sie SYN-zu-SYN-ACK.


Was ein Kernel-Zeitstempel ist.

Der Kernel ist der innerste Kern des Betriebssystems, die Schicht, die direkt mit der Hardware und der Netzwerkkarte spricht. Wenn ein Paket auf der Netzwerkkarte ankommt, vergibt der Kernel sofort einen Zeitstempel, also eine sehr genaue Uhrzeit-Notiz, wann das Paket eintraf. Tcpdump bekommt diese Kernel-Zeitstempel und schreibt sie in die PCAP. Das Wichtige daran ist: der Kernel-Zeitstempel entsteht ganz nah an der Leitung, fast ohne Umweg. Die Python-App dagegen bekommt erst dann mit, dass ein Paket da ist, wenn der Kernel ihr die Kontrolle zurückgibt, und das dauert ein winziges bisschen länger. Genau aus diesem winzigen Unterschied wird gleich der Offset, von dem wir noch sprechen.


Was perf underscore counter ist.

Perf underscore counter, ausgesprochen performance counter, ist die Stoppuhr, die der Python-Code benutzt. Es ist eine monotone, hochauflösende Uhr. Monoton heißt, sie kann nicht rückwärts springen, anders als die normale Systemuhr, die zum Beispiel durch eine Zeitsynchronisation verstellt werden könnte. Hochauflösend heißt, sie misst sehr fein, im Bereich von Bruchteilen einer Millisekunde. Sie ist nur für Dauer-Messungen gedacht, also für die Frage: wie viel Zeit ist zwischen Punkt A und Punkt B vergangen. Der Code startet diese Uhr direkt vor dem Verbindungsaufbau und stoppt sie direkt danach. Die Differenz ist der App-Timer tcp underscore handshake underscore millisekunden. Wichtig zu wissen: dieselbe Uhr, dieser perf underscore counter, wird auch für die anderen Zeiten benutzt, etwa die Zeit bis zum ersten Token. Das wird später noch entscheidend.


Was ein Quell-Port ist und warum die Paarung darüber funktioniert.

Wenn der Rechner eine Verbindung aufbaut, bekommt jede einzelne Verbindung vom Betriebssystem einen eigenen lokalen Port zugewiesen, den Quell-Port. Ein Port ist einfach eine Nummer, die eine bestimmte Verbindung auf dem Rechner eindeutig kennzeichnet. Man kann sich das vorstellen wie eine Hausnummer für eine bestimmte Unterhaltung. Das Ziel ist immer dasselbe, nämlich Port vierhundertdreiundvierzig beim Server, das ist der Standard-Port für verschlüsselte Verbindungen. Aber der Quell-Port auf unserer Seite ist bei jedem einzelnen Cold-Start neu und einzigartig.

Und genau das ist der Trick für die Paarung. Wir machen rund dreißig Verbindungsaufbauten nacheinander, und tcpdump schneidet währenddessen alle Pakete mit. Hinterher müssen wir aber wissen, welches Paket-Paar in der Mitschrift zu welcher App-Messung gehört. Der Quell-Port ist der gemeinsame Schlüssel. Der Code notiert für jede Verbindung ihren Quell-Port zusammen mit der gemessenen Zeit. Und in der PCAP trägt jedes SYN und jedes SYN-ACK ebenfalls diesen Quell-Port. So lässt sich Connect Nummer eins aus dem App-Log eindeutig dem SYN-zu-SYN-ACK-Paar mit demselben Quell-Port in der Mitschrift zuordnen, Connect Nummer zwei dem nächsten und so weiter. Ohne den Quell-Port hätte man nur einen Haufen Pakete und einen Haufen Zeiten und wüsste nicht, was zu was gehört. Mit dem Quell-Port wird aus dem Haufen eine saubere Eins-zu-eins-Paarung.


Das Eich-Experiment. Was gegen was verglichen wird.

Jetzt zum eigentlichen Experiment. Auf der Mess-Instanz in Frankfurt werden rund dreißig Cold-Start-Verbindungen ausgeführt. Cold-Start heißt, jede Verbindung wird frisch aufgebaut und danach wieder geschlossen, kein Wiederverwenden. Währenddessen läuft tcpdump mit und schneidet den echten Netzwerkverkehr in eine PCAP-Datei.

Verglichen werden zwei Dinge. Auf der einen Seite die App-Messung, also tcp underscore handshake underscore millisekunden aus dem perf underscore counter im Python-Code. Das ist, was die Anwendung glaubt gemessen zu haben. Auf der anderen Seite die Leitungs-Messung, also SYN-zu-SYN-ACK aus den Kernel-Zeitstempeln in der Paketmitschrift. Das ist, was wirklich auf der Leitung passiert ist. Gepaart wird über den Quell-Port, wie gerade beschrieben. So bekommt man für jeden einzelnen Connect ein Paar aus App-Wert und Leitungs-Wert und kann die Differenz ausrechnen.

Ein wichtiges Detail zur Wahl des Anbieters. Geeicht wird gegen einen host-terminierten Anbieter, konkret Azure und Deepgram, nicht gegen einen Cloudflare-Edge-Knoten. Der Grund: bei einem Edge-Anbieter wäre der Vergleich tautologisch, also ein Zirkelschluss, weil Verbindungsaufbau und Ping denselben Knoten treffen. Bei einem echten entfernten Host ist der Vergleich aussagekräftig. Außerdem fixiert man bewusst eine einzige Ziel-IP, denn Deepgram verteilt über mehrere Server. Nur mit fester Ziel-IP zeigen der Aufnahme-Filter und alle dreißig Verbindungen auf denselben Knoten.


Das Ergebnis. Übereinstimmung auf rund ein Zehntel einer Millisekunde.

Das Ergebnis ist der eigentliche Clou. Die App-Messung und die Leitungs-Messung stimmen auf rund ein Zehntel einer Millisekunde überein. Und zwar an beiden Enden der Skala.

Beim ersten Fall, Azure mit Sitz in Italy North, beträgt der Handshake rund elf Millisekunden. Der App-Timer lag im Mittel bei etwa elf Komma neunundzwanzig Millisekunden, die Leitung bei etwa elf Komma achtzehn Millisekunden. Die Differenz ist also rund plus null Komma elf Millisekunden.

Beim zweiten Fall, Deepgram in den USA, beträgt der Handshake rund hundertneununddreißig Millisekunden, also mehr als das Zehnfache. Der App-Timer lag bei etwa hundertneununddreißig Komma null eins Millisekunden, die Leitung bei etwa hundertachtunddreißig Komma neunundachtzig Millisekunden. Die Differenz ist wieder rund plus null Komma eins zwei Millisekunden.

Das ist der entscheidende Punkt. Egal ob der Handshake elf Millisekunden oder hundertneununddreißig Millisekunden dauert, die Differenz zwischen App und Leitung bleibt fast gleich, nämlich rund ein Zehntel einer Millisekunde. Damit ist der Connect-Timer paket-validiert. Das ist die Contribution C zwei, also der zweite eigene Beitrag der Arbeit. Wichtig dabei: alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.


Was der Offset von plus einem Zehntel einer Millisekunde bedeutet.

Jetzt zur Bedeutung dieses kleinen Pluszeichens. Die App misst minimal mehr als die Leitung. Warum? Zwischen dem Kernel-Ereignis, also dem Moment, in dem das SYN-ACK auf der Netzwerkkarte eintrifft und der Kernel seinen Zeitstempel setzt, und dem Moment, in dem die Python-App die Kontrolle zurückbekommt und ihre eigene Uhr stoppt, vergeht eine winzige Rückkehrzeit. Der Kernel muss die App sozusagen erst aufwecken und ihr sagen, dass die Verbindung steht. Diese winzige Zeitspanne misst die App zusätzlich mit, der Kernel-Zeitstempel nicht. Deshalb ist die App-Zahl immer ein klein wenig größer, und zwar immer in dieselbe Richtung, daher das Pluszeichen.

Und jetzt kommt das Wichtigste, was man dem Professor sagen muss. Dass dieser Offset klein ist und vor allem konstant bleibt über völlig unterschiedliche Handshake-Dauern, von elf Millisekunden bis hundertneununddreißig Millisekunden, das ist genau das Kennzeichen einer sauberen Messung. Es ist kein Fehler. Würde der Offset mit der Handshake-Dauer mitwachsen, also bei hundertneununddreißig Millisekunden plötzlich auch zehnmal so groß sein, dann hätte man ein systematisches Problem im Timer. Aber er bleibt klein und konstant. Das beweist: der App-Timer hat einen festen, vernachlässigbaren, gerichteten Versatz, der durch die normale Betriebssystem-Mechanik erklärbar ist, und sonst nichts. Ein konstanter, kleiner, erklärbarer Offset ist ein Gütesiegel, kein Mangel.


Die ehrliche Kehrseite. Was nicht geeicht ist.

Jetzt der Teil, der genauso wichtig ist, vielleicht sogar wichtiger für die Glaubwürdigkeit. Es wäre verlockend zu behaupten, jetzt seien alle Zahlen aus Layer drei paket-validiert. Das wäre aber falsch, und der Professor würde es sofort durchschauen. Diese Reichweiten-Grenze trägt im Audit den Namen H zwei.

Geeicht ist ausschließlich der Connect-Timer, also tcp underscore handshake underscore millisekunden, die Zeit für den TCP-Handshake. Nicht geeicht sind die Zeit bis zum ersten Token, die Zeit bis zum ersten Audio und die Zeit bis zum ersten Partial. Warum nicht? Diese drei Metriken nutzen zwar denselben perf underscore counter, dieselbe Stoppuhr. Aber sie starten an einer ganz anderen Stelle. Sie starten erst beim Absenden des eigentlichen Requests, und zwar tief im produktiven Software-Stack, also in den Bibliotheken httpx für gewöhnliche Web-Anfragen und websockets für die dauerhaften Verbindungen. Der Eich-Pfad dagegen lief über einen ganz einfachen, rohen Socket, nicht über diesen produktiven Stack. Deshalb decken die Pakete den Handshake-Teil ab, aber nicht den Teil, in dem die Engine rechnet und das erste Token oder Audio liefert.

Was darf man also sagen und was nicht? Man darf nie behaupten, alle Layer-drei-Zahlen seien mit Paketen validiert. Validiert ist der Verbindungsaufbau-Teil. Für die Zeit bis zum ersten Token und die anderen Erste-Ausgabe-Metriken gilt nur das schwächere, aber ehrliche Argument: sie laufen über denselben geprüften Uhren-Mechanismus wie der validierte Connect-Timer. Das ist ein Vertrauens-Transfer über den geteilten Timer, kein direkter Paket-Beweis. Genau so formuliert bleibt die Aussage wasserdicht. Es gäbe einen optionalen Ausbau in der Analyse-Phase, nämlich das erste Antwort-Paket aus der PCAP gegen die Zeit bis zum ersten Token zu paaren. Aber das ist Zukunftsmusik und für die Eichung selbst nicht nötig.


Was du dir aus diesem Modul merken solltest.

Erstens, geeicht heißt: zwei unabhängige Messungen derselben Sache stimmen überein. Hier der App-Timer aus dem Python-Code gegen die echte Leitungszeit aus der Paketmitschrift, gepaart über den eindeutigen Quell-Port. Zweitens, das Ergebnis ist eine Übereinstimmung auf rund ein Zehntel einer Millisekunde, an beiden Enden der Skala, von elf bis hundertneununddreißig Millisekunden. Drittens, der kleine, konstante Plus-Offset ist die Kernel-Rückkehrzeit und ein Gütesiegel, kein Fehler. Viertens, und das ist die Ehrlichkeit, die den Professor überzeugt: geeicht ist nur der Connect-Timer. Die Zeit bis zum ersten Token, ersten Audio und ersten Partial ist nicht direkt paket-geeicht, sie erbt das Vertrauen nur über denselben Uhren-Mechanismus. Und alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.

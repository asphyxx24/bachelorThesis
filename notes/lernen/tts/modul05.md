Modul fünf. Aufbau, Cold-Start und Messkampagne.


Worum es geht.

In diesem Modul geht es um das gesamte Messdesign. Also nicht um eine einzelne Zahl, sondern um die Architektur des Experiments: Von welchem Punkt aus wird gemessen, wie sieht eine einzelne Messung aus, wie sind die vielen Messungen über die Zeit verteilt, und wie wird das Ganze so verankert, dass man es später lückenlos nachvollziehen kann. Der Prüfer, Professor Wählisch, hat dem alten Lauf misstraut, weil genau dieses Setup nicht sauber dargelegt war. Dieses Modul ist die Antwort darauf. Du sollst am Ende jeden der folgenden vier Punkte einem Skeptiker in eigenen Worten erklären können: warum eine bestimmte Server-Art, warum jede Messung bei null beginnt, warum die Messungen an festen Uhrzeiten in einer bestimmten Zeitzone liegen, und warum es so viele davon sind.


Der Vantage Point. Was das ist und warum Frankfurt.

Der Begriff Vantage Point bedeutet wörtlich Aussichtspunkt, im Messkontext ist es der Ort, von dem aus gemessen wird, also der Standort des Mess-Clients. Die Forschungsfrage dieser Arbeit ist eine europäische Perspektive: Wie verhalten sich kommerzielle Cloud-Schnittstellen für künstliche Intelligenz aus europäischer Sicht. Deshalb steht der Mess-Rechner in Europa, genauer gesagt in Frankfurt am Main, weil Frankfurt einer der zentralen Internet-Knoten Europas ist. Konkret ist der Mess-Rechner eine virtuelle Maschine bei Amazon Web Services, also bei einem der großen Cloud-Anbieter, in der Region eu-central-eins, das ist Frankfurt.

Wichtig ist hier eine ehrliche Einschränkung, die man dem Prüfer von sich aus sagen sollte. Es gibt nur diesen einen Vantage Point, also nur Frankfurt. Die gemessenen Round-Trip-Zeiten, das ist die Zeit, die ein Datenpaket für Hinweg und Rückweg braucht, sind damit Frankfurt-spezifisch. Ein anderer europäischer Standort sähe andere Distanzen zu den Servern. Der Kernbefund der Arbeit ist davon aber nicht betroffen, und das ist der entscheidende Punkt: Der Kernbefund ist negativ formuliert. Die drei Sprachmodelle hängen am selben Cloudflare-Edge in Frankfurt, also bei gleicher Netz-Distanz, antworten aber unterschiedlich schnell. Die Latenzspreizung ist damit durch Netznähe nicht erklärbar. Und gleiche Netz-Distanz bleibt gleich, egal von wo man schaut. Der eine Vantage Point ist also eine deklarierte Grenze, aber er untergräbt die zentrale Aussage nicht.


Warum keine burstable-Instanz. Der wichtigste Setup-Punkt.

Jetzt der erste der vier Prüf-Punkte, und der ist subtil, aber wichtig. Eine virtuelle Maschine bei einem Cloud-Anbieter heißt dort Instanz. Es gibt verschiedene Typen. Eine Klasse von Typen nennt man burstable, auf Deutsch etwa schubweise. Solche Typen, bei Amazon zum Beispiel die Familien t-zwei und t-drei, arbeiten mit einem Guthaben-System für Rechenleistung, man nennt das Prozessor-Guthaben. Die Idee dahinter: Solange du Guthaben hast, darfst du volle Rechenleistung ziehen. Ist das Guthaben aufgebraucht, drosselt der Anbieter die Rechenleistung, das nennt man Prozessor-Guthaben-Drosselung, also eine Drosselung wegen erschöpftem Prozessor-Guthaben.

Genau das ist für eine Latenz-Messung Gift. Wenn man Zeiten im Millisekunden-Bereich misst und mitten im Lauf die Rechenleistung der Maschine sprunghaft einbricht, dann springen die Mess-Timer, ohne dass im Netz irgendetwas passiert ist. Man bekäme also unerklärte Schwankungen in den Daten, die gar nichts mit den Servern zu tun haben, sondern nur damit, dass die eigene Mess-Maschine gerade gedrosselt wurde. Genau solche unerklärten Schwankungen waren ein Grund für das Misstrauen des Prüfers am alten Lauf, und der alte Lauf lief tatsächlich auf einer burstable-Maschine, einer t-drei-Punkt-small.

Die Lösung ist eine nicht-burstable Instanz mit garantierter Rechenleistung. Konkret eine c-sechs-i-Punkt-large. Die hat zwei garantierte virtuelle Prozessor-Kerne und vier Gigabyte Arbeitsspeicher, das reicht locker, weil die Mess-Last netzwerk-gebunden ist und nicht rechen-intensiv. Und jetzt kommt der Clou: Dass tatsächlich nicht gedrosselt wurde, wird nicht einfach behauptet, sondern empirisch belegt. Zu jedem Slot wird die sogenannte Prozessor-Steal-Zeit mitgeloggt, das ist ein Wert, der anzeigt, wie viel Rechenzeit der Maschine vom Hypervisor weggenommen wurde. Im Pilot lag dieser Wert flach bei siebenunddreißig zu siebenunddreißig über den Slot, also keine Veränderung, also keine Drosselung. Man kann dem Prüfer damit sagen: Ich habe nicht nur den richtigen Maschinen-Typ gewählt, ich kann auch in den Daten zeigen, dass er nicht gedrosselt wurde.

Zur Software-Umgebung gehört noch: Es läuft echtes OpenSSL in Version drei Punkt x, das ist die Verschlüsselungs-Bibliothek, und die Uhr der Maschine wird per chrony synchron gehalten, das ist ein Dienst zur Zeit-Synchronisation. Alles läuft in koordinierter Weltzeit.


Warum Cold-Start, kein Connection-Pooling. Der zweite Prüf-Punkt.

Cold-Start heißt wörtlich Kaltstart und meint hier: Jede einzelne Messung baut eine komplett neue Verbindung auf und schließt sie danach wieder. Eine neue Verbindung bedeutet einen frischen Transport-Handshake, das ist der dreistufige Verbindungsaufbau auf der Transport-Ebene, und einen frischen Aufbau der Transport-Verschlüsselung in Version eins Punkt drei. Erst danach wird die eigentliche Anfrage geschickt. Das Gegenteil davon nennt man Connection-Pooling oder Keep-Alive: Da hält man eine einmal geöffnete Verbindung offen und nutzt sie für viele Anfragen wieder.

Warum also der Kaltstart und nicht das viel effizientere Pooling. Weil gerade der Verbindungsaufbau zum Backend der aus europäischer Sicht interessante Anteil ist. Wenn ein Nutzer eine Sprach-Interaktion startet, baut sein Gerät eine frische Verbindung zum Dienst auf, das ist die Erste-Eindruck-Latenz, der Moment, in dem man die Distanz und den Aufbau spürt. Würde man Pooling nutzen, fiele der Verbindungsaufbau ab dem zweiten Aufruf weg, weil die Verbindung ja schon steht. Man würde damit genau den Teil wegmitteln, den man eigentlich messen will. Der Kaltstart ist also kein Versehen und keine Ineffizienz, sondern eine bewusste Entscheidung, die den interessanten Anteil sichtbar hält.


Die Struktur der Kampagne. Sieben Tage, acht Slots, hundert Messungen.

Jetzt zur zeitlichen Verteilung. Eine einzelne Messung wäre ein Schnappschuss. Aussagekraft entsteht erst durch viele Messungen, die drei Quellen von Schwankung abdecken. Erstens die Schwankung von Aufruf zu Aufruf, der reine Jitter, den fängt man durch viele Wiederholungen. Zweitens die Schwankung über den Tag, weil die Last auf den Servern tagsüber anders ist als nachts, den fängt man durch mehrere Uhrzeiten. Und drittens die Schwankung über die Woche, weil Wochentag und Wochenende sich unterscheiden, den fängt man durch sieben Tage.

Konkret sieht das so aus: sieben Tage, mal acht feste Mess-Fenster pro Tag, mal hundert Messungen pro Endpunkt und Fenster. Ein solches Mess-Fenster nennt man einen Slot. Die acht Slots liegen alle drei Stunden, also um null Uhr, drei Uhr, sechs Uhr, neun Uhr, zwölf Uhr, fünfzehn Uhr, achtzehn Uhr und einundzwanzig Uhr. Sieben Tage mal acht Slots ergibt sechsundfünfzig Slots. Sechsundfünfzig Slots mal hundert Messungen ergibt fünftausendsechshundert Messungen pro Endpunkt. Und weil es neun Endpunkte gibt, drei Anbieter pro Kategorie in den drei Kategorien Speech-to-Text, Sprachmodell und Text-to-Speech, ergibt das insgesamt rund fünfzigtausendvierhundert Aufrufe. Ein wichtiger Hinweis: Alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.


Warum feste Slots in koordinierter Weltzeit. Der dritte Prüf-Punkt.

Warum acht feste Uhrzeiten, und warum ausgerechnet in koordinierter Weltzeit und nicht in lokaler Zeit. Der Grund ist Sauberkeit über mehrere Tage hinweg. Koordinierte Weltzeit kennt keine Zeitzonen-Verschiebung und keine Sommerzeit. In lokaler Zeit gibt es einmal im Jahr einen Sommerzeit-Sprung, an dem eine Stunde verschwindet oder doppelt vorkommt. Würde man in lokaler Zeit messen, wäre der Tagesgang, den man vergleichen will, also das diurnale Muster, an einem solchen Sprung-Tag verschoben und nicht mehr sauber mit den anderen Tagen vergleichbar. In koordinierter Weltzeit gibt es diesen Sprung nicht, jeder Drei-Uhr-Slot meint über alle sieben Tage exakt denselben Moment im Tageszyklus.

Es gibt noch einen inhaltlichen Grund für die volle Vierundzwanzig-Stunden-Abdeckung. Der Tagesgang der Last betrifft vor allem die amerikanischen Backends. Die Slots müssen deshalb sowohl das amerikanische Tageshoch treffen, das ist der Nachmittag an der amerikanischen Ostküste, also etwa achtzehn bis zweiundzwanzig Uhr koordinierter Weltzeit, als auch das amerikanische Nachttief, also etwa sechs bis zehn Uhr koordinierter Weltzeit. Würde man nur europäische Bürozeiten messen, sähe man dieses Muster gar nicht.

Damit es bei der Auswertung keine Verwirrung gibt, wird zu jeder Messung das Slot-Etikett mitgeschrieben, also zum Beispiel null-drei-h für den Drei-Uhr-Slot. Die Auswertung gruppiert dann nach diesem Etikett und nicht nach der Stunde im Zeitstempel. Das verhindert, dass ein leicht verspäteter Slot fälschlich in eine falsche Stunde rutscht und einen Phantom-Slot erzeugt.


Warum interleaved und nicht block. Die Fairness zwischen Anbietern.

Innerhalb eines Slots stellt sich die Frage: in welcher Reihenfolge ruft man die neun Endpunkte auf. Hier wurde bewusst das verschränkte Verfahren gewählt, auf Englisch interleaved. Verschränkt heißt: Jede Runde geht einmal der Reihe nach durch alle neun Endpunkte, also ein Kaltstart-Aufruf je Anbieter, und das wiederholt sich hundert Runden lang. Man nennt das auch Round-Robin, also reihum. Zusätzlich rotiert die Startreihenfolge in jeder Runde, damit kein Anbieter immer an derselben Position steht.

Die Alternative wäre die Block-Variante: erst hundert Mal Anbieter A, dann hundert Mal Anbieter B, und so weiter. Das Problem dabei: Wenn die Netz- oder Server-Last sich zwischen den Blöcken ändert, was über einen Slot von vielen Minuten leicht passiert, dann sähe man einen vermeintlichen Anbieter-Unterschied, der in Wahrheit nur ein Zeit- oder Last-Effekt zwischen den Blöcken ist. Beim verschränkten Verfahren sehen dagegen alle neun Anbieter dieselbe Verteilung der Netzbedingungen über den ganzen Slot, weil sie ständig abwechselnd drankommen. Das macht den Vergleich zwischen den Anbietern fair. Ein angenehmer Nebeneffekt: Zwischen zwei Aufrufen desselben Anbieters liegen immer acht andere Aufrufe, das entlastet die Rate-Limits der Anbieter.


Warum fünftausendsechshundert pro Endpunkt. Der vierte Prüf-Punkt.

Warum so viele Messungen pro Endpunkt. Hundert pro Slot wäre schon komfortabel, um pro Slot einen belastbaren Median und mittlere Perzentile zu bekommen. Der Grund für die hohe Gesamtzahl liegt aber bei den hohen Perzentilen. Ein Perzentil ist ein Schwellwert in der sortierten Verteilung. Das neunzigste Perzentil ist der Wert, unter dem neunzig Prozent aller Messungen liegen, das fünfundneunzigste entsprechend fünfundneunzig Prozent. Gerade diese hohen Perzentile, also das fünfundneunzigste und das neunundneunzigste, beschreiben das langsame Ende, den Schwanz der Verteilung, und genau dieser Schwanz ist bei Latenzen besonders interessant, weil dort die unangenehmen Ausreißer sitzen.

Für solche hohen Perzentile braucht man viele Daten, sonst sind sie reines Rauschen. Es gibt eine Faustregel dazu, die in Modul dreizehn genauer vorkommt: Für ein Perzentil q sollte die Stichprobengröße n mal eins minus q größer oder gleich etwa fünf bis zehn sein. Für das neunundneunzigste Perzentil heißt das, man braucht hunderte bis tausende Werte, damit der Schwellwert stabil wird. Hundert Messungen je Slot reichen dafür nicht, deshalb werden die hohen Perzentile nur gepoolt über alle sechsundfünfzig Slots berechnet, und die fünftausendsechshundert pro Endpunkt geben dieser gepoolten Schätzung genug Substanz. Kurz gesagt: Die hohe Zahl dient nicht dem Median, den hätte man billiger, sondern der Belastbarkeit der hohen Perzentile.


Der Reproduzierbarkeits-Anker. Die Lauf-Metadaten.

Damit ein Skeptiker das Experiment nicht nur glauben, sondern nachvollziehen kann, wird zu jedem Slot ein eigener Metadaten-Datensatz geschrieben, der run_meta-Record. Das passiert einmal pro Slot, nicht pro Messung, und es ist die erste Zeile jeder Slot-Datei. Darin steht alles, was man braucht, um den Slot eindeutig einzuordnen.

Im Einzelnen enthält dieser Datensatz: den genauen Stand des Mess-Codes als git-Commit, also die Versionskennung des Programms, plus ein dirty-Flag, das anzeigt, ob am Code zur Laufzeit ungespeicherte Änderungen waren. Dann den Hash der Lockfile, das ist eine Prüfsumme über die exakt festgenagelten Versionen aller Programm-Bibliotheken, denn nur damit ist die Software-Umgebung reproduzierbar. Weiter die Instanz-Kennung der Mess-Maschine, die schon erwähnte Prozessor-Steal-Zeit zu Slot-Beginn, deren Slot-Ende-Gegenstück im abschließenden run_end-Datensatz steht, als Beleg gegen Drosselung, die Version der OpenSSL-Verschlüsselungs-Bibliothek, und einen Schnappschuss des chrony-Status, also der Zeit-Synchronisation. Mit diesen Angaben kann man später für jeden einzelnen Slot belegen, mit welchem Code, auf welcher Maschine, unter welcher Zeitbasis und ohne Drosselung er entstanden ist.


Code eingefroren. Warum das wichtig ist.

Ein letzter, aber zentraler Punkt für die Vertrauenswürdigkeit: Sobald die Messphase begann, wurde der Code eingefroren. Eingefroren heißt, es wird während der laufenden Kampagne nichts mehr am Mess-Code geändert. Der maßgebliche Freeze-Commit, also der eingefrorene Code-Stand, ist die Version f-neun-e-sechs-d-c-acht. Alle Slots laufen gegen genau diesen Stand, der Mess-Code für Sprachmodell, Text-to-Speech, Speech-to-Text und den Orchestrator ist über die relevanten Versionen identisch.

Der Grund ist einfach: Wenn man mitten in der Messung das Programm ändert, weiß man hinterher nicht mehr, ob ein Unterschied in den Daten vom Server kommt oder von der eigenen Code-Änderung. Ein eingefrorener Code-Stand, kombiniert mit dem git-Commit im run_meta-Datensatz jedes Slots, macht jede einzelne Messung einer eindeutigen Code-Version zuordenbar. Damit ist das Setup so dargelegt, wie der Prüfer es verlangt hat: Man kann zu jeder Zahl sagen, von wo, womit, wann und unter welchen Bedingungen sie entstanden ist. Und nochmals zur Erinnerung: Alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.

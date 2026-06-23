Modul dreizehn. Aggregation und Verfügbarkeit.


Worum es geht.

Am Ende der Kampagne hast du je Endpunkt etwa fünftausendsechshundert Einzelmessungen. Niemand will fünftausendsechshundert Zahlen sehen, sondern eine einzige ehrliche Schlagzeilen-Zahl, zum Beispiel die Latenz von Deepgram. In diesem Modul lernst du, wie aus diesen vielen Einzelwerten genau eine verteidigbare Zahl wird, ohne dass du dabei mogelst. Und du lernst, warum die Verfügbarkeit, also die Frage, wie oft ein Anbieter überhaupt antwortet, eine eigene, getrennte Achse sein muss und nicht in die Latenz-Zahl hineingerechnet werden darf. Zur Erinnerung, der Vorbehalt, der über allem steht: Alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.


Ein kleiner Statistik-Vorlauf. Sechs Begriffe.

Bevor wir loslegen, klären wir sechs Begriffe, die du flüssig erklären können musst.

Der Mittelwert ist die Summe aller Werte geteilt durch ihre Anzahl, also der Durchschnitt. Sein Problem: Ein einziger extrem großer Ausreißer zieht ihn stark nach oben. Der Median dagegen ist der mittlere Wert, wenn du alle Messungen der Größe nach sortierst. Genau die Hälfte liegt darunter, die Hälfte darüber. Der Median ist robust, das heißt, ein paar Extremwerte verschieben ihn kaum. Weil unsere Latenz-Verteilungen rechtsschief sind, also einen langen Schwanz nach oben haben mit wenigen sehr langsamen Calls, nehmen wir grundsätzlich den Median und nicht den Mittelwert.

Ein Perzentil ist eine Verallgemeinerung des Medians. Das fünfzigste Perzentil, kurz p fünfzig, ist genau der Median: Die Hälfte der Werte liegt darunter. Das neunzigste Perzentil, p neunzig, ist der Wert, unter dem neunzig Prozent aller Messungen liegen. Das fünfundneunzigste Perzentil, p fünfundneunzig, und das neunundneunzigste Perzentil, p neunundneunzig, sagen dir etwas über den langsamen Schwanz, also über die schlimmsten Fälle. Wenn jemand fragt, wie schlecht wird es im Extremfall, dann antworten die hohen Perzentile.

Ein Bootstrap-Konfidenzintervall ist ein Werkzeug, das dir sagt, wie sicher eine geschätzte Zahl überhaupt ist. Bootstrap heißt, du ziehst aus deinen vorhandenen Messwerten viele tausend Mal zufällig eine neue Stichprobe mit Zurücklegen, rechnest jedes Mal die interessierende Zahl neu aus, etwa den Median, und schaust dir an, wie stark diese Werte streuen. Das fünfundneunzig-Prozent-Konfidenzintervall ist dann der Bereich, in dem fünfundneunzig Prozent dieser nachgespielten Schätzungen liegen. Es ist also eine ehrliche Spannweite um deine Zahl herum statt einer nackten Punktangabe. Wir nehmen Bootstrap und nicht das klassische Intervall, weil unsere Verteilungen schief sind und die klassische Formel Symmetrie unterstellt, die hier nicht gilt.

Eine Pareto-Front ist ein Konzept aus dem Vergleich nach zwei Gütedimensionen gleichzeitig. Stell dir zwei Achsen vor, eine für Latenz und eine für Verfügbarkeit. Ein Anbieter liegt auf der Pareto-Front, wenn es keinen anderen gibt, der in beiden Dimensionen zugleich besser ist. Die Front ist also die Menge der nicht dominierten Kandidaten. Sie macht sichtbar, dass schnell und zuverlässig zwei verschiedene Qualitäten sind und dass man nicht beide in eine einzige Bestenliste pressen kann.

Zensur, auf Englisch censoring, heißt in der Statistik, dass du den wahren Wert einer Messung nicht kennst, sondern nur weißt, dass er oberhalb einer bestimmten Grenze liegt. Bei uns ist diese Grenze der Timeout von rund dreißig Sekunden. Wenn ein Call nach dreißig Sekunden abgebrochen wird, weißt du nur: Die echte Latenz wäre größer gewesen als dreißig Sekunden, aber wie groß genau, weißt du nicht. Dieser Wert ist zensiert. Das ist gleich der Schlüssel, um zu verstehen, wie ein Anbieter gleichzeitig schnell und furchtbar im Schwanz sein kann.


Die Aggregationsregel. Der zweistufige Median.

Jetzt die Kernregel, intern A vier genannt. Die Schlagzeilen-Zahl je Endpunkt ist nicht einfach der Median über alle fünftausendsechshundert Rohwerte. Sie wird in zwei Stufen gebildet. Erste Stufe: Du bildest für jede Kombination aus Endpunkt und Slot den Median über die Messungen in genau diesem Slot. Über die volle Woche sind das pro Slot rund siebenhundert Runs, also sieben Tage mal hundert Messungen. So bekommst du acht Slot-Mediane, einen für jeden der acht Tageszeit-Slots. Zweite Stufe: Die Schlagzeilen-Zahl ist der Median dieser acht Slot-Mediane. Daher der Name, Median der Slot-Mediane.


Warum der Median der Slot-Mediane statt einfach poolen.

Poolen bedeutet, alle Rohwerte in einen Topf zu werfen und einmal den Median darüber zu nehmen. Das klingt einfacher, hat aber zwei Fallen. Erstens, Slots können unterschiedlich viele erfolgreiche Messungen enthalten. Ein gepoolter Median gewichtet dann den Slot mit mehr erfolgreichen Runs stärker. Das heißt, ausgerechnet die Tageszeiten mit besserer Verfügbarkeit ziehen die Zahl zu sich. Bei einem Anbieter, der zu den US-Stoßzeiten wegen Rate-Limits öfter ausfällt, verschönert das die Latenz-Zahl, weil gerade die schlechten Stunden weniger Stimmen haben. Zweitens, es könnte einen Tagesgang geben, einen sogenannten Diurnal-Effekt. Falls die Last auf den US-Backends über den Tag schwankt, wäre ein gepoolter Median dafür anfällig. Wichtig: Dieser Tagesgang ist nicht belegt, er ist eine Design-Annahme, gegen die der zweistufige Median robust macht. Der zweistufige Median gibt jeder Tageszeit das gleiche Gewicht, behandelt also jeden der acht Slots gleichberechtigt, und ist robust gegen einen einzelnen Ausreißer-Slot. Genau deshalb ist er der gepoolten Variante überlegen.


Die Gegenprobe. Und ein ehrlicher Vorbehalt zum Bootstrap.

Du berichtest trotzdem zusätzlich den gepoolten Median als Gegenprobe, also den Median über alle Rohwerte zusammen. Wenn der zweistufige und der gepoolte Median übereinstimmen, ist der Befund robust. Wenn sie auseinanderlaufen, ist genau das selbst ein Befund, nämlich ein Hinweis auf einen Tagesgang oder auf ausfallabhängige Verzerrung. Dazu kommt für jede Zahl ein fünfundneunzig-Prozent-Bootstrap-Konfidenzintervall. Wichtig ist hier ein ehrlicher Vorbehalt: Das Bootstrap-Konfidenzintervall über die Slot-Mediane steht noch aus. Bis es vorliegt, prüfst du immer zusätzlich gegen die gepoolte Variante gegen. Mit sechsundfünfzig von sechsundfünfzig Slots, der abgeschlossenen Vollkampagne, ist das Slot-Bootstrap belastbar.


Die Perzentil-Regel. Welches Perzentil aus welcher Datenmenge.

Nicht jedes Perzentil lässt sich aus jedem Datensatz seriös ziehen. Das fünfzigste und das neunzigste Perzentil sind schon pro Slot auflösbar, weil ein Slot mit hundert Messungen dafür genug Werte hat. Das fünfundneunzigste und das neunundneunzigste Perzentil dagegen darfst du nur über die volle Kampagne hinweg bilden, nicht pro Slot. Der Grund ist eine Faustregel: Ein Perzentil ist erst stabil, wenn die Anzahl der Werte mal eins minus dem Perzentil-Anteil mindestens etwa fünf bis zehn ergibt. Für das neunundneunzigste Perzentil heißt das, du brauchst viele hundert Werte, denn nur dann liegen genügend Messungen oberhalb der Schwelle, um sie überhaupt zu schätzen. Ein einzelner Slot mit hundert Messungen liefert das nicht. Bei hundert Werten wäre das neunundneunzigste Perzentil praktisch nur das Maximum, also der eine langsamste Wert, und das ist keine stabile Schätzung, sondern ein Zufallstreffer.


Die Verfügbarkeit als eigene Achse.

Jetzt der zweite Hauptpunkt. Die Latenz wird ausschließlich über erfolgreiche Calls berechnet. Das nennt man success-only, also nur die erfolgreichen. Ein gescheiterter Call hat ja gar keine sinnvolle Latenz, er hat nur einen Fehler. Die Verfügbarkeit, also die Erfolgs-Rate oder umgekehrt die Fehler-Rate, wird streng getrennt davon geführt, als eigene zweite Achse. Dargestellt wird das als Pareto-Front, Latenz gegen Verfügbarkeit. Der Grund ist einfach: Schnell und zuverlässig sind zwei verschiedene Gütedimensionen, und man darf sie nicht in eine einzige Zahl verquetschen. Das konkrete Beispiel aus den Daten: OpenAI-Text-to-Speech ist beim Median schnell, hat aber drei Komma eins Prozent Fehlschläge, das sind hundertdreiundsiebzig von fünftausendsechshundert Calls. Wer nur auf den Median schaut, würde OpenAI für hervorragend halten und die gescheiterten Anfragen komplett übersehen.


Die Survivorship-Zensur. Warum OpenAI-Text-to-Speech gleichzeitig schnell und im Schwanz das schlechteste sein kann.

Das ist der subtilste Punkt des Moduls, und ein Prüfer wird genau hier nachbohren. Die Frage lautet: Wie kann derselbe Anbieter beim Median schnell sein und trotzdem den schlimmsten Schwanz haben? Die Antwort heißt Survivorship-Zensur, also Überlebenden-Verzerrung kombiniert mit der eben erklärten Zensur. Bei drei Komma eins Prozent Fehlschlägen ist jedes Perzentil, das oberhalb der Fehler-Rate liegt, durch den Timeout zensiert. Rechne mit: Wenn drei Komma eins Prozent der Calls scheitern, dann landet das fünfundneunzigste Perzentil und erst recht das neunundneunzigste Perzentil im Bereich der gescheiterten Calls. Diese gescheiterten Calls brachen alle am Timeout von rund dreißig Sekunden ab. Das fünfundneunzigste und das neunundneunzigste Perzentil liegen damit bei rund dreißig Sekunden, also bei der Obergrenze, dem sogenannten Cap. Und jetzt der entscheidende Satz: Diese rund dreißig Sekunden sind kein echtes Backend-Tail. Sie sind nicht die Zeit, die das Backend zum Rechnen brauchte. Sie sind nur der abgeschnittene Timeout-Wert. So passt beides zusammen: Ein schneller Median für die erfolgreichen Calls und ein katastrophales Perzentil, das in Wahrheit nur der Abbruchgrenze entspricht. Deshalb musst du immer beides nebeneinander berichten. Du sagst zum Beispiel, das fünfundneunzigste Perzentil ist X, und zwar nur über die erfolgreichen Calls, also über die rund sechsundneunzig Komma neun Prozent, die durchkamen, und du nennst die Gesamtverfügbarkeit getrennt daneben. Nur so ist die Zahl ehrlich.


Die End-to-End-Faltung. Eine Monte-Carlo-Simulation, keine Addition.

Zuletzt die Gesamtlatenz der Pipeline, also End-to-End über alle drei Phasen Speech-to-Text, Sprachmodell und Text-to-Speech. Hier lauert ein klassischer Fehler, den du nicht machst: Man addiert nicht einfach die drei Mediane. Das wäre falsch. Stattdessen nimmst du eine Monte-Carlo-Faltung. Faltung ist der mathematische Name dafür, wie sich Verteilungen beim Summieren von Zufallsgrößen verbinden. Monte-Carlo heißt, du machst das durch Simulation. Konkret: Du ziehst aus der Verteilung der ersten Phase, also aus den gemessenen Zeiten bis zum ersten finalen Transkript beim Speech-to-Text, einen Zufallswert. Du ziehst aus der Verteilung der zweiten Phase, der Zeit bis zum ersten Token beim Sprachmodell, einen Zufallswert. Und du ziehst aus der dritten Phase, der Zeit bis zum ersten Audio beim Text-to-Speech, einen Zufallswert. Diese drei Werte summierst du zu einer Pipeline-Gesamtzeit. Und das wiederholst du rund zehntausend Mal. So entsteht die echte End-to-End-Verteilung, aus der du dann das fünfzigste, das neunzigste und das fünfundneunzigste Perzentil samt Konfidenzintervall ablesen kannst.


Warum die Summe der Perzentile falsch wäre.

Der Kernsatz dazu, den du verstehen musst: Das fünfundneunzigste Perzentil der Summe ist nicht die Summe der fünfundneunzigsten Perzentile. Warum nicht? Weil es extrem unwahrscheinlich ist, dass alle drei Phasen ausgerechnet im selben Call gleichzeitig ihren schlechtesten Wert treffen. Wenn du die drei hohen Perzentile addierst, unterstellst du genau dieses unwahrscheinliche Zusammentreffen, und das überschätzt den Schwanz dramatisch. Die Monte-Carlo-Faltung dagegen würfelt die Phasen unabhängig zusammen und bekommt die realistische Mischung, in der mal die eine, mal die andere Phase langsam ist, aber selten alle gleichzeitig. Genau deshalb ist die Simulation richtig und die Addition falsch.


Der rote Faden.

Halte am Ende den roten Faden fest. Aus fünftausendsechshundert Einzelwerten wird eine ehrliche Zahl durch den zweistufigen Median der Slot-Mediane, abgesichert durch die gepoolte Gegenprobe und ein Bootstrap-Konfidenzintervall. Hohe Perzentile gibt es nur über die volle Kampagne, weil ein einzelner Slot dafür zu wenige Werte hat. Verfügbarkeit ist eine eigene Achse, getrennt von der Latenz, dargestellt als Pareto-Front, weil schnell und zuverlässig verschiedene Dinge sind. Und das große Beispiel, OpenAI-Text-to-Speech kann gleichzeitig schnell im Median und das schlechteste im Schwanz sein, weil sein Schwanz nur der zensierte Timeout der drei Komma eins Prozent Fehlschläge ist und kein echtes Backend-Verhalten. Alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls; die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil.

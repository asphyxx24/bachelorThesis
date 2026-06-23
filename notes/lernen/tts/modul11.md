Modul elf. Die Anbieter-Matrix und warum überwiegend US.


Worum es geht.

Du sollst verteidigen können, warum genau diese neun Anbieter ausgewählt wurden, und warum die meisten in den USA gehostet sind, ohne dass das ein Auswahl-Fehler ist.


Die Pipeline und die neun Endpunkte.

Der Rahmen ist eine vollständige Voice-Pipeline, sequenziell: Sprache rein, dann Speech-to-Text, daraus Text, dann das Sprachmodell, daraus ein Antwort-Text, dann Text-to-Speech, daraus wieder Sprache. Pro Kategorie drei Anbieter, macht neun Mess-Endpunkte. Und der Bauplan jeder Kategorie ist bewusst gleich: ein oder mehrere US-Anbieter plus ein europa-naher Kontrastpunkt. Bei Speech-to-Text sind das Deepgram und Rev.ai aus den USA und Azure mit dem europäischen Rechenzentrum in Italien. Beim Sprachmodell OpenAI und Groq aus den USA und Mistral aus Frankreich. Beim Text-to-Speech Deepgram und OpenAI aus den USA und wieder Azure in Italien.


Warum genau diese neun.

Drei Kriterien. Erstens, es müssen marktreife, kommerzielle Anbieter sein. Zweitens, sie müssen eine echte Streaming-Schnittstelle haben, also Wort für Wort oder Stück für Stück liefern, nicht erst am Ende alles auf einmal. Drittens, roher Protokollzugang, damit kein Software-Entwicklungskit der Anbieter die Messung verfälscht. Und innerhalb jeder Kategorie ist bewusst ein europa-naher Anbieter gesetzt, damit man geografische Nähe überhaupt testen kann.


Warum überwiegend US, und warum das ein Befund ist und kein Fehler.

Das ist die heikelste Frage, und der Schlüssel ist die Umdeutung. Für Speech-to-Text und Text-to-Speech gibt es in dieser Qualitäts- und Reifeklasse praktisch keine europäisch gehosteten kommerziellen Streaming-Anbieter. Wer aus Europa eine produktive Voice-Pipeline baut, muss auf US-Engines zurückgreifen. Warum ist das kein Stichproben-Fehler? Ein Stichproben-Fehler wäre, wenn du absichtlich nur US-Anbieter genommen und damit ein verzerrtes Bild gemalt hättest, obwohl es gute europäische Alternativen gäbe. Hier ist es umgekehrt: Du hast europäische Anbieter gesucht, es gibt schlicht keine, die die Kriterien erfüllen. Die Auswahl bildet also die reale Marktlage ab. Damit ist überwiegend US selbst ein Eingangsbefund, der in der Limitations- und Diskussions-Sektion ausdrücklich benannt wird. Und er stützt sogar die Forschungsfrage: Die Anbieter-Wahl wird nicht durch Geografie oder Datenresidenz bestimmt, sondern durch die verfügbare Engine-Qualität.


Die Rolle von Mistral und Azure.

Die beiden europäischen Anbieter sind die eingebauten Kontrollpunkte für die Geografie-Hypothese. Mistral aus Frankreich ist der einzige marktreife europäische Anbieter beim Sprachmodell und ist bewusst gesetzt, um zu prüfen: Ist ein europäischer Anbieter schneller, weil er näher ist? Die Antwort ist nein. Mistral ist langsamer als das US-Groq, und beide hängen ohnehin am selben Frankfurt-Edge. Mistral ist also der Anbieter, der die Geografie-Inversion sichtbar macht. Azure mit dem Rechenzentrum in Italien ist der europa-nahe Infrastruktur-Gegenpol für Speech-to-Text und Text-to-Speech, ein echtes europäisches Rechenzentrum mit rund elf Millisekunden und ohne Content-Delivery-Netzwerk. Es ist der Beleg, dass eine niedrige Latenz auch ein echter naher Host sein kann, und liefert beim Text-to-Speech den schnellsten Wert. Ohne diese zwei hättest du nur US-Anbieter und könntest die Geografie-Frage gar nicht stellen.


Modell-Pinning gegen Drift.

Ein Reproduzierbarkeits-Detail. Wo möglich, ist die Modell-Version festgenagelt, das nennt man Pinning. Sonst könnte der Anbieter still das Modell hinter demselben Namen austauschen, das nennt man Modell-Drift, und deine Zahlen wären nicht mehr vergleichbar. Zusätzlich wird die vom Server tatsächlich zurückgemeldete Modell-Kennung pro Call mitgeloggt, sodass ein stiller Wechsel sample-genau sichtbar wird, statt unbemerkt zu bleiben.


Warum an der gemischten Auswahl festhalten.

Die neun Anbieter funktionieren unterschiedlich: manche terminieren am Edge, manche an einem echten Host, verschiedene Protokolle, verschiedene Regionen. Man könnte versucht sein, die Auswahl gleichförmig zu machen. Das wäre ein Fehler. Erstens ist die Verschiedenheit die Realität, die du beschreibst. Zweitens ermöglicht gerade die Verschiedenheit den Kernbeleg: dass die drei Sprachmodelle zufällig alle an derselben Edge terminieren, ist die Voraussetzung für das Kontrollexperiment. Drittens muss nicht jeder Anbieter jede Frage beantworten. Die Arbeit stellt drei Fragen: die Kausalfrage zu Netz gegen Backend, den beschreibenden Vergleich, und die Gesamt-Pipeline. Für die Kausalfrage tragen die Sprachmodelle und OpenAI Text-to-Speech bei, Speech-to-Text nicht. Für den Vergleich und die Pipeline tragen alle neun bei. Der Kernsatz fürs Gespräch: Die Anbieter wurden nicht trotz, sondern teils wegen ihrer Unterschiede behalten. Die saubere Haltung ist nicht, vergleichbar oder nicht, sondern: welche Frage beantwortet welcher Datensatz, und welche eben nicht. Verschiedenheit ist Befund, kein Mangel.

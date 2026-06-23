Modul zehn. Code-Architektur und Zeitmessung.


Worum es geht.

Du sollst ein Skript am Bildschirm grob durchgehen können. Nicht jede Zeile, aber: wo liegt was, wo läuft die Uhr, und wie setzt der Code die Methodik aus den vorigen Modulen technisch um. Das ist ein Überblick-Modul.


Die Verzeichnis-Struktur.

Der Code spiegelt die drei Schichten direkt wider. In Layer eins liegt die Netzwerk-Diagnose: eine zentrale Liste der neun Endpunkte plus die Einzel-Werkzeuge für TCP-Ping, ICMP, DNS, ASN, TLS und Traceroute. In Layer zwei liegt das Capture-Skript, das die Cold-Start-Verbindungen macht, während tcpdump mitschneidet, und das Analyse-Skript, das die Paket-Mitschrift auswertet. In Layer drei liegt das Herzstück: eine Konfigurationsdatei als zentrale Wahrheitsquelle, in der alle Endpunkte, Modelle, Timeouts und festen Eingaben an einer einzigen Stelle stehen; eine Connect-Datei, die die Verbindungs-Submetriken misst; je ein Caller für Sprachmodell, Text-to-Speech und Speech-to-Text; und ein Orchestrator, der alles zusammenführt und einen ganzen Slot abfährt. Merksatz: Konfiguration zentral, Messlogik pro Kategorie getrennt, Orchestrierung an einer Stelle.


Wie die Zeit gemessen wird und wo die Uhr läuft.

Alle Zeiten kommen aus einer monotonen, hochauflösenden Uhr, dem sogenannten Performance-Counter. Monoton heißt, sie kann nicht rückwärts springen wie die normale Systemuhr, und sie ist genau für Dauer-Messungen gedacht. Ergebnisse werden in Millisekunden gespeichert. Wo startet und stoppt die Uhr für die Zeit bis zum ersten Token beim Sprachmodell? Erinnerung an die Asymmetrie aus Modul acht: Beim Sprachmodell ist diese Zeit verbindungs-inklusiv. Im Code heißt das: Die Uhr wird kurz vor dem Absenden des Requests gestartet, also bevor die frische Verbindung steht, und beim ersten eintreffenden Antwort-Chunk gestoppt. Die Differenz ist die Zeit bis zum ersten Token. Genau deshalb steckt der Verbindungsaufbau mit drin.


Cold-Start im Code.

Modul fünf als Code: Für jeden einzelnen Call wird ein frischer Client beziehungsweise eine frische Verbindung erzeugt und danach geschlossen. Kein Wiederverwenden. Warum frischer Client je Call? Nur so misst jeder Call einen echten Cold-Start inklusive TCP- und TLS-Handshake. Würde der Code ein Client-Objekt wiederverwenden, hielte die Bibliothek die Verbindung offen, und ab dem zweiten Call fiele der Verbindungsaufbau weg. Genau der Teil, den du messen willst. Der frische Client im Code ist also die technische Garantie für das Cold-Start-Prinzip.


Der IPv4-Zwang.

Ein unscheinbares, aber wichtiges Detail: Der Code erzwingt die Adressfamilie IPv4. Warum? Mehrere Hosts, die hinter Cloudflare, haben sowohl eine IPv4- als auch eine IPv6-Adresse, das nennt man Dual-Stack. Layer eins misst über die klassische Auflösung ohnehin IPv4. Würde Layer drei unkontrolliert IPv6 wählen, was im allerersten Echtlauf tatsächlich passierte, dann misst Layer eins eine IPv4-Adresse und Layer drei eine ganz andere IPv6-Adresse, und die Brücke zwischen den Schichten sowie die Edge-gegen-Host-Klassifikation verglichen plötzlich zwei verschiedene Adressfamilien. Der Zwang auf IPv4 sorgt dafür, dass alle Schichten dieselbe Adresse sehen.


Der Orchestrator.

Hier wird die Kampagne aus Modul fünf technisch umgesetzt. Erstens, ein Datei-Lock, das verhindert, dass sich zwei Slots überlappen, falls ein Slot überzieht. Zweitens, das verschränkte Round-Robin mit Rotation: Statt hundertmal Anbieter A und dann hundertmal Anbieter B geht jede Runde einmal durch alle neun Endpunkte, und die Startreihenfolge rotiert pro Runde. Was verhindert das Rotieren? Ohne Rotation stünde derselbe Anbieter immer an derselben Position jeder Runde, zum Beispiel einer immer direkt nach der Wartezeit zuerst und ein anderer immer zuletzt. Das gäbe jedem Anbieter eine feste relative Position mit eventuell systematischem Vor- oder Nachteil. Die Rotation verteilt die Positionen gleichmäßig, sodass kein Anbieter dauerhaft auf einem guten oder schlechten Platz sitzt. Drittens, ein harter Zeit-Backstop pro Call von fünfundsiebzig Sekunden in einem eigenen Thread, falls ein Call total hängt, damit er den Slot nicht einfrieren kann. Viertens, eine saubere Ausgabedatei pro Slot: erste Zeile sind die Lauf-Metadaten, dann ein Datensatz pro Call, letzte Zeile ein Abschluss-Marker, und der Prozess schreibt auch bei einem Abbruch-Signal sauber zu Ende.


Erfolg ist inhaltsbasiert, nicht Verbindung stand.

Ein Call gilt nicht schon dann als Erfolg, wenn die Verbindung stand, sondern nur, wenn inhaltlich gültiger Output kam. Beim Sprachmodell mindestens ein Wort und mindestens drei Antwort-Chunks, beim Text-to-Speech mindestens tausend Bytes Audio, bei Speech-to-Text ein nicht-leeres Final-Transkript. Warum inhaltsbasiert? Sonst würde eine quasi-leere Antwort fälschlich als schnell zählen. Ein Anbieter, der sofort eine leere oder entartete Antwort zurückgibt, hätte eine super Zeit bis zum ersten Token, aber nichts geliefert. Inhaltliche Erfolgskriterien fangen das ab. In einem alten Lauf hatte Mistral rund zweiundsiebzig quasi-leere Erfolge. Und die Fehler werden als roher Text gespeichert, nicht als vorab fest kategorisiertes Schema. Die Einordnung in Timeout, Server-Fehler und so weiter passiert erst in der Auswertung. Wichtig dabei: nicht naiv auf das Wort Timeout filtern, denn die echten Timeouts stehen als längerer Fehlertext da.

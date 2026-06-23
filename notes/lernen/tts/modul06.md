Modul sechs. Layer eins. Infrastruktur, Edge gegen Host.

Worum es geht.

Dieser Block beantwortet den schärfsten Einwand, den Professor Wählisch bisher gestellt hat. Der Einwand lautet sinngemäß: Drei eurer Anbieter zeigen aus Frankfurt eine Round-Trip-Zeit von nur rund einer Millisekunde, und das habt ihr nicht erklärt. Genau darauf gibt Layer eins die Antwort. Layer eins ist die unterste der drei Mess-Schichten und misst die reine Netzwerk-Nähe zum Host, also wie weit die Maschine entfernt ist, mit der wir tatsächlich reden. Am Ende dieses Moduls kannst du erklären, warum drei Anbieter rund eine Millisekunde zeigen, ohne dass das ein Messfehler ist, und du kannst sauber trennen, was eine Edge ist und was ein gewöhnlicher Host.

Zuerst die Begriffe, die du in eigenen Worten beherrschen musst.

Die Round-Trip-Zeit, kurz die Zeit für Hin und Zurück, ist die Dauer, die ein kleines Datenpaket braucht, um zum Ziel und wieder zurück zu kommen. Sie ist das direkte Maß für die Netz-Distanz. Nah heißt kleine Round-Trip-Zeit, weit weg heißt große Round-Trip-Zeit.

Das Internet-Control-Message-Protokoll, abgekürzt I-C-M-P, ist das klassische Protokoll hinter dem gewöhnlichen ping-Befehl. Es ist eine Art Kontroll- und Diagnose-Sprache des Internets. Viele Anbieter und viele Inhalts-Liefer-Netzwerke beantworten dieses Protokoll aber gar nicht, sie blocken es. Darauf kommen wir gleich zurück, denn das ist der Grund, warum wir es nicht als Hauptmessung nehmen.

Der T-C-P-Handshake ist der Verbindungs-Aufbau einer normalen Internet-Verbindung. Er läuft in drei Schritten. Der Client schickt ein sogenanntes Synchronisations-Paket, der Server antwortet mit einer Synchronisations-Bestätigung, und der Client bestätigt seinerseits mit einer Bestätigung. Für die Messung interessiert uns nur der erste Hin-und-Zurück-Schritt, also Synchronisation raus und Synchronisations-Bestätigung zurück. Das ist genau eine Round-Trip-Zeit.

Die A-S-N, die Autonomous-System-Number, ist die eindeutige Kennung eines Betreiber-Netzes. Jedes große Netz im Internet hat so eine Nummer. Die Nummer dreizehntausenddreihundertfünfunddreißig gehört Cloudflare. Die Nummer achttausendfünfundsiebzig gehört Microsoft. Gehört eine Ziel-Adresse zu einer bestimmten Nummer, dann weiß man belegt, zu wessen Netz sie gehört.

Ein Content-Delivery-Network, kurz C-D-N, ist ein Inhalts-Liefer-Netzwerk. Es betreibt viele kleine Knoten verteilt über die ganze Welt. So ein Knoten nahe am Nutzer heißt Edge, also Randknoten. Die Edge terminiert die Verbindung in der Nähe des Nutzers, statt am weit entfernten Ursprungs-Server. Man redet dann physisch mit einer Maschine, die nur rund eine Millisekunde entfernt steht. Cloudflare ist so ein Inhalts-Liefer-Netzwerk.

Traceroute, auf Deutsch Routenverfolgung, ist ein Werkzeug, das den Weg eines Pakets Schritt für Schritt sichtbar macht. Es zeigt jeden Zwischenstopp, jeden sogenannten Hop, auf dem Pfad zum Ziel. So sieht man, in welchem Netz die Reise endet.

Der D-N-S-Resolver ist der Namens-Auflöser. Das Domain-Name-System, kurz D-N-S, ist das Telefonbuch des Internets. Es übersetzt einen Namen wie api Punkt openai Punkt com in eine numerische Adresse. Ein Resolver ist ein Server, der diese Übersetzung für dich erledigt. Bekannte öffentliche Resolver sind der von Google unter acht Punkt acht Punkt acht Punkt acht, der von Cloudflare unter eins Punkt eins Punkt eins Punkt eins und Quad-Neun unter neun Punkt neun Punkt neun Punkt neun.

Die T-T-L, die Time-to-live, ist die Lebenszeit eines Eintrags im Namens-System. Sie sagt in Sekunden, wie lange eine Antwort gültig bleibt, bevor neu gefragt werden muss. Eine kurze Lebenszeit erlaubt dem Anbieter, häufig zwischen verschiedenen Adressen zu wechseln.

Anycast bedeutet, dass dieselbe Adresse an vielen Orten der Welt gleichzeitig existiert und das Netz dich automatisch zum nächstgelegenen Standort leitet. Das ist der Trick, mit dem ein Inhalts-Liefer-Netzwerk dieselbe Adresse überall nah erscheinen lässt.

Round-Robin schließlich heißt Reihum-Verteilung. Hinter einem Namen stehen mehrere Adressen, und das Namens-System gibt mal die eine, mal die andere zurück. So verteilt ein Anbieter die Last über mehrere Rechenzentren.

Die Primärmetrik. Warum T-C-P-Ping und nicht das klassische ping.

Wir messen die Round-Trip-Zeit per T-C-P-Handshake auf Port vierhundertdreiundvierzig, nicht per dem klassischen ping über das Kontroll-Protokoll. Der Hauptgrund ist Vergleichbarkeit. Eine faire Tabelle über alle neun Endpunkte braucht eine einzige Messgröße. Das klassische ping wird aber von mehreren unserer Endpunkte geblockt, nicht alle neun antworten darauf. Würden wir für die einen das klassische ping und für die anderen den T-C-P-Handshake mischen, verglichen wir zwei verschiedene Größen, und das wäre angreifbar. Der T-C-P-Handshake dagegen funktioniert bei allen neun, weil jeder API-Endpunkt per Definition T-C-P auf Port vierhundertdreiundvierzig annehmen muss, sonst käme gar keine Verbindung zustande.

Der zweite Grund: Der T-C-P-Handshake trifft genau den Port, über den auch die echte Messung läuft, nämlich Port vierhundertdreiundvierzig, die verschlüsselte Verbindung. Das klassische ping liefe über einen Nebenkanal, den manche Anbieter ganz anders behandeln. Der dritte Grund ist Konsistenz mit Layer drei. Der T-C-P-Handshake misst genau einen Hin-und-Zurück-Schritt, also eine Round-Trip-Zeit, und das ist exakt dieselbe Größe, in die sich der Verbindungs-Aufbau in Layer drei zerlegt. Layer eins und Layer drei sprechen damit dieselbe Sprache.

Das klassische ping über das Kontroll-Protokoll läuft trotzdem zusätzlich mit, aber nur zur Quer-Validierung. Bei den Endpunkten, wo beide Methoden funktionieren, zeigen wir, dass der T-C-P-Handshake und das klassische ping ungefähr denselben Wert liefern. Damit ist belegt, dass der T-C-P-Handshake ein gültiger Stellvertreter für die Round-Trip-Zeit ist und für die Verweigerer guten Gewissens als alleinige Quelle dienen darf. Das ist eine Selbst-Validierung der Methode, kein blinder Fleck.

Wie genau gemessen wird, steht im Code. Wir lösen den Namen einmal vorab auf und verbinden danach direkt zur Adresse, sonst würde die Namens-Auflösungs-Zeit fälschlich in die Round-Trip-Zeit hineinrutschen. Dann pingen wir zwanzig Mal pro Ziel und werten das Minimum und den Median aus. Das Minimum ist der beste Schätzer der reinen Pfad-Latenz, weil es am wenigsten durch kurzzeitigen Stau verfälscht ist. Den Median speichern wir zusätzlich, denn er enthält das normale Warteschlangen-Verhalten.

Die Edge-Klassifikation. Drei Kriterien, alle drei müssen zutreffen.

Jetzt kommt der zentrale Erklärschritt. Ein Endpunkt zählt nur dann als Edge, wenn alle drei Kriterien gleichzeitig erfüllt sind. Es ist eine Und-Verknüpfung, kein Oder. Trifft auch nur eines nicht zu, ist es ein Host.

Das erste Kriterium: Die Round-Trip-Zeit aus Frankfurt liegt bei rund einer bis zwei Millisekunden, also im einstelligen Millisekunden-Bereich. Das zweite Kriterium: Die aufgelöste Ziel-Adresse gehört zu einer Inhalts-Liefer-Netzwerk-Nummer, konkret zu der Cloudflare-Nummer dreizehntausenddreihundertfünfunddreißig. Das dritte Kriterium: Die Routenverfolgung endet in genau diesem Inhalts-Liefer-Netz, der letzte antwortende Stopp liegt bei rund einer Millisekunde in eben dieser Nummer. Per Adresse bestätigt sind bisher das erste und zweite Kriterium über den Verbindungs-Aufbau-Timer und die Netz-Nummer; die T-C-P-Variante der Routenverfolgung über Port vierhundertdreiundvierzig ist spezifiziert, aber noch offen, weil sie root-Rechte braucht. Mit anderen Worten, der Randknoten ist selbst der Endpunkt, es gibt keinen Durchstich zu einem weit entfernten Backend.

Warum brauchen wir alle drei? Weil jedes einzelne Kriterium für sich täuschen kann. Eine niedrige Round-Trip-Zeit allein heißt noch nicht Edge, das sehen wir gleich bei Azure. Eine Adresse in einer bestimmten Nummer allein heißt noch nicht, dass die Verbindung dort wirklich terminiert. Und ein Marketing-Label wie Anycast heißt schon gar nichts. Erst die Konjunktion aller drei macht den Befund wasserdicht.

Die drei Round-Trip-Klassen aus dem maßgeblichen Lauf.

Maßgeblich ist allein der Lauf auf der Mess-Instanz in Frankfurt, eine einmalige Momentaufnahme vom sechzehnten Juni. Aus diesem Lauf fallen drei saubere Klassen.

Die erste Klasse ist die Edge-Klasse mit rund einer Millisekunde. Dazu gehören OpenAI, Groq und Mistral bei den Sprachmodellen, sowie OpenAI bei der Sprachausgabe. Alle vier terminieren bei Cloudflare in Frankfurt, alle unter der Nummer dreizehntausenddreihundertfünfunddreißig.

Die zweite Klasse ist das europäische Rechenzentrum mit rund elf Millisekunden. Das ist Azure, unter der Microsoft-Nummer achttausendfünfundsiebzig, im Standort Italy North. Das ist ausdrücklich kein Inhalts-Liefer-Netzwerk, sondern ein normales Rechenzentrum.

Die dritte Klasse ist das US-Backend mit rund hundertvierzig Millisekunden. Dazu gehört Deepgram, das auf zwei US-Netze auflöst, nämlich Zayo unter der Nummer sechstausendvierhunderteinundsechzig, dreimal, plus Cogent unter der Nummer hundertvierundsiebzig, ebenfalls dreimal. Und dazu gehört Rev Punkt ai, das auf das Amazon-Netz unter der Nummer sechzehntausendfünfhundertneun auflöst, dreimal.

Die Kernpointe. Warum Azure trotz elf Millisekunden ein Host ist.

Das ist die Frage, an der sich entscheidet, ob du das Modul wirklich verstanden hast. Azure hat eine niedrige Round-Trip-Zeit von rund elf Millisekunden, und trotzdem klassifizieren wir es als Host, nicht als Edge. Warum? Weil eine niedrige Round-Trip-Zeit allein eben nicht ausreicht. Azure scheitert am zweiten Kriterium. Seine Adresse gehört zur Microsoft-Nummer achttausendfünfundsiebzig, und das ist kein Inhalts-Liefer-Netzwerk, sondern ein ganz normales Rechenzentrum im Standort Italy North. Azure ist einfach geografisch nah, weil es ein echtes europäisches Rechenzentrum ist. Niedrige Distanz, aber keine Randknoten-Terminierung, also Host.

Und das ist sogar wichtig für die Glaubwürdigkeit der gesamten Arbeit. Azures niedrige Zahl ist ein realer Backend-Standort, kein Randknoten-Artefakt. Damit ist Azures Vorsprung bei der Sprachausgabe ein echter Standort-Vorteil und keine Täuschung durch eine vorgeschobene Edge. Dieser Standort-Vorsprung gilt allerdings sauber nur gegenüber Deepgram, dem echten US-Transit; OpenAI bei der Sprachausgabe sitzt selbst am Cloudflare-Frankfurt-Edge.

Jetzt der umgekehrte Fall, ebenso lehrreich. Deepgram trägt historisch ein Anycast-Label, bewirbt sich also selbst als überall-nah. Gemessen zeigt Deepgram aber rund hundertvierzig Millisekunden. Es scheitert damit schon am ersten Kriterium, die Round-Trip-Zeit ist viel zu hoch. Also ist Deepgram ein Host, ein Multi-Rechenzentrums-Anbieter mit Reihum-Verteilung, trotz des Anycast-Labels. Daraus folgt der Leitsatz dieses Moduls: Messung schlägt Marketing. Wir glauben nicht dem Werbe-Begriff, wir glauben der gemessenen Zahl plus der Netz-Nummer plus der Route.

Die D-N-S-Dimension. Wie man Reihum-Verteilung und Anycast erkennt.

Layer eins hat vier Säulen, und die erste ist die Namens-Auflösung. Hier ist der Trick: Wir lösen jeden Host nicht über einen, sondern über drei unabhängige Resolver auf. Den von Google unter acht Punkt acht Punkt acht Punkt acht, den von Cloudflare unter eins Punkt eins Punkt eins Punkt eins und Quad-Neun unter neun Punkt neun Punkt neun Punkt neun. Zusätzlich lesen wir die Lebenszeit des Eintrags aus, also die Time-to-live, und optional das DNSSEC-Echtheits-Flag.

So erkennt man Reihum-Verteilung und Anycast. Liefern die verschiedenen Resolver mehrere oder wechselnde Adressen, dann ist es Reihum-Verteilung. Deepgram zum Beispiel löst auf sechs verschiedene Adressen über zwei Netze auf. Das ist der direkte Beleg für einen Multi-Rechenzentrums-Betrieb. Eine kurze Lebenszeit verstärkt das Bild, weil sie dem Anbieter erlaubt, sehr häufig zwischen Adressen umzuschalten. Genau das ist die Antwort auf die Prüfer-Frage, wie ihr Reihum-Verteilung und Anycast erkannt habt und mit welchen Resolvern. Antwort: über den Mehr-Resolver-Vergleich aus drei unabhängigen Quellen plus die Lebenszeit.

Die Datensatz-Hygiene. Warum nur die Mess-Instanz zählt.

Es gibt zwei Stolpersteine, die du kennen musst, im Audit als H-Vier und A-Eins geführt. Erstens enthält das Daten-Verzeichnis für Layer eins zusätzlich einen Entwickler-Lauf, der auf einem macOS-Rechner entstanden ist. Dort liegt die Round-Trip-Zeit bei rund siebzehn bis einundzwanzig Millisekunden. Dieser Lauf darf nicht in die Auswertung, weil ihm der Vantage-Stempel fehlt, also der Nachweis, von welchem Standort aus gemessen wurde. Maßgeblich ist allein der Lauf auf der Mess-Instanz in Frankfurt. Den macOS-Lauf erkennt man nur an der Größenordnung der Round-Trip-Zeit, deshalb muss man hier besonders aufpassen.

Zweitens das Thema Transport-Verschlüsselung. Das Python auf dem macOS-Rechner ist gegen eine Bibliothek namens LibreSSL gebunden, die die Aushandlung auf die Transport-Verschlüsselung in Version eins Punkt zwei deckelt und alle Hosts fälschlich als Version eins Punkt zwei meldet. Deshalb dürfen auch die Verschlüsselungs-Zahlen nur von der Mess-Instanz stammen, die mit echtem OpenSSL in Version drei läuft. Pro Messung wird die OpenSSL-Version mitgeloggt, damit man die LibreSSL-Zeilen sofort verwerfen kann.

Zum Schluss der wichtige Vorbehalt zu allen Zahlen. Alle Kampagnen-Zahlen sind A-vier-Mediane über sechsundfünfzig von sechsundfünfzig Slots, also die abgeschlossene Vollkampagne, nur erfolgreiche Calls. Die maßgebliche Infrastruktur-Momentaufnahme stammt vom sechzehnten Juni; die Edge-gegen-Host-Klassifikation je Adresse ist zusätzlich über den Verbindungs-Aufbau-Timer aus Layer drei über sechsundfünfzig von sechsundfünfzig Slots bestätigt. Die Konfidenzintervalle stehen noch aus, die Werte selbst sind final und die Ordnung ist stabil. Die Klassifikation selbst, also Edge gegen Host, ändert sich dadurch aber nicht, denn sie ruht auf den Netz-Nummern und den Größenordnungen, nicht auf der letzten Nachkomma-Stelle.

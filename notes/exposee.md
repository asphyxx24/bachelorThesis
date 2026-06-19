# Exposé zur Bachelorarbeit

**Bachelorarbeit (B.Sc. Informatik, TU Dresden)**
**Autor:** Anton Rusik · Matrikelnummer 4847595
**Erstprüfer:** Prof. Dr. Matthias Wählisch
**Arbeitstitel (Arbeitsstand, noch nicht final entschieden):** Erklärt Netznähe die Latenzunterschiede? Eine drei-schichtige Messstudie zu Cloud-AI-Sprachdiensten (STT, LLM, TTS) aus EU-Sicht

## Motivation & Forschungsfrage

Echtzeit-Sprachassistenten verketten kommerzielle Cloud-Dienste für Spracherkennung (STT), Sprachmodelle (LLM) und Sprachsynthese (TTS) sequenziell. Die Antwortlatenz entscheidet über die Nutzbarkeit, doch ihre Ursachen, also Netzweg gegenüber Backend-Verarbeitung, werden kaum getrennt gemessen. Öffentliche Latenz-Benchmarks solcher Dienste vermischen beide Anteile typischerweise, während die hier verwendete paket-validierte Schichtentrennung sie überhaupt erst getrennt messbar macht. Die Arbeit liefert eine empirische Latenz- und Verfügbarkeits-Charakterisierung dieses kommerziellen LLM-/AI-Servings, deren schärfsten Befund die LLM-Stufe liefert.

**Leitfrage**

> In welchem Maße erklären **Netzwerk- und Infrastruktureigenschaften** (RTT, Protokoll, Hosting-Region), verglichen mit der **Backend-Verarbeitung** der Anbieter, die Latenzunterschiede zwischen kommerziellen Cloud-AI-APIs aus EU-Perspektive, und wie sich daraus die sequenzielle Cold-Start-Gesamtlatenz der Voice-Pipeline ergibt?

Die Frage ist bewusst offen, denn auch der Befund, dass das Netzwerk *weniger* erklärt als das Backend, wäre ein ebenso tragfähiges Ergebnis. Neben der Latenz wird die Verfügbarkeit (Fehlerrate) je Endpunkt als eigene Achse erhoben.

## Methodik

Gemessen wird von einem festen Vantage Point (AWS EC2, Frankfurt) gegen neun Endpunkte, also je drei Anbieter pro Stufe: STT (Deepgram, Rev.ai, Azure), LLM (OpenAI, Groq, Mistral) und TTS (Deepgram, OpenAI, Azure). Drei sauber getrennte Messschichten:

- **Layer 1 (Infrastruktur):** DNS, RTT (TCP/ICMP), TLS, Traceroute, ASN → Netznähe zum Host.
- **Layer 2 (Paketebene):** Verkehrsaufzeichnung (tcpdump/PCAP) zur **paketbasierten Validierung des Connect-Timers**. Der in der Anwendung gemessene Wert stimmt mit dem aus den Paketen abgeleiteten auf ~0,1 ms überein. (Die Antwortlatenzen `ttft`/`ttfa` nutzen denselben Messmechanismus, sind aber nicht direkt paket-geeicht.)
- **Layer 3 (API-Latenz):** Cold-Start-Messung, also jede Anfrage über eine frische Verbindung ohne Connection-Pooling, da aus EU-Sicht gerade der Verbindungsaufbau zum Backend der interessante Anteil ist. Erfasst werden atomare Submetriken (TCP-/TLS-/WebSocket-Handshake) sowie Time-to-first-Token/-Audio.

Zielumfang: 7-Tage-Kampagne, 8 Zeitslots pro Tag, n=100 je Endpunkt und Slot, interleaved, insgesamt rund 50.000 Einzelmessungen. Vorläufig ausgewertet werden die bislang erhobenen Slots robust mit Bootstrap-Konfidenzintervallen, wobei die Aggregation (Median der Slot-Mediane gegenüber gepoolt) noch gegengeprüft wird. Die Latenz wird nur auf erfolgreichen Calls betrachtet, die Verfügbarkeit getrennt als eigene Achse ausgewiesen.

## Zentrales Ergebnis (Zwischenstand)

Die drei LLM-Anbieter terminieren **alle am selben Cloudflare-Edge in Frankfurt**: je Anbieter beide DNS-rotierten Edge-IPs als AS13335 bei ~1 ms TCP-RTT gemessen und per ASN-Lookup bestätigt (100 % des LLM-Traffics). Trotz nahezu identischer Netzanbindung streut die Antwortlatenz um **rund das Sechseinhalbfache (~6,5×)**, wobei die geografische Ordnung sogar invertiert ist: Ein EU-gehosteter Dienst ist langsamer als ein US-Dienst.

Die belastbare Aussage ist daher negativ: **Die Netznähe erklärt die Spreizung nicht.** Die Differenz liegt also nicht in der EU-Edge-Nähe, sondern im Backend und Serving, etwa in der Inferenz-Hardware (zum Beispiel Groqs LPU gegenüber GPU-Serving), der Modellgröße und dem Serving-Stack. Diese positive Lesart trägt einen unvermeidbaren Modellgrößen-Confound, denn das schnellste Modell ist zugleich das kleinste auf Spezialhardware, und wird transparent diskutiert. Die negative Kernaussage bleibt davon unberührt, da bereits die invertierte Geografie-Ordnung Netznähe als Erklärung ausschließt. Der Befund ist zudem vom einzelnen Vantage Point unabhängig, weil er bei *konstanter* Netzdistanz (gleicher Edge, ~1 ms für alle drei LLM) auftritt.

## Beitrag, Abgrenzung, Stand

- **Kernbefund:** empirischer Nachweis, dass Netznähe die Latenzspreizung nicht erklärt, am stärksten an LLMs mit identischem Edge. STT trägt zur Engine-These bewusst nicht bei, da es auf der fairen Metrik Engine und Geografie nicht scharf trennt, und dient als methodischer Kontrast- und Verfügbarkeitsfall.
- **Methodischer Beitrag:** eine reproduzierbare, mehrfach auditierte Drei-Schichten-Methodik samt paket-validierter Edge-Grenze für Performance-Aussagen über kommerzielle Blackbox-AI-Dienste.
- **Methoden-Baustein:** eine ping-basierte Heuristik zur Klassifikation der Connect-Zusammensetzung. Aus den Phasen wird die sequenzielle Cold-Start-Gesamtlatenz der Pipeline zusammengesetzt.
- **Out of Scope:** Transkriptions- und Ausgabequalität (gemessen werden nur Latenz und Verfügbarkeit) sowie der einzelne Vantage Point (Frankfurt). Die RTT- und Edge-Zahlen sind FRA-spezifisch, der Backend-Kernbefund ist davon unberührt.
- **Stand:** Die Messinfrastruktur steht und ist mehrfach auditiert. Die Kampagne läuft noch, danach folgen Auswertung, Statistik und schriftliche Ausarbeitung (geplante Fertigstellung voraussichtlich im August 2026).

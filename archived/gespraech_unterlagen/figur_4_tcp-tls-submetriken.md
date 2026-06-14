# Figur 4 — connect_ms-Zerlegung: TCP/TLS-Submetriken aus dem PCAP

![](02_submetrics_stacked.png)

## Worum es geht

Die Figur zerlegt die Verbindungsaufbauphase (`connect_ms`) jedes Providers in unabhängig aus dem Paket-Mitschnitt (PCAP) gemessene Submetriken — TCP-Handshake, TLS-Handshake, Zeit bis zum ersten Applikations-Datenpaket. Sie ist der methodische Einstieg: Sie zeigt, dass `connect_ms` kein Black-Box-Wert ist, sondern aus zählbaren Round-Trips (RTTs) besteht, und dass der dritte Balken bei Azure keine Server-Verarbeitung, sondern eine client-seitige Sendelücke enthält.

## Was auf der Figur zu sehen ist

- **Diagrammtyp:** gestapeltes Balkendiagramm (stacked bar), ein Balken pro Provider-Endpunkt.
- **X-Achse:** die neun gemessenen Endpunkte, beschriftet `azure_stt`, `deepgram_tts`, `deepgram_stt`, `openai_llm`, `azure_tts`, `mistral_llm`, `groq_llm`, `openai_tts`, `revai_stt`. Die Balken sind absteigend nach Gesamthöhe sortiert.
- **Y-Achse:** „Zeit [ms]", lineare Skala (keine Log-Skala), von 0 bis gut 620 ms.
- **Drei Segmente je Balken (Legende „Phase"):**
  - **Blau — „TCP-Handshake (1 RTT)":** Zeit von TCP SYN bis SYN-ACK, also ein Round-Trip.
  - **Orange — „TLS-Handshake (1 RTT)":** Zeit vom TLS ClientHello bis ServerHello, ebenfalls ein Round-Trip (bei TLS 1.3; Rev.ai nutzt TLS 1.2, siehe unten).
  - **Grün — „bis 1. App-Daten (inkl. Sendelücke)":** Zeit vom Ende des TLS-Handshakes bis zum ersten Applikations-Datenpaket; dieses Segment enthält Protokoll-Setup (z. B. WebSocket-Upgrade) und — bei Azure — die client-seitige Sendelücke.
- **Annotationen:** über jedem Balken steht die Gesamthöhe in ms (445, 621, 477, 169, 97, 73, 55, 54, 285).
- **Hinweistext oben rechts:** „n = 1 Capture (Single-Slot 2026-06-08)" — die Werte stammen aus genau einem Mitschnitt pro Provider.
- **Untertitel:** stellt die Kernaussage voran — TCP und TLS je ~1 RTT, und bei Azure ist der grüne Block (414 von 446 ms) überwiegend eine client-seitige Sendelücke, kein Server-Processing (Verweis auf §7.4).
- **`revai_stt`:** zeigt nur blau und orange (TCP + TLS), kein grünes Segment — für Rev.ai wurde der App-Daten-Zeitpunkt im PCAP nicht erfasst (Felder `proto_setup_ms`/`app_data_start_ms` leer).

## Die Messwerte (mit Zahlen)

Quelle: `analysis/tables/02_pcap_communication_profile.csv`, Spalten `tcp_hs_ms`, `tls_hs_ms`, `proto_setup_ms`, `app_data_start_ms`. n = 1 Capture/Provider.

| Endpunkt | RTT | TCP-HS | TLS-HS | bis 1. App-Daten (grün) | Balkenhöhe |
|---|---|---|---|---|---|
| deepgram_tts | 138 | 142,9 | 145,0 | 333,4 | 622 |
| deepgram_stt | 138 | 148,4 | 150,2 | 178,6 | 478 |
| azure_stt | 10 | 18,5 | 12,7 | 414,0 | 446 |
| revai_stt (TLS 1.2) | 144 | 142,7 | 142,8 | — | 285 |
| openai_llm | 1 | 0,9 | 3,1 | 164,8 | 169 |
| azure_tts | 10 | 11,9 | 12,4 | 72,7 | 98 |
| mistral_llm | 1 | 1,0 | 6,5 | 65,6 | 73 |
| groq_llm | 1 | 1,3 | 3,3 | 50,7 | 55 |
| openai_tts | 1 | 1,6 | 3,2 | 49,6 | 54 |

Kernpunkte:
- **TCP und TLS sind je ~1 RTT.** Deepgram (RTT 138): TCP 148, TLS 150 ms — beide ungefähr eine RTT. Azure (RTT 10): TCP 18, TLS 13 ms. Die Cloudflare-Endpunkte (RTT ~1): TCP <2 ms. Das ist das mechanistische Fundament der ganzen Figur.
- **Azure STT, der grüne Block:** Das Segment „bis 1. App-Daten" beträgt 414 ms, der erste App-Daten-Zeitpunkt liegt bei 446 ms — bei einer RTT von nur 10 ms. Das ist nicht durch Netzwerk oder Handshake erklärbar; es ist eine **client-seitige Sendelücke** (die App ist bereits bei `connect_ms` ≈ 49 ms sendebereit, sendet das Audio aber erst später). `app_data_start_ms` (446) ist daher ungleich `connect_ms` (49). Konkret: das letzte Setup-Paket liegt bei ~87 ms, das erste Audio bei ~446 ms — die isolierte reine Lücke ist also ~358 ms (§7.4).
- **Deepgram STT, der grüne Block (178 ms):** Hier ist die Pre-Audio-Zeit der dritte RTT — WebSocket-Upgrade + Session-Init —, KEINE Client-Lücke. Deepgrams ~3-RTT-Handshake (TCP 148 + TLS 150 + WS, je 1 RTT) deckt die Balkenhöhe ab.
- **Rev.ai:** TLS 1.2 (`ECDHE-RSA-AES128-GCM-SHA256`) statt 1.3 — der einzige Provider ohne 1-RTT-TLS; daraus entsteht im Kampagnen-Median der TLS-1.2-Penalty von ~153 ms.

## Was man daraus ableitet (der Befund / der Fortschritt)

Drei nicht-triviale Punkte:

1. **`connect_ms` ist mechanistisch zerlegbar.** Statt einer Black-Box zeigt das PCAP zählbare RTTs: TCP = 1 RTT, TLS = 1 RTT, Protokoll-Setup = 1 RTT. Das stützt das Cross-Layer-Modell `connect_ms ≈ N_RTTs × ping + k` (n = 4 direkte Provider, slope ~1) — hier aber unabhängig auf Paketebene, nicht aus Layer-3-Timing abgeleitet. Wichtig: `connect_ms` ist nur für die DIREKTEN Provider cross-Provider vergleichbar; bei den vier Cloudflare-Endpunkten misst es den Edge, nicht das Backend. Das r des Modells ist bewusst kein Gütemaß, sondern Methoden-Baustein.
2. **Azures grüner Block ist KEIN Server-Processing.** Das ist die didaktisch wichtigste Korrektur: Wer nur die Balkenhöhe (446 ms) sieht, würde fälschlich auf langsame Azure-Infrastruktur schließen. Die Paketanalyse zeigt, dass die App schon nach ~49 ms (3 RTTs bei 10-ms-RTT) sendebereit ist und die 414 ms grüner Block überwiegend client-seitige Wartezeit sind. Das trennt sauber, was zum Netzwerk/Connect gehört und was nicht.
3. **Beleg für die Forschungsfrage (Netzwerk vs. Backend-Verarbeitung):** Genau weil der Verbindungsaufbau hier vollständig auf Netzwerk-RTTs zurückführbar ist, lässt sich der spätere große Latenzunterschied bei STT (Deepgram-TTFT 575 vs. Azure-TTFT 1715 ms) NICHT mehr dem Connect zuschreiben — der Connect ist bei Azure sogar günstiger. Diese Figur räumt also die Netzwerk-/Connect-Erklärung als Hauptursache des STT-Unterschieds ab und verlagert die Last auf die nachgelagerte Backend-Verarbeitung. Sie liefert damit eine ANTEILS-Aussage, keine Kausalaussage: Region und Engine sind hier konfundiert (n = 1 EU-Provider je Kategorie).

## Rolle im Gespräch

Diese Figur ist der **Methodik-Einstieg** des Figurensets. Sie etabliert zwei Dinge, auf die alle späteren Aussagen aufbauen: (a) `connect_ms` besteht aus zählbaren RTTs (TCP/TLS je 1 RTT), und (b) die Balkenhöhe ist nicht naiv als „Server-Geschwindigkeit" lesbar — der dritte Balken kann eine Client-Sendelücke enthalten. Erst wenn das geklärt ist, ist die spätere Zerlegung der STT-TTFT in „Netz vs. Verarbeitung" (Azure: −375 ms Netz, +1140 ms Verarbeitung, netto +765 ms) glaubwürdig. Sie kommt vor den Befund-Figuren und immunisiert gegen die Fehlinterpretation „Azure ist langsam, weil weit weg vom Backend".

## Grenzen / ehrliche Caveats

- **n = 1 Capture pro Provider.** Es ist ein Single-Slot-Mitschnitt vom 2026-06-08, keine Verteilung. Die absoluten Werte können slot-/lastabhängig schwanken (besonders Deepgrams Anycast-RTT); die Figur belegt die Zerlegungs-Logik, nicht robuste Mediane.
- **Die Sendelücke ist methodisch, nicht provider-inhärent.** Azures 414/446 ms grüner Block hängt vom Mess-Client ab (wann er das Audio sendet); ein anderer Sende-Zeitpunkt änderte den Balken. Die Lücke charakterisiert die Messung, nicht Azures Server.
- **„bis 1. App-Daten" mischt zwei Dinge.** Bei Deepgram ist der grüne Block echtes Protokoll-Setup (WS-Upgrade, 1 RTT); bei Azure überwiegend Client-Warten. Das Segment hat also je nach Provider unterschiedliche Bedeutung — die Farbe allein trennt das nicht, der Untertitel und §7.4 müssen es erklären.
- **Cloudflare-Caveat:** Bei Groq/Mistral/OpenAI (ASN 13335) misst das PCAP den Cloudflare-Edge, nicht das Provider-Backend. Die niedrigen Balken (54–169 ms) sind Edge-Connect, kein Hinweis auf Backend-Nähe.
- **Rev.ai unvollständig:** kein grünes Segment (App-Daten-Zeitpunkt nicht erfasst), daher nur als TCP+TLS-Vergleichswert nutzbar.
- **`effektive_RTTs` in der CSV ist artefaktbehaftet:** Werte wie 43,4 oder 140,2 entstehen aus `app_data_start / rtt` und sind bei kleinen RTTs (Cloudflare) oder Sendelücken (Azure) irreführend — sie sind NICHT die echte Handshake-Tiefe (die ist 3 RTTs). Diese Spalte gehört nicht in die Argumentation.

## Wenn der Prof fragt

**„Wenn Azure schon nach 49 ms sendebereit ist — woher kommen die 446 ms bis zum ersten App-Daten-Paket?"**
Das ist eine client-seitige Sendelücke: Mein Mess-Client baut die Verbindung in ~3 RTTs (≈49 ms bei 10-ms-RTT) auf, schickt das Audio aber erst danach. Das letzte Setup-Paket liegt bei ~87 ms, das erste Audio bei ~446 ms — die Differenz (~358 ms) ist Wartezeit auf der Client-Seite, kein Server-Processing. `app_data_start_ms` (446) ist deshalb bewusst getrennt von `connect_ms` (49); für den fairen Provider-Vergleich nutze ich `connect_ms`. (Hinweis: Der grüne CSV-Block `proto_setup_ms` ist mit 414 ms etwas größer als die im §7.4 isolierte reine Lücke von ~358 ms, weil er das gesamte Intervall ab TLS-Ende fasst — beides beschreibt dieselbe Client-Wartezeit.)

**„Heißt das, die Engine erklärt die ganze STT-Latenz?"**
Nein — so weit trägt die Figur nicht. Die STT/TTS-Inversion falsifiziert die Hypothese, die Region erkläre die Latenz hinreichend; sie beweist nicht, dass die Engine alles erklärt. Es ist eine Anteils-, keine Kausalaussage: Mit nur einem EU-Provider je Kategorie sind Region und Backend konfundiert. Ich spreche deshalb bewusst von „Backend-Verarbeitung" statt kausal von „der Engine".

**„n = 1 — ist das nicht zu wenig, um daraus etwas zu schließen?"**
Für absolute Mediane ja, deshalb stützt sich der Latenzbefund auf die Kampagne mit 50.400 Messungen (0 % NaN). Diese Figur dient nur dem mechanistischen Nachweis der Zerlegung: dass TCP und TLS je genau 1 RTT sind und dass der dritte Balken bei Azure eine Client-Lücke ist. Diese strukturellen Aussagen sind aus einem sauberen Mitschnitt ablesbar und mit dem Kampagnen-`connect_ms`-Median (Azure ~49 ms) konsistent.

# Figur 1 — Drei RTT-Klassen: die naive Erwartung „nah = schnell"

![](01_ping_rtt_boxplot.png)

## Worum es geht

Die Figur zeigt die reine Netzwerk-Umlaufzeit (Round-Trip-Time, RTT) vom Vantage Point AWS Frankfurt zu allen sieben gemessenen API-Endpunkten. Sie etabliert die geografisch motivierte Intuition „je näher der Server, desto kleiner die Latenz" in Form von drei klar getrennten RTT-Klassen — genau die Erwartung, die die nachfolgenden Figuren auf der Applikationsschicht falsifizieren.

## Was auf der Figur zu sehen ist

- **Titel:** „Drei RTT-Klassen aus Frankfurt: Cloudflare-Edge ~1 ms, Azure EU ~10 ms, US-Hosting ~140 ms" — benennt die drei Klassen bereits.
- **X-Achse (`Endpoint`):** sieben kategoriale Endpunkte, von links nach rechts nach steigender RTT sortiert: `mistral.ai`, `openai.com`, `groq.com`, `azure-stt`, `azure-tts`, `deepgram.com`, `rev.ai`.
- **Y-Achse (`RTT [ms] (log-Skala)`):** die Umlaufzeit in Millisekunden, **logarithmisch** skaliert. Die Log-Skala ist hier zwingend: zwischen ~1 ms und ~140 ms liegen mehr als zwei Größenordnungen; auf linearer Skala wären die drei untersten Provider zu einem nicht unterscheidbaren Strich am Achsenboden zusammengedrückt. Gitterlinien bei 10⁰ (1 ms), 10¹ (10 ms) und 10² (100 ms).
- **Boxplots:** je ein Boxplot pro Endpunkt. Die Box umfasst das 25.–75.-Perzentil (Interquartilsabstand), der Strich in der Box ist der Median, die Whisker reichen bis zu den Extremwerten innerhalb des üblichen 1,5×IQR-Bereichs. Die Boxen sind durchweg flach — die RTT ist über die Messdauer hinweg stabil (Standardabweichung bei allen Endpunkten ≤ 4,4 ms, bei Deepgram 4,4 ms, bei Rev.ai 3,8 ms).
- **Legende „Mess-Quelle":** zwei Einträge. **ICMP (Kampagne)** — die regulären Ping-Messungen, mit denen sechs der sieben Endpunkte erfasst sind. **TCP-SYN (Rev.ai, ICMP geblockt)** — für `rev.ai` ist ICMP-Echo serverseitig gesperrt, daher wird die RTT dort ersatzweise aus dem TCP-SYN→SYN-ACK-Zeitabstand gewonnen. Das ist methodisch tragfähig, weil das SYN/SYN-ACK-Paar denselben einen Netzwerk-Hin-und-Rückweg durchläuft wie ein ICMP-Echo.
- **Drei gepunktete horizontale Referenzlinien** mit Beschriftung: „Cloudflare-Edge ~1 ms", „Azure EU ~10 ms", „US-Hosting ~140 ms". Sie markieren die drei Klassen; jeder Endpunkt sitzt auf genau einer dieser Linien.

Man erkennt drei getrennte Höhenbänder: die ersten drei Provider clustern auf ~1 ms, die beiden Azure-Endpunkte auf ~10 ms, Deepgram und Rev.ai auf ~140 ms. Dazwischen liegt jeweils eine ganze Größenordnung ohne Zwischenwerte.

## Die Messwerte (mit Zahlen)

Quelle: `data/layer1_extra/ping_tcp.csv` (ICMP-Mediane, n=70 pro Endpunkt, 0/70 fehlerhaft) und `analysis/tables/01_infrastructure_profile.csv` (Spalte `rtt_icmp_median_ms`; Rev.ai über `rtt_tcp_median_ms`, da ICMP geblockt).

**Klasse 1 — Cloudflare-Edge (~1 ms):**
- mistral.ai: 1,0 ms (Profil-Tabelle; ICMP-Median in ping_tcp.csv 1,988 ms)
- openai.com: 1,2 ms (ICMP-Median 2,298 ms)
- groq.com: 1,4 ms (ICMP-Median 1,780 ms)

**Klasse 2 — Azure Italy North (~10 ms):**
- azure-stt: 10,3 ms (ICMP-Median 12,532 ms)
- azure-tts: 10,4 ms (ICMP-Median 16,401 ms)

**Klasse 3 — US-Hosting (~140 ms):**
- deepgram.com: 137,8 ms (ICMP-Median 133,972 ms; Standardabweichung 4,4 ms)
- rev.ai: 144,2 ms (nur TCP-SYN, da ICMP geblockt; TCP-Median 144,239 ms, Standardabweichung 3,8 ms)

Die drei Klassen unterscheiden sich um jeweils etwa eine Größenordnung: ~1 ms / ~10 ms / ~140 ms. Innerhalb jeder Klasse sind die Provider praktisch ununterscheidbar.

> Hinweis zur leichten Diskrepanz: Die Werte in der Profil-Tabelle (z. B. mistral 1,0) und in `ping_tcp.csv` (1,988) weichen geringfügig ab, weil die Tabelle aus einem anderen Mess-Subset/Slot aggregiert. Beide bestätigen dieselbe Klassen-Zuordnung; für das Argument zählt allein die Größenordnung.

## Was man daraus ableitet (der Befund / der Fortschritt)

Der Befund (F1 in `notes/findings.md`) ist die saubere Drei-Klassen-Struktur der reinen Netzwerk-RTT. Sie ist nicht trivial, weil sie zeigt, dass die Geografie auf der Netzwerkschicht **genau so wirkt, wie man es naiv erwartet**: Cloudflare-Edge in Frankfurt antwortet in ~1 ms, ein eigenständiger Server-Standort in Italien (Azure) in ~10 ms, ein US-Server in ~140 ms — konsistent mit der Signallaufzeit über transatlantische Glasfaser.

Damit ist die geografische Erwartung auf Layer 1 **bestätigt und quantifiziert**. Das ist der notwendige Aufbau: Die Forschungsfrage stellt Netzwerkeigenschaften der Backend-Verarbeitung gegenüber. Diese Figur fixiert die Netzwerk-Seite als saubere, vorhersagbare, geografie-getriebene Größe. Erst dadurch wird der spätere Bruch sichtbar — wenn nämlich der ~140-ms-US-Provider Deepgram die STT-Aufgabe mit einem niedrigeren TTFT abschließt (575 ms) als der ~10-ms-EU-Provider Azure (1715 ms).

Diese spätere Inversion **falsifiziert die Hypothese, die Region erkläre die Latenz hinreichend** — sie belegt nicht, dass die Backend-Verarbeitung „alles" erklärt. Es ist eine Anteils-, keine Kausalaussage: je Kategorie steht nur ein EU-Provider zur Verfügung, Region und Backend-Engine sind konfundiert. Ohne die hier etablierte Netzwerk-Ordnung wäre der spätere Bruch jedoch nicht als überraschend erkennbar. Ein methodischer Hinweis zur Vergleichbarkeit über die Schichten hinweg: Beim STT-Cold-Start ist der TTFT connect-**exklusiv** (gemessen ab dem ersten Audio-Chunk, also nach dem Verbindungsaufbau); der STT-Cold-Start ist damit `connect_ms + ttft_ms`. Die RTT dieser Figur ist die unterste Komponente dieses Verbindungsaufbaus.

## Rolle im Gespräch

Erste Figur, reiner Aufbau. Sie liefert die Intuition „nah = schnell", die das Publikum mitbringt, und belegt sie mit Daten — damit die folgenden Figuren (STT/TTS-Inversion, connect-Zerlegung) sie gezielt brechen können. Sie definiert außerdem die drei RTT-Klassen als Vokabular, auf das alle späteren Argumente zurückgreifen (z. B. „Deepgram ist netzwerkseitig Klasse 3, löst die STT-Aufgabe aber schneller als Klasse 2").

## Grenzen / ehrliche Caveats

- **Die Figur zeigt nur die Netzwerk-RTT, nicht die End-zu-End-Latenz.** Sie sagt bewusst nichts über connect_ms, Handshakes oder Backend-Verarbeitung aus — das ist gerade der Punkt: Sie ist die Netzwerk-Hälfte, die später der Verarbeitungs-Hälfte gegenübergestellt wird.
- **„Cloudflare-Edge" misst die Edge, nicht das Backend.** Die ~1 ms für groq/mistral/openai sind die RTT zum Cloudflare-Knoten in Frankfurt, hinter dem das eigentliche US-Backend liegt. Die Edge-RTT sagt nichts über die Entfernung zum tatsächlichen Rechen-Backend. Genau deshalb ist das spätere Cross-Layer-Modell nur für die direkten (nicht Cloudflare-fronted) Provider gültig und bricht bei diesen 4/9 Providern.
- **Rev.ai ist nicht ICMP-, sondern TCP-SYN-gemessen** (ICMP geblockt). Das erfasst dieselbe eine RTT, ist aber eine andere Mess-Quelle — daher der separate Legendeneintrag. Kein Vergleichsfehler, aber transparent zu nennen. Nicht zu verwechseln mit dem TLS-1.2-Penalty von Rev.ai (~153 ms, F2): Der betrifft den *Handshake*, nicht die hier gezeigte RTT.
- **Mediane, keine Tails.** Die Boxen sind eng, aber die Figur betont die zentrale Tendenz; seltene Routing-Ausreißer (besonders bei Deepgrams Anycast) sind hier nicht der Fokus.

## Wenn der Prof fragt

**„Warum Log-Skala — verzerrt das nicht?"**
Im Gegenteil, sie verhindert die Verzerrung. Bei linearer Skala über 1 bis 144 ms verschwänden die ~1-ms- und die ~10-ms-Klasse zu einem ununterscheidbaren Strich am Achsenboden; sichtbar blieben nur die US-Provider. Die Log-Skala macht alle drei Klassen gleichzeitig sichtbar und zeigt, dass sie sich um jeweils einen näherungsweise konstanten Faktor (~10×) unterscheiden — genau das ist die Aussage.

**„Warum ist Rev.ai per TCP-SYN gemessen und nicht per Ping — sind die Werte vergleichbar?"**
Rev.ai blockt ICMP-Echo serverseitig, daher liefert Ping keinen Wert. Das SYN/SYN-ACK-Paar durchläuft denselben einen Netzwerk-Hin-und-Rückweg und misst dieselbe physikalische RTT; der TLS-/Handshake-Mehraufwand bleibt außen vor. Mit 144,2 ms liegt Rev.ai sauber in derselben US-Klasse wie Deepgram (137,8 ms, per ICMP gemessen) — die Klassen-Zuordnung ist also robust gegenüber der Mess-Quelle.

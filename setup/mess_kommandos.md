# Mess-Kommandos (welcher Befehl misst was)

> Angelegt: 2026-06-14 · Teil des Neuaufbaus (s. `messprotokoll.md`)
>
> Diese Datei hält **spezifisch** fest, mit **welchem Werkzeug/Befehl** jede Messung erhoben wird —
> getrennt nach Schicht. Zweck: Reproduzierbarkeit und die „ich weiß genau, was ich messe"-Erklärung
> für den Prof.
>
> **Zwei Ebenen unterscheiden:**
> - **Werkzeug-Ebene** = die rohen CLI-Befehle (`ping`, `dig`, `curl`, `traceroute`, `tcpdump`,
>   `tshark`, Python-`socket`/`ssl`). Die sind **stabil** und unten exakt dokumentiert.
> - **Wrapper-Skript** = das Python-Skript, das den Befehl in Schleife ausführt + Ergebnis als JSONL
>   speichert. Diese werden im Neuaufbau **neu gebaut**; die Befehle darin bleiben die unten genannten.
>   *(Die alten Wrapper liegen als Referenz in `../archived/measurements/`.)*
> - **Platzhalter:** `<host>` = API-Host (s. `api_endpunkte.md`), `<url>` = volle URL,
>   `<iface>` = Netzwerk-Interface des Vantage Points.

---

## Layer 1 — Infrastruktur (aktives Messen)

### RTT primär: TCP-Ping (Port 443) — für alle 9
Python-`socket`, kein CLI-Tool (misst SYN→SYN-ACK = 1 RTT auf Port 443):
```python
ip = socket.gethostbyname(host)          # DNS EINMALIG vorab — nicht in die RTT mitmessen!
t0 = time.perf_counter()
sock = socket.create_connection((ip, 443), timeout=5.0)   # zur IP verbinden → reine SYN→SYN-ACK-Zeit
rtt_ms = (time.perf_counter() - t0) * 1000
```
→ liefert `tcp_handshake_ms` / `rtt_ms`. **Primäre RTT-Metrik** (s. Ping-Strategie im Protokoll).
> **Präzision:** Zur **IP** verbinden (nicht zum Hostnamen), sonst steckt die DNS-Auflösung in der RTT.
> Über N Wiederholungen den **Minimal-RTT** als Schätzer der Pfadlatenz nehmen (min ≈ unkongestioniert;
> Median enthält Queueing) — beides speichern.

### RTT sekundär: ICMP-Ping — nur wo nicht geblockt
```bash
ping -c <count> -W 2 <host>
```
→ klassische ICMP-RTT (min/avg/max). Dient als **Cross-Check** gegen den TCP-Ping.

### DNS-Auflösung (Multi-Resolver-Vergleich)
```bash
dig @8.8.8.8 <host> A +short +time=3 +tries=1     # Google
dig @1.1.1.1 <host> A +short +time=3 +tries=1     # Cloudflare
dig @9.9.9.9 <host> A +short +time=3 +tries=1     # Quad9
```
TTL-Wert separat:
```bash
dig <host> A +noall +answer +time=3 +tries=1
```
→ aufgelöste IPs je Resolver + DNS-TTL.

### TLS-Handshake + Verbindungs-Timing (zwei Wege)

**(a) `curl`-Timing** (zerlegt den Aufbau in Phasen — exakt die Submetrik-Logik):
```bash
curl -s -o /dev/null --connect-timeout 10 \
  -w "dns_ms:%{time_namelookup}\ntcp_connect_ms:%{time_connect}\ntls_done_ms:%{time_appconnect}\nttfb_ms:%{time_starttransfer}\ntotal_ms:%{time_total}\nhttp_version:%{http_version}\n" \
  <url>
```
→ `dns_ms`, `tcp_connect_ms`, `tls_handshake_ms (= time_appconnect − time_connect)`, ttfb, total, HTTP-Version.

**(b) Python-`ssl`** (für TLS-Details, die curl nicht zeigt):
```python
ctx = ssl.create_default_context()
ctx.set_alpn_protocols(["h2", "http/1.1"])
sock  = socket.create_connection((host, 443), timeout=5.0)
ssock = ctx.wrap_socket(sock, server_hostname=host)
# → ssock.version()  ssock.cipher()  ssock.selected_alpn_protocol()  Zertifikat-CN
```
→ `tls_version`, Cipher-Suite, ausgehandeltes ALPN, Zertifikat-Common-Name + `tcp_connect_ms`/`tls_handshake_ms`.

### Route (Traceroute) + AS-Pfad
```bash
traceroute -n -w 2 -q 1 -m 25 <host>
```
AS-Nummer je Hop-IP via Team-Cymru-DNS:
```bash
dig +short <reversed-ip>.origin.asn.cymru.com TXT +time=2 +tries=1
```
→ Hop-Liste + AS-Pfad (zeigt, über welche Netze/Provider die Route läuft).

### DNSSEC-Status (optional)
Per `dnspython`: AD-Flag, RRSIG im Answer, DS-Record beim Parent → ob die Zone signiert/validiert ist.

---

## Layer 2 — Paketaufzeichnung (nur Dumping)

### Capture (pro Anbieter, n=1, mit sudo)
```bash
sudo tcpdump -i <iface> -w data/layer2/capture_<provider>_<YYYYMMDD_HHMM>.pcap \
     host <host> -s 0 -c 200000
```
Ablauf: tcpdump starten → **N≈30 Cold-Start-Calls** nacheinander ausführen → tcpdump (SIGTERM) stoppen.
→ ein PCAP mit N Handshakes (in der Analyse am 4-Tupel getrennt). Interface vorher prüfen:
```bash
ip -br link        # Interface-Namen ermitteln (z.B. ens5 / eth0)
```

### Analyse (nachgelagert, kein Live-Messen)
Felder je Paket extrahieren:
```bash
tshark -r <pcap> -T fields -E separator='|' -E header=n \
  -e frame.number -e frame.time_relative -e frame.len \
  -e tcp.srcport -e tcp.dstport -e tcp.flags -e tcp.len \
  -e ip.src -e ip.dst
```
Daraus berechnet das Analyse-Skript: `tcp_handshake_ms` (SYN→SYN-ACK), Round-Trips bis erste
App-Daten, **Inter-Arrival-Time** (Diff von `frame.time_relative`), Paketgrößen (`frame.len`/`tcp.len`),
Retransmits. → s. PCAP-Größen-Tabelle im `messprotokoll.md`.

---

## Layer 3 — API-Latenz (Cold-Start, aktives Messen)

Kein generisches CLI-Tool — pro Anbieter ein Wrapper, der eine **frische** Verbindung aufbaut, den
festen Input sendet und die Timestamps/Submetriken misst (s. Layer-3-Abschnitt im Protokoll). Aufruf
über einen Runner mit Slot-/n-Parametern:
```bash
python measurements/layer3/run.py --n 100 --tag 09h --api all   # oder: stt | llm | tts
python measurements/layer3/run.py --n 3  --tag test --api stt --dry-run   # Test ohne Schreiben
```
- `--n` Messungen pro Anbieter (Kampagne: 100), `--tag` Tageszeit-Slot (`09h`, `12h`, …, wird ins JSONL
  geschrieben → Gruppierung nach `tag`, nicht nach Timestamp, s. A12).
- `MEASUREMENT_DELAY_S = 1.5` s Pause zwischen Einzelmessungen (Rate-Limit-Schutz).
- Ergebnis: JSONL je Slot mit allen rohen Timestamps + Submetriken (s. Rohdaten-Speicherung im Protokoll).

> Die Slot-Automatisierung (8 Slots/Tag, alle 3 h, 7 Tage) läuft per Scheduler (cron/systemd-timer)
> auf der EC2 — die genaue Slot-Mechanik wird im Kampagnen-Abschnitt festgelegt.

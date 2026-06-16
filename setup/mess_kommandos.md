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
> ⚠️ **Plattform-Notiz `-W`:** Unter **Linux** ist `-W` der Timeout in **Sekunden** (EC2-Kampagne →
> `-W 2` korrekt), unter **macOS** in **Millisekunden**. Für lokale Vortests auf dem Mac stattdessen
> `-t 5` (Gesamt-Timeout) bzw. `-W 2000` verwenden. Die Kampagne läuft ohnehin auf der EC2.

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
# WICHTIG: maximum_version NICHT cappen — sonst wird TLS 1.3 künstlich verhindert.
sock  = socket.create_connection((host, 443), timeout=5.0)
ssock = ctx.wrap_socket(sock, server_hostname=host)
# → ssock.version()  ssock.cipher()  ssock.selected_alpn_protocol()  Zertifikat-CN
```
→ `tls_version`, Cipher-Suite, ausgehandeltes ALPN, Zertifikat-Common-Name + `tcp_connect_ms`/`tls_handshake_ms`.

> ⚠️ **TLS-Versions-Footgun (A1) — verbindlich:** macOS-Python (System **und** projekt-`.venv`) ist
> gegen **LibreSSL 2.8.3** gelinkt und cappt auf **TLS 1.2** → die Probe meldet **alle** Hosts fälschlich
> als 1.2. Daher:
> 1. **`tls_version` nie aus macOS-Python** übernehmen — die TLS-Version wird **ausschließlich auf der
>    EC2** (echtes OpenSSL 3.x) erhoben. macOS-Python nur für Dev/Logik-Tests.
> 2. Pro Messung **`ssl.OPENSSL_VERSION` mitloggen** → LibreSSL-Zeilen sind sofort verwerfbar.
> 3. Nach dem Handshake `ssock.version()` als **harten Guard** prüfen (z. B. Assert „nicht < 1.2 wegen
>    Lib-Cap").
> 4. **Cross-Check mit echtem OpenSSL:** `openssl s_client -connect <host>:443 -servername <host> -tls1_3`
>    (bzw. ohne `-tls1_3` → ausgehandelte Version aus „Protocol :"-Zeile lesen).
> 5. **Interpreter pinnen** (s. Lockfile/Versions-Capture, A5) — die TLS-Quelle muss reproduzierbar OpenSSL sein.

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

## Layer-1-Skripte — gebaut & reviewt (Stand 2026-06-15)

Die obigen Befehle sind jetzt als kleine Python-Wrapper in **`measurements/layer1/`** umgesetzt. Jedes
Skript läuft über alle 7 Hosts (zentral in `hosts.py`), druckt eine Tabelle und speichert die Rohdaten
als JSONL in **`data/layer1/<skript>.jsonl`**. Gebaut „Methodik-first"; jedes Skript wurde **einzeln per
ultracode-Review** geprüft (Finden → adversariale Gegenprüfung), die bestätigten Fixes sind eingearbeitet.

| Messung | Skript | setzt Befehl um | wichtige Entscheidungen / Rohdaten |
|---------|--------|------------------|------------------------------------|
| TCP-RTT (**primär**) | `tcp_ping.py` | Python-`socket`-Handshake | N=20, **min + median**, **alle** Rohwerte (`rtts_ms`), `resolved_ip`; Uhr stoppt vor `close()` |
| ICMP-RTT (Cross-Check) | `icmp_ping.py` | `ping -c` | N=10; pingt die **aufgelöste IP** (gleiche IP wie TCP → fairer Vergleich); „geblockt" vs. echter Fehler getrennt; volle `raw`-Ausgabe |
| DNS Multi-Resolver | `dns_lookup.py` | `dig @8.8.8.8/1.1.1.1/9.9.9.9` | IPv4 je Resolver + TTL (über Google-Resolver; = **verbleibende Cache-TTL**) |
| ASN/Netz je IP (**Bed. b**) | `asn_lookup.py` | `dig TXT …origin.asn.cymru.com` | **alle** IPv4s je Host, MOAS-sicheres Parsing, rohe Cymru-Zeile gespeichert |
| TLS-Info + Timing | `tls_info.py` | Python-`ssl` | A1-Guard (Version **nur auf EC2** belastbar), TCP/TLS getrennt getimt, Cipher + Bits + Cert-CN/SAN |
| Traceroute + AS-Pfad (**Bed. c**) | `traceroute_asn.py` | `traceroute -n` + Cymru | auf **aufgelöste IP**, 25 Hops, `-w 2`, `reached_dest`-Flag, ASN-Cache |

**Gemeinsame Bau-Prinzipien (Lehre aus Review + altem Lauf):**
- Jedes Skript gibt **IMMER einen Record pro Host** zurück — auch bei Fehler (DNS, fehlendes Tool, Timeout).
  Kein einzelner Fehlschlag reißt den ganzen Lauf ab.
- **Fehlendes CLI-Tool** (`dig`/`traceroute` sind auf frischem Ubuntu/EC2 **nicht** vorinstalliert!) wird
  gefangen (`except OSError`), nicht als Crash.
- **Rohdaten vollständig** speichern (alle Einzelwerte, rohe Tool-Ausgabe), nicht nur Aggregate.
- Hosts **zentral** in `hosts.py` (eine Quelle der Wahrheit).

**Ausführen** (vom Repo-Wurzelverzeichnis):
```bash
.venv/bin/python measurements/layer1/<skript>.py     # tcp_ping | icmp_ping | dns_lookup | asn_lookup | tls_info | traceroute_asn
```

**Dokumentierte Entscheidungen (2026-06-15):**
- **TCP-SYN-Traceroute (Bedingung c):** Das Skript nutzt **UDP**-Traceroute (ohne sudo, Mac-tauglich).
  Auf der **EC2 zusätzlich** (mit sudo), weil Cloudflare/Azure UDP stärker filtern:
  `sudo traceroute -T -p 443 -n -w 2 -q 1 -m 25 <ip>` → belastbarer für (c); ggf. später als `--tcp`-Flag.
- **Output-Pfad** ist `cwd`-relativ (bewusst simpel) → Skripte **vom Repo-Root** starten.
- **DNSSEC** (oben als optional markiert) ist **noch nicht** gebaut → bei Bedarf nachrüsten.

---

## Layer 2 — Paketaufzeichnung + Handshake-Eichung

Skripte: `measurements/layer2/capture.py` (Cold-Start-Connects + Quell-Port-Log) + `analyze.py`
(parst die PCAP via `tcpdump -r`, paart per Quell-Port, vergleicht Wire vs. App). **Keine Extra-Library.**

### Eichung (durchgeführt 2026-06-16, je host-terminierter Provider, feste Ziel-IP)
```bash
# iface prüfen: ip -o -4 route show to default
sudo timeout 25 tcpdump -i ens5 -n -w data/layer2/cap_<prov>.pcap "tcp port 443 and host <IP>" &
.venv/bin/python measurements/layer2/capture.py --host <host> --ip <IP> --n 30 --out data/layer2/applog_<prov>.jsonl
.venv/bin/python measurements/layer2/analyze.py --pcap data/layer2/cap_<prov>.pcap --applog data/layer2/applog_<prov>.jsonl
```
**Ergebnis:** App-`tcp_handshake_ms` = Wire-SYN→SYN-ACK auf ~0,1 ms genau (Azure 11 ms: +0,11; Deepgram
139 ms: +0,12) → Layer-3-Timer am Paket-Level validiert (C2). Feste `--ip` bei Round-Robin (Deepgram).

### Richere PCAP-Analyse (Analyse-Phase, optional)
Inter-Arrival-Times der Antwort-Pakete / Retransmits aus *während echter API-Calls* aufgezeichneten PCAPs —
ebenfalls dependency-frei via `tcpdump -tt -n -r <pcap>` parsebar (Muster s. `analyze.py`). Noch ausstehend.

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

> Die Slot-Automatisierung (8 Slots/Tag, alle 3 h, 7 Tage) läuft per **cron** auf der EC2 — Deploy,
> Instanz, Betrieb und Pilot-Ergebnisse stehen in **`setup/deployment.md`**.

---

## Layer-3-Skripte — gebaut & reviewt (Stand 2026-06-15)

Umgesetzt in **`measurements/layer3/`**. Cold-Start je Call (frische Verbindung, kein Pooling),
durchgängig **IPv4** (s. messprotokoll.md). Jeder Caller gibt **IMMER einen Record** zurück. Jedes
Skript wurde **einzeln per ultracode-Review** geprüft (Finden → adversariale Gegenprüfung), Fixes eingebaut.

| Skript | Rolle | wichtige Entscheidungen / Metriken |
|--------|-------|-----------------------------------|
| `config.py` | Single Source of Truth | Endpunkte, gepinnte Modelle (A2), Timeouts (A7), Keys aus `.env`, Pfade via `__file__` (cron-robust) |
| `connect.py` | atomare dns/tcp/tls-Submetriken | Wegwerf-Socket = **Referenz** (TCP+TLS, kein h2); echte Peer-IP kommt aus dem Mess-Request |
| `llm.py` | OpenAI/Groq/Mistral (HTTPS+SSE) | `ttft`/`total` **connect-INKLUSIV**; `effective_model` aus `chunk.model` (A2); IPv4 erzwungen (`local_address`) |
| `tts.py` | Deepgram/OpenAI/Azure (HTTPS-Stream) | `ttfa`/`total`/`audio_bytes`/`n_chunks`; mp3 gepinnt (A8); `audio_bytes` nur Erfolgs-Gate, **kein** Cross-Provider-Maß (Bitrate ≠) |
| `stt.py` | Deepgram/Rev.ai/Azure (rohe WebSockets) | **`ttfp`** (Time-to-first-Partial) **primär**, `ttft` (Final) sekundär, beide **connect-EXKLUSIV**; **Audio 1×-realtime gepaced** + paralleler Empfang (`asyncio.gather`); Submetriken `ws_connect`/`session_init`/`audio_upload`; Audit `ttfp_is_final`/`ttfp_text`; **voller Transkript-String** (A14) |
| `run.py` | Slot-Runner | interleaved Round-Robin + Rotation, 1,5 s Delay; **flock** (kein Parallel-Slot), **Slot-Deadline**, **Per-Call-Timeout**, `run_meta`+`run_end` (A5/A6/A8) |

**Ausführen:** `.venv/bin/python measurements/layer3/<skript>.py` (einzeln) bzw.
`run.py --n 100 --tag 09h` (ein Slot). Rohdaten → `data/layer3/` bzw. `data/layer3/campaign/<tag>_<ts>.jsonl`.

**Wichtige Mess-Entscheidungen (Pilot-bestätigt, s. deployment.md):**
- **Rev.ai-Session-Init:** der „connected"-Recv (~1 RTT) liegt zwischen WS-Connect und erstem Chunk →
  als eigene Submetrik `session_init_ms` erfasst, damit `ws_connect`/user-perceived Cold-Start cross-provider fair bleiben.
- **STT-Audio 1×-realtime gepaced** (nicht Dump) + paralleler Empfang → nur so liefern alle drei echte Interims für `ttfp` (endpointing-frei, cross-provider fair); `ttft` (Final) enthält zusätzlich Endpointing, über `ttft − audio_upload_ms` isolierbar. S. `messprotokoll.md` → „STT-Primärmetrik".
- **Rev.ai-Billing:** ~15 s/Call (15-s-Boden, Wall-Clock ~2 s) → ~1.400 min für die volle Kampagne.

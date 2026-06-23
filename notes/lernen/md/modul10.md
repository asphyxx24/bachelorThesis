# Modul 10 — Code-Architektur & Timing

**Ziel:** Ein Skript am Bildschirm grob durchgehen können — wo liegt was, wo läuft die Uhr, wie setzt der Code die Methodik um. Überblick-Modul.

## 10.1 Verzeichnis-Struktur

Der Code spiegelt die drei Schichten:

- **`measurements/layer1/`** — `hosts.py` (9 Endpunkte) + Einzel-Tools (TCP-Ping, ICMP, DNS, ASN, TLS, Traceroute).
- **`measurements/layer2/`** — `capture.py` (Cold-Start-Connects, tcpdump parallel) + `analyze.py` (PCAP-Auswertung).
- **`measurements/layer3/`** — das Herz:
  - `config.py` — **Single Source of Truth** (Endpunkte, Modelle, Timeouts, feste Inputs).
  - `connect.py` — Connect-Submetriken (Wegwerf-Socket).
  - `llm.py` / `tts.py` / `stt.py` — je ein Caller.
  - `run.py` — **Orchestrator** (fährt einen Slot ab).

*Merksatz: Konfiguration zentral, Messlogik pro Kategorie getrennt, Orchestrierung an einer Stelle.*

## 10.2 Timing — wo die Uhr läuft

Alle Zeiten aus **`time.perf_counter()`** (monoton, hochauflösend), in ms. **LLM-`ttft`-Uhr:** Start `t_request` *kurz vor* dem Request-Absenden (vor der frischen Verbindung), Stopp beim ersten SSE-Content-Chunk (`t_first_token`). `llm_ttft = t_first_token − t_request` → connect ist **inklusive** (Asymmetrie aus Modul 8).

## 10.3 Cold-Start im Code

Für **jeden** Call ein **frischer** `httpx.Client` bzw. eine frische WebSocket-Verbindung, danach geschlossen. Wiederverwenden würde via Keep-Alive/Pooling den Verbindungsaufbau ab Call 2 wegfallen lassen — genau den Teil, den du messen willst. Der frische Client ist die **technische Garantie** für Cold-Start.

## 10.4 IPv4-Zwang

Erzwungen (httpx `local_address="0.0.0.0"`, Sockets `AF_INET`). Mehrere Hosts sind dual-stack; ohne Zwang wählte Layer 3 evtl. IPv6, während Layer 1 IPv4 misst → Cross-Layer-Brücke und Edge/Host-Klassifikation verglichen verschiedene Adressfamilien. Der Zwang sorgt dafür, dass **alle Schichten dieselbe Adresse** sehen.

## 10.5 `run.py` — Orchestrator

- **`flock`** — verhindert überlappende Slots.
- **Interleaved Round-Robin mit Rotation** (`shift = rnd % len(eps)`): jede Runde durch alle 9 Endpunkte, Startreihenfolge rotiert. **Was verhindert das Rotieren?** Ohne Rotation säße ein Anbieter dauerhaft auf derselben (bevorzugten/benachteiligten) Position; Rotation verteilt die Positionen gleichmäßig.
- **Per-Call-Hard-Timeout (75 s, Thread)** — Backstop gegen hängende Calls.
- **Sauberes JSONL:** `run_meta` → Call-Records → `run_end`; SIGTERM-sauber.

## 10.6 Erfolg ist content-basiert

Erfolg ≠ „Verbindung stand", sondern **inhaltlich gültiger Output**: LLM ≥ 1 Wort & ≥ 3 SSE-Chunks; TTS ≥ 1000 Bytes; STT nicht-leeres Final. Sonst zählte eine quasi-leere Antwort fälschlich als „schnell" (Mangel A10: Mistral hatte ~72 quasi-leere „Erfolge"). Fehler werden als **roher String** gespeichert, Bucketierung erst in der Auswertung (H3: nicht naiv über `error == 'timeout'` filtern).

## Prüf-Fragen

1. Wo startet/stoppt die LLM-`ttft`-Uhr im Code — und warum ist connect damit enthalten?
2. Warum ein frischer Client je Call — was würde Wiederverwenden kaputtmachen?
3. Was verhindert das Rotieren der Startreihenfolge?
4. Warum ist „Erfolg" content-basiert und nicht „Verbindung stand"?

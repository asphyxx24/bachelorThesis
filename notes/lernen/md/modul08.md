# Modul 8 — Layer 3 & Metrik-Asymmetrie ⭐

**Ziel:** Die Metriken sattelfest erklären — der häufigste Prüf-Punkt: Connect-Submetriken (Wegwerf-Socket), die Asymmetrie (STT connect-exklusiv vs. LLM/TTS connect-inklusiv), die korrekte E2E-Formel, die zwei IP-Felder + Fail-Filter-Falle und der Output-Mengen-Confound.

> **Hinweis:** Alle Kampagnen-Zahlen sind **A4-Mediane** der **Vollkampagne, abgeschlossen (56/56 Slots)** (success-only); die Bootstrap-Konfidenzintervalle stehen noch aus. Die **Punktschätzer sind final**, die **Ordnung ist stabil**.

## 8.1 Was Layer 3 misst + Cold-Start

- **Layer 3** misst die **API-Latenz** (Application Programming Interface = Aufruf-Schnittstelle eines Dienstes) der 9 Anbieter — als **einzige** Schicht über die **volle URL bis zum Backend** (Layer 1 misst nur bis zum Host). → misst die **Engine-Verarbeitung**.
- **Cold-Start:** jede Messung baut eine **frische** TCP- + TLS-Verbindung auf — **kein** Connection-Pooling, **kein** Keep-Alive. Begründung: realer Overhead einer **neuen Gesprächssession** (so wie ein Nutzer, der eine Voice-Interaktion startet). Warm-Reuse würde den Verbindungsaufbau verstecken — gerade der ist aus EU-Sicht (Distanz zum US-Backend) interessant.

## 8.2 Begriffe

- **Submetrik:** ein **Teilstück** einer größeren Messgröße — nicht der ganze Connect als eine Zahl, sondern **jede Phase einzeln** (`dns_ms`, `tcp_handshake_ms`, `tls_handshake_ms`; bei STT zusätzlich der WS-Upgrade, der im `ws_connect_ms` steckt — kein eigenes `ws_upgrade_ms`-Feld).
- **Socket:** Endpunkt einer Netzwerkverbindung im Betriebssystem (die „Steckdose" einer Verbindung).
- **Wegwerf-Socket:** eine **eigene, nur dafür geöffnete** Verbindung, die den Connect atomar zerlegt und danach **sofort geschlossen** wird — getrennt von der eigentlichen Mess-Anfrage (`connect.py`).
- **`getpeername`:** Betriebssystem-Aufruf auf einem offenen Socket, der zurückgibt, **mit welcher IP** dieser Socket tatsächlich verbunden ist.
- **Round-Robin:** ein Hostname wird **reihum** auf mehrere IPs aufgelöst (mal die eine, mal die nächste).
- **connect-exklusiv vs. connect-inklusiv:** ob der Verbindungsaufbau **abgezogen** ist (exklusiv) oder **enthalten** ist (inklusiv).
- **E2E (End-to-End):** Gesamtlatenz der **kompletten sequenziellen** Pipeline STT → LLM → TTS.
- **Confound (Störgröße):** eine versteckte dritte Größe, die einen Vergleich verfälscht, weil sie sich mit der gemessenen Größe **vermischt** (man glaubt A zu messen, misst aber A vermischt mit B).

## 8.3 Connect-Submetriken (Wegwerf-Socket)

Der frühere Sammel-Timer `connect_ms` (Black-Box, eine Zahl) ist **abgeschafft**. Stattdessen wird der Aufbau in **atomare Teile** zerlegt und **roh** gespeichert:

| Submetrik | misst | ≈ RTT | gilt für |
|-----------|-------|-------|----------|
| `dns_ms` | Namensauflösung (Hostname → IP), getrennt, da oft gecacht | — | alle |
| `tcp_handshake_ms` | SYN → SYN-ACK | 1 RTT | alle |
| `tls_handshake_ms` | ClientHello → Handshake fertig (TLS 1.3) | 1 RTT | alle |
| `ws_upgrade_ms` | WebSocket-Upgrade + Session-Init | 1 RTT | **nur STT** |
| *(abgeleitet)* `connect_total_ms` | **Summe** der obigen Phasen | — | nur in der Auswertung |

- **Warum Wegwerf-Socket?** `httpx` (LLM/TTS) gibt die Phasen **nicht atomar** heraus. `connect.py:connect_submetrics()` öffnet daher kurz **einen separaten Socket**: `gethostbyname` (→ `dns_ms`), `socket.create_connection` (→ `tcp_handshake_ms`), `wrap_socket` (→ `tls_handshake_ms`), dann `close()`.
- **Rolle bei LLM/TTS: nur Referenz.** Das echte `ttft`/`ttfa` läuft connect-inklusiv über die echte Anfrage; der Wegwerf-Socket dient nur dazu, den connect-Anteil bei Bedarf **herausrechnen** zu können.
- **Vorteil:** dieselbe atomare Phase ist über **alle 9 Endpunkte** vergleichbar; `tcp_handshake_ms` ist zudem **identisch** mit dem Layer-1-TCP-Ping → Cross-Layer-Brücke (`connect ≈ N_RTTs × ping`) **transparent statt behauptet**.

## 8.4 Die Metrik-Asymmetrie (Kern)

Die entscheidende Frage: **Ab wann läuft die Uhr für das erste Token/Audio?** — nicht über alle Kategorien gleich, deshalb **explizit deklariert**:

| Kategorie | Uhr startet bei | connect | Erste-Ausgabe-Metrik |
|-----------|-----------------|---------|-----------------------|
| **STT** | **erstem Audio-Chunk** (nach dem Connect) | **exklusiv** | `ttfp` (Time-to-first-**Partial**, primär) |
| **LLM** | **Absenden des Requests** (frische Verbindung) | **inklusiv** | `ttft` (Time-to-first-**Token**) |
| **TTS** | **Absenden des Requests** (frische Verbindung) | **inklusiv** | `ttfa` (Time-to-first-**Audio**) |

- **STT = connect-exklusiv:** der Verbindungsaufbau ist **abgezogen** (steht separat in den Submetriken); `ttfp` zählt ab dem ersten Audio-Chunk.
- **LLM/TTS = connect-inklusiv:** die Uhr startet **vor** dem Verbindungsaufbau (beim Request-Absenden über die frische Verbindung), der Connect **steckt also in der Zahl**.
- **Im Code sichtbar:** in `llm.py` wird `t_req = time.perf_counter()` gesetzt und **direkt danach** `client.stream(...)` aufgerufen — die Uhr läuft über den Verbindungsaufbau hinweg (`ttft_ms = t_first_token − t_req`). Identisches Muster in `tts.py` (`ttfa_ms`). Bei STT startet die Uhr erst am ersten Audio-Chunk.

## 8.5 Warum die Asymmetrie (Kernantwort)

Sie bildet die **reale Nutzungssituation** ab — gemessen wird jeweils die **vom Nutzer wahrgenommene** Wartezeit, und die beginnt kategorienspezifisch:

- **STT:** wahrgenommen ab dem Moment, in dem **Audio zu fließen beginnt** → user-perceived STT-Cold-Start = **`connect_total + stt_ttfp`** (connect bewusst getrennt, hinterher zusammensetzbar).
- **LLM/TTS:** wahrgenommen schon **mit dem Absenden des Requests** (inkl. Verbindungsaufbau) → daher connect-inklusiv korrekt.

In beiden Fällen misst man genau das, was der Nutzer als Wartezeit erlebt — nur der Startpunkt unterscheidet sich.

## 8.6 E2E nicht naiv addieren

**E2E (End-to-End)** = Gesamtlatenz der **sequenziellen** Pipeline STT → LLM → TTS (sequenziell, weil das LLM erst auf dem **finalen** Transkript starten kann).

- **Die Falle (naiv):** alle connect-Zeiten **plus** alle ttf-Zeiten addieren → **zählt connect bei LLM und TTS DOPPELT** (er steckt dort schon im connect-inklusiven `ttft`/`ttfa`). Ergebnis künstlich zu groß.
- **Korrekte Formel:**

  ```
  E2E = stt_connect + stt_ttft + llm_ttft + tts_ttfa
  ```

  - **STT** trägt **connect + ttf** bei (seine Metrik ist connect-**exklusiv**, enthält den Aufbau nicht).
  - **LLM und TTS** tragen **nur ihr `ttft` bzw. `ttfa`** bei (ihr Aufbau steckt schon drin).
  - → connect zählt **pro Stufe genau einmal**, nie doppelt.
- **Detail:** für die sequenzielle Pipeline trägt STT **`stt_ttft`** (finales Transkript) bei, **nicht** `ttfp` — das LLM wartet auf das Final, nicht auf das erste vorläufige Wort. Die `ttfp`-Summe ist nur **STT-Standalone-Responsiveness**, **keine** realisierbare Pipeline-Latenz.

## 8.7 Die zwei IP-Felder + Fail-Filter-Falle

Jeder Record trägt **zwei** IP-Felder verschiedener Herkunft; bei Round-Robin weichen sie in **~29 %** der Calls ab.

| Feld | Herkunft (Code) | Eigenschaft | Verwenden für |
|------|-----------------|-------------|---------------|
| top-level `resolved_ip` | `getpeername` am **realen Mess-Socket** (`llm.py` / `tts.py`) | **echter Peer** der Mess-Anfrage; **`null` bei Fails** | **nur** Cross-Layer-RTT-Brücke (welcher reale Server lieferte die Latenz), dort **nur** Samples mit `resolved_ip == connect.resolved_ip` |
| `connect.resolved_ip` | `gethostbyname` am **Wegwerf-Socket** (`connect.py`) | **immer befüllt**, auch bei Fails; eigene Round-Robin-Ziehung | **Region, ASN, Verfügbarkeit, connect-Submetriken** |

- **Warum zwei Felder?** Bei **Round-Robin** kann der Wegwerf-Socket eine **andere IP** ziehen als die echte Mess-Anfrage → daher die **~29 %** Abweichung. Verwechslung verfälscht IP-/Region-/Brücken-Analysen.

**Fail-Filter-Falle (kritisch):**

- Fails **NIE** über „top-level `resolved_ip` ist `null`" filtern! Bei einem Fail ist dieses Feld **gerade `null`** → man würde **genau die Timeouts/Abbrüche** aus der Verfügbarkeitsrechnung werfen und die Verfügbarkeit **auf 100 % schönrechnen**.
- **Immer** über das **`success`-Flag** bzw. den **Fehler-String** filtern (beides bleibt auch bei Ausfall erhalten und macht ihn sichtbar).

## 8.8 Output-Mengen-Confound (A8)

- **Confound:** `total_ms` skaliert mit der **Ausgabelänge** (wer mehr sagt, braucht länger). → ein **wortkarges** Modell wirkt „schnell" **durch Knappheit, nicht durch Tempo** — ein Pseudo-Sieg, wenn man nach `total_ms` rankt.
- **Lösung:** **`ttft`/`ttfa` sind PRIMÄR** — sie messen nur bis zum **ersten** Ausgabe-Element und sind damit **mengen-unabhängig** (das erste Token kommt gleich schnell, egal ob 5 oder 50 folgen). `total_ms` nur **sekundär** und **pro Token normalisiert**.
- **LLM:** `max_tokens=50` ist ein **Cap** (Obergrenze), **kein Fixwert** → die Ausgabemenge streut weiterhin → `total_ms` nicht roh vergleichen.
- **TTS:** nur der **Container `mp3`** ist gepinnt, **nicht die Bitrate** → `audio_bytes` streut **~3,6×** → dient **nur als Erfolgs-Gate**, **nicht** als Vergleichsmaß. `ttfa` (erstes Audio-Byte, mengen-unabhängig) bleibt fair; `total_ms` ist cross-provider **nicht** vergleichbar.

## Prüf-Fragen

1. Warum startet die STT-Uhr anders als bei LLM/TTS?
2. Was passiert, wenn man E2E naiv aufsummiert?
3. Welches IP-Feld wofür — und warum nie Fails über das null-Feld (top-level resolved_ip) filtern?
4. Warum gewinnt ein wortkarges Modell nicht einfach durch Knappheit?

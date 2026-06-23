# Modul 12 — Datenartefakte & echte Ergebnisse

**Ziel:** Wissen, wo welche Zahl herkommt, was sie bedeutet, und was bewusst *nicht* verwendet wird. Die Zahlen sind die **finalen 56-Slot-Werte** (Vollkampagne, abgeschlossen 56/56, A4 = Median der Slot-Mediane, success-only); Bootstrap-CI noch ausstehend.

## 12.1 Begriffe

- **Datenartefakt:** Eine Zahl/ein Ergebnis, das nicht den vermuteten echten Effekt misst, sondern eine Eigenschaft des **Mess- oder Aufbereitungs-Vorgangs** selbst. Gefährlich, weil es wie ein Befund aussieht (Beispiel weiter unten: die alte „1722 ms = Endpointing"-These war ein Dump-Bulk-Compute-Artefakt).
- **Slot:** Ein Mess-Zeitfenster, in dem alle 9 Endpunkte je `n=100` gemessen werden. Geplant: 56 Slots; final gelandet: **56 von 56 Slots (A4)**.
- **A4 (Median der Slot-Mediane):** robustes Aggregat über die 56 Slots, success-only. Bootstrap-CI noch ausstehend.
- **ASN (Autonome-System-Nummer):** Kennung des Netzbetreibers, dem ein IP-Bereich gehört — die „Eigentums-Auskunft" einer IP. Cloudflare = `AS13335`.
- **Edge:** CDN-Knoten nahe Frankfurt, der die Verbindung annimmt, ohne dass das Verarbeitungs-Backend in der Nähe ist.

> **Prüfer-Frage hinter diesem Modul:** Nicht nur „ist die Zahl richtig?", sondern „**woher weißt du, dass diese Zahl das misst, was du behauptest** — und nicht ein Nebenprodukt deiner Pipeline?"

## 12.2 Der maßgebliche Datensatz + Beleg-Artefakte

**Maßgeblich** (Quelle aller Latenz-Zahlen):

| Pfad | Inhalt | Status |
|------|--------|--------|
| `data/audit_20260618/ec2_data/` | Roh-Pull der Kampagne von der EC2 (Frankfurt) | **56 von 56 Slots (A4)**, gitignored |

**Beleg-Artefakte daneben** (keine Latenz, sondern Cross-Layer-Absicherung):

| Datei | Inhalt | Wozu |
|-------|--------|------|
| `data/audit_20260618/l1_rtt_per_ip.md` | RTT je produktiv getroffener IP | belegt die Netz-Distanz pro realem Server |
| `data/audit_20260618/asn_per_ip.md` | ASN je IP | belegt, an welchem Netz/welcher Edge die Verbindung endet |

Diese beiden schließen die **Cross-Layer-Brücke** (Layer 1 ↔ Layer 3): Sie verbinden die Netzwerk-Messung (Schicht 1) mit der Anwendungs-Messung (Schicht 3).

## 12.3 Die Kernzahlen (final, 56 von 56 Slots, A4)

### LLM — `ttft` (Time-to-first-Token, Request-Absenden → erstes Token)

| Provider | `ttft` | Edge-RTT | Termination |
|----------|--------|----------|-------------|
| **Groq** | **~66,9 ms** | ~1,3 ms | Cloudflare FRA, `AS13335` |
| **Mistral** | **~278,9 ms** | ~1,1 ms | Cloudflare FRA, `AS13335` |
| **OpenAI** | **~486,6 ms** | ~1,2 ms | Cloudflare FRA, `AS13335` |

→ **Faktor ~7,3×** (gepoolt 8,3×) zwischen schnellstem und langsamstem — bei **identischer Edge-RTT (~1 ms)**. Gleiches Netz, gleiche Distanz, trotzdem ~7,3×. **Die Spreizung kann nicht von der Netznähe kommen** — das ist der Kernbeleg (C1). Geografie ist sogar **invertiert**: EU-Mistral langsamer als US-Groq.

### Edge & Eichung

- **Edge-RTT:** rund **1 ms** (Cloudflare FRA, `AS13335`) — echte Infrastruktur-Eigenschaft, kein Mess-Artefakt.
- **Layer-2-Eichung:** App-`tcp_handshake_ms` trifft die Wire-Latenz auf **±0,1 ms** genau. **Geeicht ist nur der Connect-Timer**; `ttft`/`ttfa` sind *nicht* direkt paket-geeicht, nutzen aber denselben `perf_counter`-Mechanismus.

### TTS — `ttfa` (Time-to-first-Audio)

| Provider | `ttfa` | Termination |
|----------|--------|-------------|
| **Azure** | **~94 ms** (schnellstes TTS) | echter EU-Host (Italy North) |
| **Deepgram** | **~516 ms** | echter US-Transit |
| **OpenAI** | **~942 ms** (connect ~1 ms, ttfa connect-exkl. ~941 ms) | Cloudflare FRA, `AS13335` (zweite identical-edge-Instanz) |

→ OpenAI-TTS terminiert am **selben Cloudflare-Edge** wie die OpenAI-LLM (connect ~1 ms), ist aber fast 10× langsamer als Azure → die ~942 ms sind **reines Backend** (connect-exkl. ~941 ms), stärkt C1. „Trotz US-Konkurrenz" gilt präzise nur ggü. Deepgram (echter US-Transit).

### STT — `ttfp` (Time-to-first-Partial, erstes Live-Wort)

| Provider | `ttfp` |
|----------|--------|
| **Azure** | ~1045 ms (gleichauf mit Deepgram) |
| **Deepgram** | ~1045 ms |
| **Rev.ai** | ~1494 ms |

→ **STT trägt C1 NICHT.** Auf der fairen Metrik `ttfp` ist Azure **nicht** der langsamste. Kein sauberer Backend-Beleg auf der STT-Achse.

## 12.4 Was belastbar ist

| Belastbar (final, A4) | Begründung |
|-----------------------|------------|
| Die **56-Slot-Kampagne** (`ec2_data/`) | maßgeblicher Latenz-Datensatz (56 von 56 Slots) |
| Der **EC2-Layer-1-Lauf** (16.6.) | korrekter Vantage Point (RTT/DNS/ASN) |
| Die **Layer-2-PCAP-Eichung** | Connect-Timer wire-validiert ±0,1 ms |

> **Stand:** Die Latenz-Zahlen sind final (Vollkampagne, abgeschlossen 56/56, A4 = Median der Slot-Mediane, success-only). **Offen:** Bootstrap-CI noch ausstehend.

**Unbestätigt:** Der **Tagesgang (diurnal)** — die Trennung Tag × Slot ist noch nicht abschließend geprüft → noch keine Tageszeit-Inferenz.

## 12.5 Was bewusst NICHT verwendet wird

| Quelle | Zahlen | Warum draußen |
|--------|--------|---------------|
| **Predeploy-Pilot** (Vorab-Probelauf vor dem Deploy) | LLM `75 / 268 / 476 ms` | **reproduziert aus keinem Kampagnen-Datensatz** → nicht mehr geführt; stattdessen Kampagne `~67/279/487 ms` (Ordnung identisch; finaler Faktor ~7,3× — gepoolt 8,3× — ist sogar **größer** als der Pilot, der Kernbefund wird dadurch stärker) |
| **macOS-Layer-1-Lauf** (im Repo unter `data/layer1/`) | RTT ~17–21 ms | **kein Vantage-Stempel** im Record (nur an der RTT-Größenordnung erkennbar); macOS-LibreSSL meldet zudem TLS falsch → nur EC2-L1 zählt |

## 12.6 Deepgram-Beleglage (ehrlich, teilzirkulär) — selbst ansprechen

**Teilzirkulär** = ein Beleg, der sich teilweise auf sich selbst stützt statt unabhängig zu sein.

- Für **Deepgram** stammt die **per-IP-RTT NUR aus dem Layer-3-`connect`-Timer** (SYN→SYN-ACK-Größe der produktiven Calls), **nicht** aus einem unabhängigen Layer-1-Ping.
- Der eigene L1-Ping deckte nur **1 von 6** produktiv getroffenen IPs (Deepgram = Multi-DC-Round-Robin). Der **langsamere Datacenter wurde nie unabhängig L1-gemessen**.
- `asn_per_ip.md` schließt die Lücke **sauber nur für die LLMs** (100 % `AS13335`).

> **Konsequenz:** Die Cross-Layer-Brücke ist für Deepgram **nicht** unabhängig geschlossen → als **Limitation offen benennen**. C1 hängt aber an den **LLMs** (Edge sauber + vollständig belegt), nicht an Deepgram — daher steht C1 trotzdem.

**Sag das von selbst:** „Für Deepgram ist die per-IP-RTT teilzirkulär (selber Connect-Timer, nur 1/6 IPs unabhängig gepingt). Mein Kernargument hängt an den LLMs, wo die Brücke per `asn_per_ip.md` für 100 % des Traffics sauber geschlossen ist."

## Prüf-Fragen

1. Welcher Datensatz ist maßgeblich, welcher nicht — und warum?
2. Was ist final (56-Slot-A4, success-only), und was bleibt offen (Bootstrap-CI)?

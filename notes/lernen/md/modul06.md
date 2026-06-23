# Modul 6 — Layer 1: Infrastruktur (Edge vs. Host) ⭐

**Ziel:** Den Prüfer-Einwand „drei Anbieter mit ~1 ms" sauber über die Edge/Host-Klassifikation auflösen — also belegen, warum drei Endpunkte aus Frankfurt eine RTT von ~1 ms zeigen, dass das **kein** Messfehler ist, und wie man sauber zwischen einem CDN-Edge und einem echten Host trennt.

## 6.1 Begriffe

Jeden Begriff so verinnerlichen, dass du ihn in eigenen Worten erklären kannst.

- **RTT (Round-Trip-Zeit):** Dauer, die ein Paket zum Ziel **und zurück** braucht. Direktes Maß für die Netz-Distanz: nah = kleine RTT, weit = große RTT.
- **ICMP:** Das *Internet Control Message Protocol*, das klassische Protokoll hinter dem `ping`-Befehl — eine Diagnose-/Kontroll-Sprache des Internets. Wird von vielen CDNs/Hosts **geblockt** (deshalb nicht als Primärmetrik geeignet).
- **TCP-Handshake:** Verbindungs-Aufbau in 3 Schritten — `SYN` → `SYN-ACK` → `ACK`. Für die Messung zählt nur `SYN` raus → `SYN-ACK` zurück = **genau 1 RTT**.
- **ASN (Autonomous System Number):** eindeutige Kennung eines Betreiber-Netzes. **`AS13335` = Cloudflare**, **`AS8075` = Microsoft**, `AS6461` = Zayo, `AS174` = Cogent, `AS16509` = Amazon. Gehört eine IP zu einer ASN, ist belegt, zu wessen Netz sie gehört.
- **CDN / Edge:** Ein *Content Delivery Network* betreibt viele weltweit verteilte Knoten. Ein Knoten nahe am Nutzer heißt **Edge** (Randknoten); er **terminiert** die Verbindung lokal statt am fernen Ursprungs-Server → ~1 ms RTT. Cloudflare ist so ein CDN.
- **Traceroute:** Werkzeug, das den Paket-Pfad Hop für Hop (Zwischenstopp für Zwischenstopp) sichtbar macht → zeigt, in welchem AS die Reise **endet**.
- **DNS-Resolver:** Namens-Auflöser. DNS = „Telefonbuch des Internets" (Name → IP). Öffentliche Resolver: Google `8.8.8.8`, Cloudflare `1.1.1.1`, Quad9 `9.9.9.9`.
- **TTL (Time-to-live):** Lebenszeit eines DNS-Eintrags in Sekunden — wie lange eine Antwort gültig bleibt. Kurze TTL = Anbieter kann häufig zwischen Adressen wechseln.
- **Anycast:** Dieselbe IP existiert an vielen Orten gleichzeitig; das Netz routet dich zum nächsten Standort. Der Trick, mit dem ein CDN eine Adresse überall nah erscheinen lässt.
- **Round-Robin:** Reihum-Verteilung — hinter einem Namen stehen mehrere IPs, das DNS gibt mal die eine, mal die andere zurück (Last über mehrere Rechenzentren).

## 6.2 Die Primärmetrik: TCP-Ping statt ICMP

RTT wird per **TCP-Handshake auf Port 443** gemessen (`measurements/layer1/tcp_ping.py`), **nicht** per ICMP. Drei Gründe:

1. **Vergleichbarkeit (Hauptgrund):** Eine faire Tabelle über alle 9 Endpunkte braucht **eine** Messgröße. ICMP wird von mehreren Endpunkten geblockt — nicht alle 9 antworten. ICMP für die einen + TCP für die anderen zu mischen vergliche zwei verschiedene Größen → angreifbar. TCP-Ping funktioniert bei **allen 9**, weil jeder API-Endpunkt per Definition TCP auf Port 443 annehmen muss.
2. **Relevanter Port:** TCP-Ping (`SYN` auf 443 → `SYN-ACK`) trifft **denselben Port** wie die echte API-Verbindung, nicht einen ICMP-Nebenkanal, den manche Anbieter abweichend behandeln.
3. **Konsistenz mit Layer 3:** TCP-Ping = `SYN`→`SYN-ACK` = **1 RTT** — exakt die Größe, in die sich `connect_total_ms` in Layer 3 zerlegt (`tcp_handshake_ms`). Layer 1 und Layer 3 sprechen dieselbe Sprache → die Cross-Layer-Brücke `connect ≈ N × ping` wird transparent.

**ICMP läuft trotzdem mit** — als *Cross-Validierung*. Wo **beide** Methoden funktionieren, zeigt man `tcp_ping ≈ icmp_ping` → Selbst-Validierung, dass TCP-Ping ein gültiger RTT-Proxy ist, und darf bei den ICMP-Verweigerern als alleinige Quelle dienen.

**Mess-Detail aus dem Code** (`tcp_ping.py`): DNS wird **einmal vorab** aufgelöst, dann zur IP verbunden (sonst steckte die DNS-Zeit in der RTT). `N=20` Pings je Ziel; ausgewertet werden **Minimum** (bester Schätzer der reinen Pfad-Latenz, am wenigsten durch Queueing verfälscht) und **Median** (enthält Queueing).

## 6.3 Die 3 Edge-Kriterien (Konjunktion — alle drei nötig)

Ein Endpunkt gilt **genau dann als Edge**, wenn **(a) ∧ (b) ∧ (c)** alle zutreffen — sonst **Host**:

| | Kriterium | Operationalisierung | Werkzeug |
|---|-----------|---------------------|----------|
| **(a)** | TCP-RTT ≈ **1–2 ms** aus FRA | Minimal-TCP-Ping auf Port 443 im einstelligen ms-Bereich | Layer-1-TCP-Ping |
| **(b)** | Ziel-IP in **CDN-ASN** | aufgelöste IP gehört zu Cloudflare `AS13335` (bzw. anderem CDN-AS) | ASN-/Whois-Lookup (Team-Cymru) |
| **(c)** | Traceroute **endet im CDN-AS** | letzter antwortender Hop liegt bei ~1 ms in `AS13335` — der Edge **ist** der Endpunkt, kein Durchstich zu fernem Backend | `traceroute` (Standard-UDP; TCP-SYN-Variante `-T -p 443` spezifiziert, aber noch offen — braucht root/sudo) |

**Warum alle drei?** Weil jedes einzelne Kriterium **täuschen** kann:
- Niedrige RTT allein ≠ Edge (siehe Azure, 6.5).
- Eine IP in einer ASN allein belegt noch nicht, dass die Verbindung dort terminiert.
- Ein Marketing-Label wie „Anycast" belegt gar nichts (siehe Deepgram, 6.5).

Erst die Konjunktion macht den Befund wasserdicht. Argumentiert wird über **gemessene Latenz + AS + Route**, **nicht** über „wem gehört die IP".

## 6.4 Die 3 RTT-Klassen (maßgeblicher EC2-Lauf, 16. Juni)

Maßgeblich ist **nur** der Lauf auf dem Vantage Point in Frankfurt — eine **einmalige Momentaufnahme** vom 2026-06-16 (kein Slotbetrieb). Drei saubere Klassen:

| Klasse | RTT | Anbieter | ASN / Org | Terminierung |
|--------|-----|----------|-----------|--------------|
| **Edge** | ~1 ms | OpenAI, Groq, Mistral (LLM) + OpenAI-TTS | `AS13335` Cloudflare FRA | **Edge** |
| **EU-RZ** | ~11 ms | Azure (STT + TTS) | `AS8075` Microsoft, Italy North — **kein CDN** | **Host** |
| **US-Backend** | ~140 ms | Deepgram | Zayo `AS6461` ×3 + Cogent `AS174` ×3 (Multi-DC) | **Host** |
| **US-Backend** | ~140 ms | Rev.ai | Amazon `AS16509` ×3 | **Host** |

Diese Klassifikation steht als feste Spalte in `setup/api_endpunkte.md` (§Terminierung) = **Single Source of Truth**.

## 6.5 „Messung > Marketing" — die zwei Lehrstücke

**Azure (~11 ms, trotzdem Host) — die Kernpointe:** Niedrige RTT heißt **nicht** automatisch Edge. Azure scheitert an **Kriterium (b)**: seine IP gehört zu `AS8075` (Microsoft) — **kein CDN**, sondern ein **echtes EU-Rechenzentrum** (Italy North). Niedrige Distanz, aber keine CDN-Terminierung → **Host**. Das ist sogar **wichtig für die Glaubwürdigkeit**: Azures Vorsprung bei TTS ist ein **realer Backend-Standort**, kein Edge-Artefakt.

**Deepgram (Anycast-Label, trotzdem Host) — der Umkehrfall:** Deepgram bewirbt sich als „Anycast", misst aber ~140 ms → scheitert an **Kriterium (a)** (RTT zu hoch) → **Host** (Multi-DC-Round-Robin). 

**Leitsatz:** *Messung schlägt Marketing.* Wir glauben nicht dem Werbe-Begriff, sondern der **gemessenen RTT + ASN + Route**.

## 6.6 Die DNS-Dimension: Multi-Resolver + TTL

Die DNS-Auflösung (`measurements/layer1/dns_lookup.py`) ist die **erste der vier Layer-1-Säulen** (DNS, RTT, TLS, Traceroute). Jeder Host wird über **drei unabhängige Resolver** aufgelöst:

- Google `8.8.8.8` · Cloudflare `1.1.1.1` · Quad9 `9.9.9.9`
- zusätzlich wird die **TTL** ausgelesen (optional das DNSSEC-AD-Flag).

**So erkennt man Round-Robin / Anycast:** Liefern die Resolver **mehrere oder wechselnde IPs**, ist es **Round-Robin**. Beispiel: **Deepgram löst auf 6 IPs über 2 ASNs** (Zayo + Cogent) auf → belegtes **Multi-Datacenter**. Eine kurze TTL verstärkt das Bild (häufiges Umschalten möglich). Das ist die Antwort auf „wie habt ihr Round-Robin/Anycast erkannt und mit welchen Resolvern": **Multi-Resolver-Vergleich aus 3 Quellen + TTL**.

## 6.7 Datensatz-Hygiene: H4 / A1 (warum nur der EC2-Lauf zählt)

Zwei Stolpersteine, die die Daten verteidigbar machen:

- **H4 (Vantage-Stempel):** `data/layer1/` enthält **zusätzlich** einen **macOS-Dev-Lauf** mit RTT ~17–21 ms. Dieser darf **nicht** in die Auswertung — ihm fehlt der **Vantage-Stempel** (kein Nachweis des Mess-Standorts). Maßgeblich ist **nur der EC2-Lauf** (Frankfurt). Der macOS-Lauf ist **nur an der RTT-Größenordnung** erkennbar → besonders aufpassen.
- **A1 (LibreSSL-TLS):** Das macOS-Python ist gegen **LibreSSL** gebunden, das die TLS-Aushandlung auf **1.2** deckelt und **alle** Hosts fälschlich als 1.2 meldet. Deshalb dürfen **TLS-Zahlen ausschließlich vom EC2** (echtes **OpenSSL 3.x**) stammen. Pro Messung wird `ssl.OPENSSL_VERSION` mitgeloggt → LibreSSL-Zeilen sofort verwerfbar.

> **Alle Kampagnen-Zahlen sind A4-Mediane über 56 von 56 Slots (Vollkampagne, abgeschlossen; success-only); die Bootstrap-Konfidenzintervalle stehen noch aus. Die Punktschätzer sind final, die Ordnung ist stabil.** Die maßgebliche L1-RTT ist die einmalige Momentaufnahme (16.6.), die Edge/Host-Klassifikation je IP ist zusätzlich über den L3-`connect`-Timer (56 von 56 Slots) bestätigt. Die **Edge/Host-Klassifikation** ändert sich dadurch **nicht** — sie ruht auf ASN + Größenordnung, nicht auf der letzten Nachkommastelle.

## Prüf-Fragen

1. Warum TCP- statt ICMP-Ping?
2. Nach welchen 3 Kriterien ist etwas „Edge"?
3. Warum ist Azure trotz 11 ms ein „Host"?
4. Wie habt ihr Round-Robin/Anycast im DNS erkannt (welche Resolver)?

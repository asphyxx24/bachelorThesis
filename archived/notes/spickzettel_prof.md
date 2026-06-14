# Spickzettel — meine BA in Stichpunkten (Prof-Gespräch & Erklären)

> Zweck: Ich kann damit meine komplette Arbeit frei erklären — vom 30-Sekunden-Pitch bis zu
> kritischen Rückfragen. In *meiner* Sprache, zum Vorlesen/Sprechen.
> Stand 2026-06-08 · Zahlen = Juni-Kampagne. Konfidenz-Marker: ✅ = aus Rohdaten bestätigt (3/3),
> ⚠️ = vor dem Termin final aus Tabelle prüfen.

---

## 0. Der 30-Sekunden-Pitch (für jeden, auch den Passanten)

- Ich messe, **wie schnell kommerzielle KI-Sprach-APIs** (Spracherkennung, Sprachmodell, Sprachausgabe) **aus Europa antworten** — und vor allem **warum** der eine schneller ist als der andere.
- **Überraschender Kernbefund:** Nicht die **geografische Nähe** entscheidet, sondern die **Rechen-Engine im Hintergrund**. Ein US-Anbieter (RTT 138 ms) schlägt einen EU-Anbieter (RTT 10 ms) klar — weil dessen Modell schneller rechnet.
- **Schönster Beweis:** *Derselbe* EU-Anbieter (Azure) **verliert** bei Spracherkennung und **gewinnt** bei Sprachausgabe. Gleicher Standort, gegensätzliches Ergebnis → es liegt **nicht** am Standort.
- **Beitrag:** Ich widerlege die naheliegende „näher = schneller"-Intuition mit kontrollierten Messungen und liefere die Methodik, *wann* Netzwerknähe die Latenz erklärt und *wann nicht*.

**Ein-Satz-Version:** *„Aus EU-Sicht dominiert im Kaltstart einer Voice-Pipeline die Backend-Engine die Latenz, nicht die Netzwerknähe — am schärfsten belegt durch die standort-invariante STT/TTS-Inversion desselben Providers."*

---

## 1. Was ich gemacht habe (das Setup)

- **9 kommerzielle Cloud-AI-APIs** in 3 Kategorien: STT (Spracherkennung), LLM (Sprachmodell), TTS (Sprachausgabe).
  - STT: Deepgram (US), Rev.ai (US), Azure (EU/Italien)
  - LLM: OpenAI (US), Groq (US-LPU), Mistral (EU)
  - TTS: Deepgram (US), OpenAI (US), Azure (EU)
- **Messpunkt:** AWS-Server in **Frankfurt** (eu-central-1) → konsistente EU-Perspektive.
- **Cold-Start:** Jede Messung baut eine **neue Verbindung** auf (kein Connection-Pooling) → misst den Overhead jeder *neuen* Gesprächssession.
- **Kampagne:** 1.–7. Juni 2026, **7 Tage × 8 Zeitschlitze/Tag = 56 Slots**, **n=100 pro Provider/Slot** → **50.400 Einzelmessungen**, **0 % fehlende Werte**. ✅
- **Drei Messschichten** (siehe Punkt 2) plus identische Eingaben pro Kategorie für faire Vergleiche.

---

## 2. Die drei Schichten (so erkläre ich die Methodik)

- **Layer 1 — Infrastruktur:** Was sagt das *Netzwerk allein*, ohne die API zu nutzen? **Ping (RTT), DNS, TLS-Version, Route/ASN.** → Wie weit weg, welches Protokoll, wer hostet.
- **Layer 2 — Pakete (PCAP):** **Mitschnitt der echten Datenpakete** beim Verbindungsaufbau. Zeigt *unabhängig*: TLS 1.2 vs 1.3, Anzahl der Handshake-RTTs, ob jemand hinter **Cloudflare** sitzt. → Meine **Gegenkontrolle**.
- **Layer 3 — API-Latenz:** Die APIs **wirklich aufrufen** und stoppen: `connect` (Verbindung steht), `ttft`/`ttfa` (erstes Token/Audio), `total`. → Die Latenz, die der **Nutzer spürt**.
- **Warum drei Schichten?** Layer 3 zeigt den *Effekt* (wer ist schnell), Layer 1+2 liefern den *Beweis*, dass es **nicht** am Netzwerk liegt. Das ist mein Methoden-Kern.

---

## 3. Der Kernbefund + das ganze „Warum" (Engine schlägt Geografie)

**Befund in einem Satz:** Aus EU-Sicht erklärt die Netzwerknähe die wahrgenommene Latenz **gerade nicht** — die Backend-Engine dominiert. Belegt durch fünf zusammenhängende Pfeiler:

1. **STT — US schlägt EU:** Deepgram (US, RTT 138 ms) liefert erstes Token nach **~575 ms**, Azure (EU, RTT 10 ms) erst nach **~1715 ms** — in **56/56 Slots**, ohne Überlappung. ✅
   - Zerlegung: Azure spart **~130 ms Netzwerk**, verliert aber **~1130 ms** durch die langsamere Engine. → Netzwerkvorteil wird von der Verarbeitung *aufgefressen*.
2. **TTS — die Inversion (mein bester Beweis):** *Derselbe* Azure gewinnt jetzt: ttfa **~67 ms** vs Deepgram **~557 ms** vs OpenAI **~954 ms**. ✅
   - Pointe: Gleicher Standort, gleiche RTT, **gegensätzliches Ergebnis** → es kann nicht die Region sein, es ist die Engine. Das ist ein *natürliches Experiment*, keine bloße Korrelation.
3. **Zerlegung (das „Warum"):** Ich trenne pro Anfrage Netzwerk- von Verarbeitungsanteil. → zeigt, dass der Netzwerkanteil real, aber klein ist.
4. **Cloudflare-Grenze:** 4/9 Provider sitzen hinter Cloudflare (Frankfurt-Edge, RTT ~1 ms) → dort *kann* reine Netzwerkmessung den Backend-Anteil gar nicht mehr sehen. Das markiert die **Gültigkeitsgrenze** der Netzwerk-Erklärung. ✅
5. **Datenqualität + echter Cold-Start:** 0 % fehlende Werte, n=100 exakt, und ich *beweise*, dass der Cold-Start echt ist (connect-Zeit bleibt über die 100 Läufe flach → keine Verbindungs-Wiederverwendung). ✅

---

## 4. Warum das mehr ist als ein Benchmark (meine Contribution)

- **C1 (Kern):** Empirische, kontraintuitive **Widerlegung** der „näher = schneller"-Intuition — quantifiziert, nicht behauptet.
- **C2:** Eine **dreischichtige Zerlegungs-Methodik** (Connect/TLS/Cold-Start), die Industrie-Benchmarks (z. B. Artificial Analysis) so **nicht** leisten — die messen nur end-to-end inkl. Netz, ohne Vantage-Point-Kontrolle. Plus Cloudflare-Fronting als Gültigkeitsgrenze.
- **C3 (Methoden-Baustein):** Eine **kostenlose Heuristik** — aus einem simplen Layer-1-Ping kann ich die connect-Latenz**klasse** der direkt-gehosteten Provider vorhersagen (ohne teure API-Calls). *Bewusst klein gehalten, n=4 als Limitation.*
- **Warum für einen Netzwerk-Lehrstuhl relevant:** RTT/Geografie ist *das* Lieblings-Erklärmuster — und ich zeige kontrolliert, dass es hier *nicht* greift. Eine Hypothesen-Widerlegung ist wissenschaftlich mehr wert als ein bestätigendes Ranking.

---

## 5. Die Zahlen, die ich parat habe

| Kategorie | Provider | RTT | Hauptmetrik | Konfidenz |
|---|---|---|---|---|
| STT | Deepgram (US) | 138 ms | ttft ~575 ms | ✅ |
| STT | Azure (EU) | 10 ms | ttft ~1715 ms | ✅ |
| STT | Rev.ai (US) | ~144 ms | ttft ~1420 ms; TLS 1.2 → **+153 ms** Penalty (connect-Counterfactual; ~144 ms reine TLS-RTT) | ✅ |
| TTS | Azure (EU) | 10 ms | ttfa ~67 ms (gewinnt) | ✅ |
| TTS | Deepgram (US) | 138 ms | ttfa ~557 ms | ✅ |
| TTS | OpenAI (US) | ~1 ms | ttfa ~954 ms | ✅ |
| LLM | Groq (US-LPU) | ~1 ms | ttft **~68 ms** (schnellster), aber ~33 % 429-Fehler | ✅ |
| LLM | Mistral (EU) | ~1 ms | ttft **~231 ms** | ✅ |
| LLM | OpenAI (US) | ~1 ms | ttft **~542 ms** (langsamster der drei) | ✅ |

- **Cross-Layer-Heuristik:** connect ≈ N_RTTs × ping + k, **slope 1.006, k 10.7 ms** (4 direkte Provider). ⚠️ *r bewusst nicht als Gütemaß nennen.*
- **E2E (Streaming, Kaltstart):** beste Kombi deepgram+groq+azure **~1134 ms**; **0/27** Kombis unter 1 s; mit warmen Verbindungen ~666 ms. ⚠️ *= Median-Addition, nicht echt gemessen — siehe Limitationen.*
- **Sicherheit:** DNSSEC bei **0/6** Zonen aktiv.

---

## 6. Methodik-Entscheidungen, die ich begründen kann (gegen „Methodik unklar")

- **Warum Cold-Start?** Misst den Overhead *jeder neuen* Gesprächssession (Serverless, nach Inaktivität, erster Turn). Warm-Verhalten = Future Work. **Empirisch belegt echt** (flache connect-Zeit über 100 Läufe).
- **connect_ms misst bei STT vs LLM/TTS *Verschiedenes*** (wichtig, ehrlich!): bei STT am echten In-Pfad-WebSocket (connect-*exklusiv*), bei LLM/TTS an einem Wegwerf-Socket (connect-*inklusiv*). → Ich vergleiche quer nur „**user-perceived Cold-Start**" (STT = connect+ttft, LLM/TTS = ttft/ttfa), **nie rohes connect_ms**.
- **STT als Audio-Dump** (kein Real-Time-Pacing) gemessen — das deklariere ich **offen** und rechne, wie sich der STT-Anteil ändert, wenn STT parallel zum Sprechen liefe.
- **Raw-WebSocket ohne SDK** bei allen STT → identische Messbedingungen, kein SDK-Overhead-Bias.
- **Identische Eingaben** pro Kategorie → fairer Vergleich.

---

## 7. Was ich SELBST kritisch sehe (Limitationen — ich nenne sie zuerst)

- **E2E nie als echte Pipeline gemessen** → aktuell Median-Addition; nachgeschärft per Monte-Carlo; *ein echter Lauf ist als Validierung geplant.*
- **Cross-Layer-Heuristik: nur n=4 Punkte**, N_RTTs aus dem Protokoll begründet (nicht aus dem Fit). Deshalb Methoden-Baustein, nicht Hauptbefund.
- **Region/Engine perfekt konfundiert** (n=1 EU-Provider pro Kategorie) → ich mache eine **Anteils**-, keine strenge Kausalaussage.
- **1-Sekunden-Budget** ist eine pragmatische Obergrenze; die Konversations-Literatur nennt 200–300 ms (ordne ich ein).
- **Layer-2-PCAP**: andere Instanz/Tag, n=1 → nur für **Struktur** (TLS-Version, Fronting, RTT-Anzahl), nicht für Absolutzeiten.
- **7 statt geplant 14 Tage**; nur Cold-Start; Deepgram-Anycast.

---

## 8. Erwartete Prof-Fragen → meine Antwort

- **„Was genau messen Sie?"** → Drei Schichten: Netzwerk allein (L1), Pakete (L2), echte API-Latenz (L3). Kernmetriken: connect, time-to-first-token/audio, total. Cross-validiert über die Schichten.
- **„Warum Cold-Start?"** → Overhead jeder neuen Session; relevant für Serverless & ersten Turn; warm = Future Work; und ich belege, dass es echter Cold-Start ist.
- **„Was ist die Contribution?"** → Die quantifizierte Widerlegung „Engine > Geografie" + die Zerlegungs-Methodik, die zeigt, *wann* Netzwerkmessung die Latenz erklärt und wo (Cloudflare) nicht.
- **„Ist ‚Engine schlägt Netzwerk' nicht offensichtlich?"** → (Wichtigste Frage!) Nein: ich habe es **quantifiziert** (130 ms Netz gespart vs 1130 ms Engine verloren), habe das **saubere Experiment** (Azure kippt zwischen STT/TTS) und **zerlege**, *wo* das Netzwerk doch zählt. Das ist „gemessen & eingegrenzt", nicht „weiß man".
- **„Validierung?"** → Layer-2-PCAP + Cross-Vantage-Reproduktion (8/9 <1 ms) + 0 % NaN; *plus geplanter echter E2E-Lauf*.
- **„Warum r=0.999 bei nur 4 Punkten?"** → Stimmt, deshalb ist das Modell ein **Methoden-Baustein** mit offener n=4-Limitation; ich argumentiere mit dem kleinen Residualfehler und der PCAP-Submetrik-Zerlegung, **nicht** mit r.
- **„Warum nur 9 Provider?"** → Kostenlimit + methodische Konsistenz (alle identisch, alle Cold-Start, alle Raw-WebSocket).

---

## 9. Wo ich gerade stehe / nächste Schritte

- **Datenanalyse fertig** (8 Notebooks, ~19 Figures, 7 Tabellen), Befunde aus Rohdaten **unabhängig bestätigt** (9/12 Claims).
- **Reframe gemacht:** Engine>Region als Kern, Cross-Layer-Modell zum Baustein degradiert.
- **Offen:** (1) Stale-Zahlen in Doku synchronisieren, (2) Fließtext schreiben — Methodik zuerst, (3) optional ein echter E2E-Validierungslauf.
- **Schreibstand: Prosa steht noch aus** — das ist die Hauptarbeit der nächsten Wochen.

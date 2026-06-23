# Modul 9 — STT `ttfp` + 1×-Pacing ⭐

**Ziel:** Erklären, warum die naheliegende STT-Metrik (`ttft`) unfair ist, womit du sie ersetzt (`ttfp`), warum dazu zwingend Echtzeit-Pacing gehört, und die ehrlichen Grenzen.

## 9.1 Begriffe

- **Partial / Interim:** vorläufige Wort-Vermutung *während* des Sprechens (Live-Untertitel).
- **Final:** endgültiges Transkript, wenn die Engine ein Segment für abgeschlossen hält.
- **Endpointing / Finalisierung:** die Entscheidung *wann* final — meist über Stille-Erkennung.

## 9.2 Das Problem: `ttft` ist unfair

`ttft` = *Time to First **Final***. *Wann* ein Anbieter „final" sagt, hängt von seiner **Finalisierungs-Politik** ab — und die drei finalisieren unterschiedlich. `ttft` mischt also **Engine-Geschwindigkeit** (gewollt) + **Endpointing-Politik** (ungewollt) → als Engine-Vergleich unbrauchbar.

## 9.3 Die Azure-Korrektur (Lehrstück in Ehrlichkeit)

Im Dump war Azures `ttft` konstant ~1722 ms. Erste Deutung: „festes Stille-Fenster" — **falsch**. Im Dump kam das ganze Audio auf einmal (**Bulk-Compute**); die 1722 ms waren Verarbeitungszeit, kein Timer. Unter Pacing finalisiert Azure ~98 ms nach dem letzten Audio-Byte. → Alte „Azure verliert STT"-These **gestrichen** (Mess-Artefakt). Deshalb trägt STT C1 nicht — selbst aufgedeckt = Vertrauens-Plus.

## 9.4 Die Lösung: `ttfp`

`ttfp` = *Time to First **Partial*** — Zeit bis zum ersten Live-Wort, **vor** jeder Finalisierung → **endpointing-frei**. Symmetrisch zu LLM-`ttft` (erstes Token) und TTS-`ttfa` (erstes Audio). `ttft` bleibt **sekundär** (= Stream-Ende-Final).

## 9.5 Warum 1×-Realtime-Pacing zwingend ist

*Pacing* = Audio im 1×-Echtzeit-Takt streamen (~128 ms/Chunk), Senden + Empfangen parallel. Im Dump-Modus liefert **Deepgram vor dem Final kein Partial** → kein `ttfp` vergleichbar. Nur bei echtzeit-eintreffendem Audio liefern **alle drei** echte Interims (verifiziert: 25/25 erstes Wort = Interim).

## 9.6 Das Ergebnis

| Anbieter | RTT | `ttfp` |
|----------|-----|--------|
| Azure (EU) | ~11 ms | **~1045 ms** |
| Deepgram (US) | ~142 ms | **~1046 ms** |
| Rev.ai (US) | ~140 ms | ~1494 ms |

Azure ≈ Deepgram → Azure ist *nicht* der langsamste.

## 9.7 Drei ehrliche Grenzen

1. **Pacing-Floor dominiert:** `ttfp ≈ ~0,8 s (gemeinsam) + ~1 RTT + Engine-Reaktion`. Der Floor kürzt sich in Provider-Differenzen heraus → Indikator „reagiert zügig", kein feines Ranking.
2. **Kaum geografie-sensitiv** → erklärt, warum Azure (11 ms) und Deepgram (142 ms) dasselbe `ttfp` haben.
3. **Emissions-Kadenz** = Anbieter-Politik, nicht reine Engine-Zeit.

## 9.8 Der In-Band-RTT

`ttfp` enthält bauartbedingt **~1 Netz-Roundtrip** (Audio raus → Interim zurück) + Engine-Reaktion → keine reine Rechenzeit. Aber: der RTT-Anteil ist aus Layer 1 **bekannt** (Edge ~1 ms, US ~140 ms) und **abziehbar**. Antwort auf die Prüfer-Falle: „Ja, genau ein Roundtrip — den kenne ich aus Layer 1 und trenne ihn ab."

## Prüf-Fragen

1. Warum ist `ttft` für STT unfair — welche zwei Dinge mischt es?
2. Was bringt 1×-Pacing — was würde im Dump-Modus schiefgehen?
3. Warum sind Azure und Deepgram auf `ttfp` gleichauf, obwohl Deepgram 13× weiter weg ist?
4. `ttfp` enthält einen Netz-Roundtrip — wie trennst du trotzdem Netz von Backend?

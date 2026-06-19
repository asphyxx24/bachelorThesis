# STT-Eingabe (`sample.wav`)

Fester STT-Input für **alle** Messungen (referenziert in `measurements/layer3/config.py` → `STT_WAV`).

- **Format:** 16 kHz, Mono, 16-bit PCM (RIFF/WAV), ca. 4,84 s (77.462 Frames, eigene Messung 2026-06-19).
  Vorlauf-Stille nur **~8 ms** (Sound-Onset bei Frame 135) → kein nennenswerter additiver `ttfp`-Sockel
  (die im Audit vermuteten ~400 ms reproduzieren nicht).
- **Text:** „Good morning. I would like to know the current weather forecast for Frankfurt."
- **Herkunft:** übernommen aus dem alten Lauf (`archived/measurements/layer3/sample.wav`,
  validiert 2026-05-03 mit Deepgram, `transcript_len > 0`).

> ⚠️ **Provenienz-Caveat (A14):** Ob die Aufnahme menschlich oder TTS-generiert ist, ist **nicht**
> dokumentiert. Für die **Latenz**-Messung (`ttft`) irrelevant — der Inhalt zählt dort nicht. Für eine
> spätere **WER**-Analyse relevant: eine TTS-generierte Referenz wäre zirkulär. Vor einer WER-Auswertung
> daher entweder die Herkunft klären oder eine menschliche Referenzaufnahme verwenden und
> Normalisierungsregeln (Casing/Punctuation — Deepgram `punctuate=true` vs. Azure) festlegen.

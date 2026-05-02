# fixtures/sample.wav

Diese Datei muss manuell erstellt werden bevor die STT-Messungen starten.

## Anleitung

1. Auf dem PC eine Sprachaufnahme machen (~5 Sekunden, ruhige Umgebung)
2. Folgenden Satz auf Englisch sprechen:

   > "Good morning. I would like to know the current weather forecast for Frankfurt."

3. Die Aufnahme als WAV speichern (z.B. `recording.wav`)
4. In das richtige Format konvertieren:

   ```
   ffmpeg -i recording.wav -ar 16000 -ac 1 fixtures/sample.wav
   ```

5. Validieren: Testlauf mit Deepgram → `transcript_len > 0`

## Format-Anforderungen

- 16 kHz Sample Rate
- Mono (1 Kanal)
- 16-bit PCM
- WAV-Container
- Dauer: ca. 5 Sekunden

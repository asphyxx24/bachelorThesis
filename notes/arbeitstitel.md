# Arbeitstitel (Stand 2026-06-22)

Kandidaten zum Vorlegen bei Betreuer/Zweitprüfer. Arbeitstitel ist nicht angemeldet, frei änderbar.
Diese drei sollen Prof. Wählisch vorgelegt werden (Mail-**Entwurf** in `waehlisch_titel_mail.md`,
**noch nicht versendet**). Gemeinsame Linie: neutral-deskriptiv, kein Overclaim, Rigor- statt
Behauptungs-Signal — die verteidigbare Aussage ist die *negative* („Netznähe erklärt die Latenzspreizung
nicht"), nicht „Engine/Backend dominiert" (Modellgrößen-Confound). Darum taucht „Engine" in keinem Titel auf.

> **Änderung 2026-06-22:** Der frühere Favorit „**Gleicher Edge, andere Latenz: …**" wurde **gestrichen**
> (s. Begründung unten). „Gleicher Edge" verallgemeinert einen Spezialfall: Nur **4 von 9** Endpunkten
> terminieren am selben Cloudflare-Edge (die 3 LLMs OpenAI/Groq/Mistral + OpenAI-TTS, AS13335, ~1 ms). Die
> übrigen 5 liegen real unterschiedlich weit weg (Deepgram STT+TTS ~140 ms US, rev.ai STT ~140 ms US, Azure
> STT+TTS ~11 ms EU-RZ). Die „identische Edge"-Pointe ist der **schärfste C1-Beleg auf der LLM-Achse**, aber
> **keine Eigenschaft des ganzen Anbietersets** → gehört ins Abstract/Ergebnis-Kapitel, nicht in den
> Gesamttitel. Belege: `data/audit_20260618/{l1_rtt_per_ip.md, asn_per_ip.md}`. Neuer Favorit = die offene
> Frage (kann nicht überziehen, gilt für alle 9 Endpunkte, deckt sich mit der Forschungsfrage).

## Favorit — offene Frage (kann nicht überziehen)

**Erklärt Netznähe die Latenzunterschiede? Eine drei-schichtige Messstudie zu Cloud-AI-Sprachdiensten
(STT, LLM, TTS) aus EU-Sicht**

- Reine Frageform, deckt sich exakt mit der Forschungsfrage; **null Overclaim-Angriffsfläche** und gilt für
  **alle 9** Endpunkte (nicht nur die LLM-Achse).
- Motiviert die Drei-Schichten-Methodik von selbst (die Frage *ist* die Zerlegung in Netz vs. Backend).
- Der neutralste Kandidat — auch im Exposé als vorläufiger Arbeitstitel verwendet.

## Alternative 1 — neutral-deskriptiv

**Kommerzielle Cloud-AI-APIs unter der Lupe: Eine Drei-Schichten-Latenzanalyse einer Voice-Pipeline
(Cold-Start) aus EU-Sicht**

- Rein beschreibend, kein Ergebnis-Anspruch; nennt Gegenstand (Cloud-AI-APIs, Voice-Pipeline), Methode
  (Drei-Schichten-Latenzanalyse) und Perspektive (EU). „Echtzeit" → „Cold-Start" korrigiert (gemessen wird
  der Cold-Start, kein Warmbetrieb).
- **„paket-validiert" aus dem Titel entfernt (2026-06-22):** Es gilt streng nur für den Connect-Timer
  (Audit H2), nicht für `ttft`/`ttfa` (die den Kernbefund tragen) → im Titel ein Overclaim gegenüber einem
  Netzwerk-/Methoden-Prüfer. Das Rigor-Signal gehört in den Methodik-Text, nicht in den Titel.

## Alternative 2 — Methoden-Rigor

**Eine Drei-Schichten-Methodik zur Cold-Start-Latenzmessung kommerzieller STT-, LLM-
und TTS-Dienste aus EU-Perspektive**

- Rückt die Drei-Schichten-Cold-Start-Methodik als eigenständigen Beitrag (C2) nach vorn; Mess-Rigor ganz
  ohne Ergebnisbehauptung. („paket-validiert" auch hier entfernt — H2, s. Alternative 1.)
- Risiko: der inhaltliche Negativbefund taucht im Titel nicht auf und muss im Abstract nachgeliefert werden.

> **Falls die „Edge"-Pointe doch in den Titel soll:** nur **LLM-eingeschränkt** formulieren, z. B. als
> Untertitel-Zusatz „… — am Beispiel dreier LLM-APIs an identischem Cloudflare-Edge". Niemals als
> verallgemeinerte Set-Eigenschaft. Default bleibt: Pointe ins Abstract, Titel neutral.

---

### Referenz: frühere Platzhalter (nicht mehr aktiv)

- „Gleicher Edge, andere Latenz: Eine schichtenweise, paket-validierte Latenzmessung kommerzieller
  Cloud-AI-APIs (STT, LLM, TTS) aus EU-Perspektive" (Favorit bis 2026-06-22 — gestrichen, „gleicher Edge"
  überzieht: nur 4/9 Endpunkte, s. Begründung oben)
- „Kommerzielle Cloud-AI-APIs unter der Lupe: Netzwerk-, Protokoll- und Latenzanalyse einer
  Echtzeit-Voice-Pipeline" (ursprünglicher Platzhalter)
- „Engine schlägt Geografie: …" (frühere Identität — wegen Modellgrößen-Confound nicht mehr im Titel)

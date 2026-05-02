"""One-shot: split Requesty-Records aus data/layer3/*.jsonl in deprecated_requesty/.

Hintergrund: Requesty-Daten stammen von einem API-Proxy (Gemini 2.5 Flash), nicht von
den finalen LLM-Providern (OpenAI/Groq/Anthropic). Für die Thesis nicht verwendbar.

Input:  data/layer3/*.jsonl          — gemischte Records aller APIs
Output: data/layer3/<file>.jsonl      — ohne Requesty-Records (überschrieben)
        data/layer3/deprecated_requesty/<file>.jsonl — nur Requesty-Records
"""
import json
from pathlib import Path

LAYER3 = Path("data/layer3")
DEPRECATED = LAYER3 / "deprecated_requesty"
DEPRECATED.mkdir(exist_ok=True)

files = sorted(p for p in LAYER3.glob("*.jsonl") if p.parent == LAYER3)
total_in = total_req = total_kept = 0

for src in files:
    req_lines, kept_lines = [], []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total_in += 1
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            kept_lines.append(line)
            continue
        if rec.get("api") == "requesty":
            req_lines.append(line)
            total_req += 1
        else:
            kept_lines.append(line)
            total_kept += 1

    if req_lines:
        (DEPRECATED / src.name).write_text("\n".join(req_lines) + "\n", encoding="utf-8")
    src.write_text(("\n".join(kept_lines) + "\n") if kept_lines else "", encoding="utf-8")

print(f"Files processed: {len(files)}")
print(f"Records in:      {total_in}")
print(f"Requesty moved:  {total_req}")
print(f"Kept in layer3:  {total_kept}")

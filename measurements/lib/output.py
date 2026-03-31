"""JSONL-Output und Pfad-Management.

Alle Messergebnisse werden als JSONL (JSON Lines) gespeichert.
Output-Verzeichnis: data/{layer}/ im Repo-Root.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Repo-Root/data/ — funktioniert lokal und auf EC2
REPO_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "data"


def output_path(layer: str, tag: str = "", mode: str = "") -> Path:
    """Gibt den JSONL-Ausgabepfad fuer eine Messsitzung zurueck.

    Beispiele:
      output_path("layer1", mode="background")  -> data/layer1/2026-04-01_0900_background.jsonl
      output_path("layer3", tag="09h")           -> data/layer3/2026-04-01_09h.jsonl
    """
    ts = datetime.now()
    date = ts.strftime("%Y-%m-%d")
    hhmm = ts.strftime("%H%M")

    layer_dir = DATA_DIR / layer
    layer_dir.mkdir(parents=True, exist_ok=True)

    if tag:
        filename = f"{date}_{tag}.jsonl"
    elif mode:
        filename = f"{date}_{hhmm}_{mode}.jsonl"
    else:
        filename = f"{date}_{hhmm}.jsonl"

    return layer_dir / filename


def write_jsonl(path: Path, record: dict) -> None:
    """Haengt einen Record als JSONL-Zeile an die Datei an."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def now_iso() -> str:
    """Aktuelle Zeit als ISO-8601-String (UTC)."""
    return datetime.now(timezone.utc).isoformat()

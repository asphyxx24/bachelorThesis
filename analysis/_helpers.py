"""Gemeinsame Helfer fuer alle Analyse-Notebooks.

Aufgaben:
- Datenladen aus data/processed/ (mit korrekten Pfaden relativ zum Repo-Root)
- Provider <-> Endpoint Mapping fuer Cross-Layer-Joins
- Einheitliche Farbpalette pro Provider
- Konsistente Plot-/Export-Helfer (PNG + PDF gleichzeitig)
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# Repo-Root (zwei Ebenen ueber dieser Datei: analysis/_helpers.py -> repo)
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
FIGURES_DIR = REPO_ROOT / "analysis" / "figures"
TABLES_DIR = REPO_ROOT / "analysis" / "tables"

# Sicherstellen dass Output-Ordner existieren
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Provider-Map: (Kategorie, API-Name) -> Endpoint-Hostname
# Joinschluessel fuer Cross-Layer-Analysen (Layer 1 endpoint <-> Layer 3 api)
# --------------------------------------------------------------------------
PROVIDER_TO_ENDPOINT: dict[tuple[str, str], str] = {
    ("STT", "deepgram"): "api.deepgram.com",
    ("STT", "revai"):    "api.rev.ai",
    ("STT", "azure"):    "italynorth.stt.speech.microsoft.com",
    ("LLM", "openai"):   "api.openai.com",
    ("LLM", "groq"):     "api.groq.com",
    ("LLM", "mistral"):  "api.mistral.ai",
    ("TTS", "deepgram"): "api.deepgram.com",
    ("TTS", "openai"):   "api.openai.com",
    ("TTS", "azure"):    "italynorth.tts.speech.microsoft.com",
}

# Erwartete Region (fuer Tabellen / Plot-Labels)
PROVIDER_REGION: dict[tuple[str, str], str] = {
    ("STT", "deepgram"): "USA (Anycast)",
    ("STT", "revai"):    "USA",
    ("STT", "azure"):    "Italy North",
    ("LLM", "openai"):   "USA",
    ("LLM", "groq"):     "USA (LPU)",
    ("LLM", "mistral"):  "EU/Frankreich",
    ("TTS", "deepgram"): "USA (Anycast)",
    ("TTS", "openai"):   "USA",
    ("TTS", "azure"):    "Italy North",
}

# Einheitliche Farbe pro Provider — wiedererkennbar ueber alle Plots hinweg
PROVIDER_COLORS: dict[str, str] = {
    "deepgram": "#1f77b4",  # blau
    "revai":    "#ff7f0e",  # orange
    "azure":    "#2ca02c",  # gruen
    "openai":   "#d62728",  # rot
    "groq":     "#9467bd",  # lila
    "mistral":  "#8c564b",  # braun
}


# --------------------------------------------------------------------------
# Lader fuer die processed-Daten
# --------------------------------------------------------------------------
def load_layer3(category: str) -> pd.DataFrame:
    """Lade Layer-3-Daten ('stt', 'llm', 'tts' oder 'errors')."""
    path = DATA_PROCESSED / f"layer3_{category}.parquet"
    return pd.read_parquet(path)


def load_layer1(kind: str) -> pd.DataFrame:
    """Lade Layer-1-Daten ('ping', 'dns', 'tls', 'traceroute').

    Parst ts/date als datetime wo vorhanden.
    """
    path = DATA_PROCESSED / f"layer1_{kind}.csv"
    df = pd.read_csv(path)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    return df


# --------------------------------------------------------------------------
# Plot-Export
# --------------------------------------------------------------------------
_TOPIC_DIRS = {
    "01": "01_layer1",
    "02": "02_pcap",
    "03": "03_stt",
    "04": "04_llm",
    "05": "05_tts",
    "06": "06_cross_layer",
    "07": "07_e2e",
}


def save_figure(fig, name: str) -> None:
    """Speichert ein Figure als PNG + PDF in figures/<topic>/png/ bzw. pdf/.

    Konvention: 'name' ohne Extension, mit Notebook-Praefix
    (z.B. '04_llm_ttft_violin' → figures/04_llm/png/ + pdf/).
    """
    prefix = name[:2]
    topic = _TOPIC_DIRS.get(prefix, "misc")
    for ext in ("png", "pdf"):
        out = FIGURES_DIR / topic / ext / f"{name}.{ext}"
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches="tight", dpi=150)
    print(f"  saved figures/{topic}/{{png,pdf}}/{name}")


def save_table(df: pd.DataFrame, name: str, **csv_kwargs) -> None:
    """Speichert eine Tabelle als CSV in analysis/tables/.

    Index wird per Default mitgeschrieben — fuer Provider-aggregierte Tabellen
    nuetzlich. Override via csv_kwargs={'index': False}.
    """
    out = TABLES_DIR / f"{name}.csv"
    csv_kwargs.setdefault("index", True)
    df.to_csv(out, **csv_kwargs)
    print(f"  saved tables/{name}.csv")

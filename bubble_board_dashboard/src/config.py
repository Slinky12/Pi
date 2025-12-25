from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; env vars still work
    pass


DEFAULT_COLUMNS = [
    "Category",
    "Project / Item",
    "Current Status",
    "Start Date",
    "Target End Date",
    "Estimated Cost ($)",
    "Dependencies / Prerequisites",
    "Next Action",
    "Priority",
]


@dataclass
class Settings:
    # Spreadsheet
    xlsx_path: str
    sheet_name: Optional[str] = None
    required_columns: List[str] = field(default_factory=lambda: DEFAULT_COLUMNS.copy())

    # Priority
    priority_min: int = 1
    priority_max: int = 5

    # UI
    refresh_seconds: int = 60
    bubble_columns: int = 3

    # Stocks
    tickers: List[str] = field(default_factory=lambda: ["VOO", "VOOG", "ORCL", "PLTR"])
    stock_ttl_seconds: int = 300

    # AI (DeepSeek on your desktop)
    ai_base_url: str = "http://127.0.0.1:11434/v1"  # OpenAI-compatible; Ollama uses 11434
    ai_model: str = "deepseek-r1:7b"
    ai_api_key: str = ""  # some servers ignore this; keep blank if not needed
    ai_timeout_seconds: int = 60


def _normalize_candidate_paths(candidates: List[str]) -> List[str]:
    out = []
    for p in candidates:
        if not p:
            continue
        # Expand ~ and env vars
        p2 = os.path.expandvars(os.path.expanduser(p))
        # If user gave "home/..." missing leading slash, also try "/home/..."
        if not p2.startswith("/") and p2.startswith("home/"):
            out.append("/" + p2)
        out.append(p2)
    # de-duplicate preserving order
    seen = set()
    uniq = []
    for p in out:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def load_settings() -> Settings:
    # Your provided path had common casing/leading-slash issues, so we try a few.
    base_dir = os.getenv("BUBBLE_BASE_DIR", "/home/slinky/Desktop/bubble_board")
    xlsx_name = os.getenv("BUBBLE_XLSX_NAME", "projects.xlsx")

    candidates = _normalize_candidate_paths([
        os.getenv("BUBBLE_XLSX_PATH", ""),
        str(Path(base_dir) / xlsx_name),
        str(Path(base_dir.lower()) / xlsx_name),
        "home/slinky/desktop/bubble_board/projects.xlsx",
        "/home/slinky/desktop/bubble_board/projects.xlsx",
        "/home/slinky/Desktop/bubble_board/projects.xlsx",
    ])

    xlsx_path = None
    for c in candidates:
        if Path(c).exists():
            xlsx_path = c
            break
    # If none exist, default to first candidate (so UI shows what it expects)
    if xlsx_path is None:
        xlsx_path = candidates[0] if candidates else str(Path(base_dir) / xlsx_name)

    sheet_name = os.getenv("BUBBLE_SHEET", None)
    refresh_seconds = int(os.getenv("BUBBLE_REFRESH_SECONDS", "60"))
    bubble_columns = int(os.getenv("BUBBLE_COLUMNS", "3"))

    ai_base_url = os.getenv("AI_BASE_URL", "http://127.0.0.1:11434/v1")
    ai_model = os.getenv("AI_MODEL", "deepseek-r1:7b")
    ai_api_key = os.getenv("AI_API_KEY", "")
    ai_timeout = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    tickers = os.getenv("TICKERS", "VOO,VOOG,ORCL,PLTR").split(",")
    tickers = [t.strip().upper() for t in tickers if t.strip()]

    stock_ttl = int(os.getenv("STOCK_TTL_SECONDS", "300"))

    return Settings(
        xlsx_path=xlsx_path,
        sheet_name=sheet_name,
        refresh_seconds=refresh_seconds,
        bubble_columns=bubble_columns,
        tickers=tickers,
        stock_ttl_seconds=stock_ttl,
        ai_base_url=ai_base_url,
        ai_model=ai_model,
        ai_api_key=ai_api_key,
        ai_timeout_seconds=ai_timeout,
    )

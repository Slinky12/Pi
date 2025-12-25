from flask import Flask, render_template
import pandas as pd
from pathlib import Path
import os
import math

APP = Flask(__name__)

# Set this to your file path, or export SPREADSHEET_PATH in your shell
SPREADSHEET_PATH = os.environ.get("SPREADSHEET_PATH", str(Path.home() / "bubble_board" / "projects.xlsx"))

COLUMNS = [
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

def _clean_str(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x).strip()

def _priority_key(p):
    """
    Supports:
      - High/Medium/Low (case-insensitive)
      - numeric priorities (1 is highest)
    """
    s = _clean_str(p).lower()
    mapping = {"high": 1, "h": 1, "medium": 2, "med": 2, "m": 2, "low": 3, "l": 3}
    if s in mapping:
        return mapping[s]
    # numeric?
    try:
        return int(float(s))
    except Exception:
        return 999  # unknown = lowest

def _read_sheet(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Spreadsheet not found at: {p}")

    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    elif p.suffix.lower() in [".xlsx", ".xlsm", ".xls"]:
        df = pd.read_excel(p)
    else:
        raise ValueError("Unsupported file type. Use .xlsx or .csv")

    # Ensure required columns exist (create empty if missing)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS].copy()

    # Normalize strings
    for col in COLUMNS:
        df[col] = df[col].apply(_clean_str)

    # Parse dates if possible (keeps display clean)
    for dcol in ["Start Date", "Target End Date"]:
        parsed = pd.to_datetime(df[dcol], errors="coerce")
        df[dcol] = parsed.dt.strftime("%Y-%m-%d").fillna(df[dcol])

    # Sort: Priority first, then Category, then Target End Date, then Project / Item
    df["_prio"] = df["Priority"].apply(_priority_key)
    df["_target"] = pd.to_datetime(df["Target End Date"], errors="coerce")

    df = df.sort_values(by=["_prio", "Category", "_target", "Project / Item"], ascending=[True, True, True, True])
    df = df.drop(columns=["_prio", "_target"])

    return df

@APP.route("/")
def index():
    try:
        df = _read_sheet(SPREADSHEET_PATH)
        items = df.to_dict(orient="records")
        error = None
    except Exception as e:
        items = []
        error = str(e)

    return render_template("index.html", items=items, error=error, sheet_path=SPREADSHEET_PATH)

if __name__ == "__main__":
    # host=0.0.0.0 lets other devices on your Wi-Fi open it
    APP.run(host="0.0.0.0", port=5000, debug=True)

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


def _coerce_date(series: pd.Series) -> pd.Series:
    # Handles Excel dates, strings, blanks
    return pd.to_datetime(series, errors="coerce").dt.date


def load_tasks(
    xlsx_path: str,
    sheet_name: Optional[str],
    required_columns: List[str],
) -> Tuple[pd.DataFrame, Optional[str]]:
    path = Path(xlsx_path)
    if not path.exists():
        return pd.DataFrame(), f"Spreadsheet not found at: {xlsx_path}"

    try:
        # If sheet_name not provided, pandas reads first sheet by default
        df = pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        return pd.DataFrame(), f"Failed to read xlsx: {e}"

    # Normalize columns
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        return pd.DataFrame(), (
            "Missing required columns in your sheet:\n"
            + "\n".join([f"- {m}" for m in missing])
            + "\n\nTip: make sure your headers match exactly (including spaces and slashes)."
        )

    # Keep only needed columns, but preserve order
    df = df[required_columns].copy()

    # Clean up and typing
    df["Priority"] = pd.to_numeric(df["Priority"], errors="coerce")
    df["Estimated Cost ($)"] = pd.to_numeric(df["Estimated Cost ($)"], errors="coerce")

    df["Start Date"] = _coerce_date(df["Start Date"])
    df["Target End Date"] = _coerce_date(df["Target End Date"])

    # Provide stable row id
    df["_row_id"] = range(1, len(df) + 1)

    # Fill NaNs for display
    for col in required_columns:
        df[col] = df[col].fillna("")

    # Sort: Priority asc (1 highest), then Target End Date, then Start Date, then Category
    # Handle blanks by pushing to bottom.
    df["_p_sort"] = df["Priority"].where(df["Priority"] != "", other=None)
    df["_p_sort"] = pd.to_numeric(df["_p_sort"], errors="coerce")

    df["_tend_sort"] = pd.to_datetime(df["Target End Date"], errors="coerce")
    df["_start_sort"] = pd.to_datetime(df["Start Date"], errors="coerce")

    df = df.sort_values(
        by=["_p_sort", "_tend_sort", "_start_sort", "Category", "Project / Item"],
        ascending=[True, True, True, True, True],
        na_position="last",
    ).reset_index(drop=True)

    return df, None

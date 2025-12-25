from __future__ import annotations
from datetime import date
from typing import Dict, Tuple

import pandas as pd
import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
          /* Page background */
          .stApp {
            background: radial-gradient(1200px 700px at 20% 10%, rgba(90, 156, 255, 0.18), rgba(0,0,0,0)),
                        radial-gradient(900px 600px at 85% 20%, rgba(170, 90, 255, 0.14), rgba(0,0,0,0)),
                        radial-gradient(800px 500px at 50% 90%, rgba(90, 255, 190, 0.10), rgba(0,0,0,0));
          }

          /* Bubble cards */
          .bubble {
            border-radius: 24px;
            padding: 18px 18px 14px 18px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: 0 10px 35px rgba(0,0,0,0.25);
            transition: transform .12s ease, border-color .12s ease, background .12s ease;
            height: 100%;
          }
          .bubble:hover {
            transform: translateY(-2px);
            border-color: rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.08);
          }
          .bubble-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin: 0;
          }
          .bubble-meta {
            margin-top: 8px;
            font-size: 0.88rem;
            opacity: 0.9;
          }
          .pill {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            margin-right: 6px;
            border: 1px solid rgba(255,255,255,0.14);
            background: rgba(255,255,255,0.05);
          }
          .muted { opacity: 0.8; }
          .tiny { font-size: 0.80rem; opacity: 0.85; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(settings) -> None:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.title("🫧 Bubble Board Dashboard")
        st.caption("Tasks from projects.xlsx → bubble board • Live tickers • Click for AI description")
    with c2:
        st.write("")
        st.write("")
        st.markdown(
            f"<div class='tiny'>Spreadsheet: <b>{settings.xlsx_path}</b></div>",
            unsafe_allow_html=True,
        )


def render_filters(df: pd.DataFrame, settings) -> Tuple[pd.DataFrame, Dict]:
    ui_state: Dict = {}

    # Sidebar filters for TV-friendly layout
    with st.expander("🔎 Filters & View", expanded=True):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            search = st.text_input("Search", value="", placeholder="type to filter…")
        with col2:
            categories = sorted([c for c in df["Category"].unique() if str(c).strip() != ""])
            cat = st.multiselect("Category", options=categories, default=[])
        with col3:
            statuses = sorted([s for s in df["Current Status"].unique() if str(s).strip() != ""])
            status = st.multiselect("Status", options=statuses, default=[])
        with col4:
            pri = st.multiselect(
                "Priority",
                options=list(range(settings.priority_min, settings.priority_max + 1)),
                default=[],
            )

        ui_state.update({"search": search, "cat": cat, "status": status, "pri": pri})

        out = df.copy()

        if search.strip():
            s = search.strip().lower()
            mask = (
                out["Project / Item"].astype(str).str.lower().str.contains(s)
                | out["Next Action"].astype(str).str.lower().str.contains(s)
                | out["Dependencies / Prerequisites"].astype(str).str.lower().str.contains(s)
                | out["Category"].astype(str).str.lower().str.contains(s)
            )
            out = out.loc[mask]

        if cat:
            out = out.loc[out["Category"].isin(cat)]

        if status:
            out = out.loc[out["Current Status"].isin(status)]

        if pri:
            out = out.loc[out["Priority"].isin(pri)]

    return out, ui_state


def _date_badge(d) -> str:
    if not d:
        return ""
    return str(d)


def _priority_label(p) -> str:
    try:
        pnum = int(float(p))
        return f"P{pnum}"
    except Exception:
        return "P—"


def render_task_grid(df: pd.DataFrame, settings, ui_state: Dict):
    if "selected_row_id" not in st.session_state:
        st.session_state["selected_row_id"] = None

    cols = st.columns(settings.bubble_columns, gap="large")
    selected = st.session_state["selected_row_id"]

    for idx, row in df.iterrows():
        col = cols[idx % settings.bubble_columns]
        with col:
            title = str(row["Project / Item"]).strip() or "(untitled)"
            cat = str(row["Category"]).strip()
            status = str(row["Current Status"]).strip()
            next_action = str(row["Next Action"]).strip()

            p_label = _priority_label(row["Priority"])
            start = _date_badge(row["Start Date"])
            tend = _date_badge(row["Target End Date"])

            # Render a "bubble card" + a button overlay
            st.markdown(
                f"""
                <div class="bubble">
                  <div>
                    <span class="pill">{p_label}</span>
                    <span class="pill muted">{cat or 'Uncategorized'}</span>
                    <span class="pill muted">{status or 'No status'}</span>
                  </div>
                  <p class="bubble-title">{title}</p>
                  <div class="bubble-meta">
                    <div><span class="muted">Next:</span> {next_action or '—'}</div>
                    <div class="tiny"><span class="muted">Start:</span> {start or '—'} &nbsp; <span class="muted">End:</span> {tend or '—'}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Click handler
            if st.button("Open", key=f"open_{int(row['_row_id'])}", use_container_width=True):
                st.session_state["selected_row_id"] = int(row["_row_id"])
                selected = int(row["_row_id"])

    return selected


def render_task_detail(item: Dict, settings) -> None:
    st.markdown("### 🧾 Selected Task")
    left, right = st.columns([2, 1], gap="large")
    with left:
        st.markdown(f"**{item.get('Project / Item','(untitled)')}**")
        st.write(item.get("Current Status", ""))
        st.markdown("**Next Action**")
        st.write(item.get("Next Action", "—"))
        st.markdown("**Dependencies / Prerequisites**")
        dep = item.get("Dependencies / Prerequisites", "—")
        st.write(dep if dep else "—")

    with right:
        st.markdown("**Meta**")
        st.write(f"Category: {item.get('Category','—')}")
        st.write(f"Priority: {item.get('Priority','—')}")
        st.write(f"Start Date: {item.get('Start Date','—')}")
        st.write(f"Target End Date: {item.get('Target End Date','—')}")
        st.write(f"Estimated Cost ($): {item.get('Estimated Cost ($)','—')}")

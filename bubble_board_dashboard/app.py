import os
import time
from datetime import datetime
import streamlit as st

from src.config import Settings, load_settings
from src.tasks import load_tasks
from src.stocks import get_quotes, get_sparklines
from src.ai import get_ai_description
from src.ui import inject_global_css, render_header, render_filters, render_task_grid, render_task_detail

st.set_page_config(
    page_title="Bubble Board Dashboard",
    page_icon="🫧",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_css()

settings: Settings = load_settings()

# Sidebar controls
st.sidebar.title("🫧 Bubble Board")
st.sidebar.caption("Read-only dashboard for your projects.xlsx tasks + live tickers + AI descriptions.")

st.sidebar.subheader("Data source")
st.sidebar.code(settings.xlsx_path, language="bash")
st.sidebar.write(f"Sheet: **{settings.sheet_name or 'auto'}**")
st.sidebar.write(f"Priority scale: **{settings.priority_min}–{settings.priority_max}** (1 = highest)")

st.sidebar.subheader("Refresh")
auto_refresh = st.sidebar.toggle("Auto-refresh", value=True, help="Refresh data and prices periodically.")
refresh_sec = st.sidebar.slider("Refresh interval (seconds)", min_value=10, max_value=300, value=settings.refresh_seconds, step=10)
st.sidebar.caption("Tip: set to 30–60s for a TV dashboard.")

if auto_refresh:
    # Streamlit-native auto refresh
    st.markdown(f"<meta http-equiv='refresh' content='{int(refresh_sec)}'>", unsafe_allow_html=True)

# Load tasks
tasks_df, load_error = load_tasks(
    xlsx_path=settings.xlsx_path,
    sheet_name=settings.sheet_name,
    required_columns=settings.required_columns,
)

# Header: tickers
render_header(settings)

tickers_col, tasks_col = st.columns([1, 2], gap="large")

with tickers_col:
    st.subheader("📈 Live Tickers")
    st.caption("VOO • VOOG • ORCL • PLTR")
    try:
        quotes = get_quotes(settings.tickers, ttl_seconds=settings.stock_ttl_seconds)
        sparklines = get_sparklines(settings.tickers, ttl_seconds=settings.stock_ttl_seconds)
        for t in settings.tickers:
            q = quotes.get(t)
            if not q:
                st.warning(f"{t}: no data (check internet / yfinance).")
                continue
            st.markdown(f"### {t}")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.metric("Price", q["price"], q.get("change_abs"))
            with c2:
                st.metric("Change", q.get("change_pct"), "")
            with c3:
                st.metric("As of", q.get("asof"), "")
            sp = sparklines.get(t)
            if sp is not None and len(sp) > 1:
                st.line_chart(sp, height=90)
            st.divider()
    except Exception as e:
        st.error(f"Ticker panel error: {e}")

with tasks_col:
    st.subheader("✅ Tasks")
    if load_error:
        st.error(load_error)
        st.info("Fix the path or columns, then refresh. See README for details.")
        st.stop()

    # Filters + sorting
    filtered_df, ui_state = render_filters(tasks_df, settings)
    st.caption(f"Showing **{len(filtered_df)}** items (sorted by Priority → Target End Date → Start Date).")

    # Grid
    selected_id = render_task_grid(filtered_df, settings, ui_state)

    # Detail panel
    if selected_id is not None:
        item_row = filtered_df.loc[filtered_df["_row_id"] == selected_id].iloc[0].to_dict()
        render_task_detail(item_row, settings)

        # AI description on-demand
        st.markdown("#### 🤖 AI Description")
        st.caption("Uses your local DeepSeek server on your desktop (configure in .env).")
        colA, colB = st.columns([1, 3])
        with colA:
            do_ai = st.button("Generate / Refresh", use_container_width=True)
        with colB:
            st.info("Click the button to generate an AI description for the selected task.")
        if do_ai:
            with st.spinner("Generating…"):
                try:
                    desc = get_ai_description(item_row, settings)
                    st.success("Done.")
                    st.markdown(desc)
                except Exception as e:
                    st.error(f"AI call failed: {e}")
                    st.markdown(
                        "- Verify your desktop AI server is reachable from the Pi.\n"
                        "- Check AI_BASE_URL / AI_MODEL in .env.\n"
                        "- See README for DeepSeek server options."
                    )
    else:
        st.info("Click a task bubble to see details and generate its AI description.")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from config import RESULTS_DAY

st.set_page_config(
    page_title="TN Election 2026 Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("pages/overview.py", title="Overview", icon="📊"),
    st.Page("pages/trends.py", title="Trend Lines", icon="📈"),
    st.Page("pages/sources.py", title="Source Breakdown", icon="🔍"),
    st.Page("pages/topics.py", title="Topic Heatmap", icon="🗺️"),
]

if RESULTS_DAY:
    pages.append(st.Page("pages/results_day.py", title="Results Day", icon="🗳️"))

pg = st.navigation(pages)
pg.run()

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from storage.db import get_session
from storage.models import HourlyAggregate, RawPost
from dashboard.components.charts import source_stacked_bar

st.title("Source Breakdown")

cutoff_dt = datetime.utcnow() - timedelta(days=7)

session = get_session()
try:
    rows = (
        session.query(HourlyAggregate)
        .filter(HourlyAggregate.state == "TN")
        .filter(HourlyAggregate.hour >= cutoff_dt)
        .all()
    )

    lang_rows = (
        session.query(RawPost.lang, RawPost.source)
        .filter(RawPost.collected_at >= cutoff_dt)
        .all()
    )
finally:
    session.close()

if not rows:
    st.info("No source data yet.")
    st.stop()

records = []
for r in rows:
    breakdown = r.source_breakdown or {}
    if isinstance(breakdown, str):
        breakdown = json.loads(breakdown)
    for source, count in breakdown.items():
        records.append({"date": r.hour.date(), "source": source, "post_count": count})

df = pd.DataFrame(records)
if not df.empty:
    df_daily = df.groupby(["date", "source"])["post_count"].sum().reset_index()
    fig = source_stacked_bar(df_daily)
    st.plotly_chart(fig, use_container_width=True)

if lang_rows:
    lang_df = pd.DataFrame(lang_rows, columns=["lang", "source"])
    lang_counts = lang_df["lang"].value_counts()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Language Distribution")
        st.dataframe(lang_counts.rename("count"))
    with col2:
        st.info(
            "**Signal quality:**\n"
            "- **YouTube**: High-volume Tamil comments\n"
            "- **Reddit**: English, higher quality discussion\n"
            "- **Telegram**: Real-time Tamil political channels\n"
            "- **Google Trends**: Search buzz (not sentiment)"
        )

import streamlit as st
from datetime import date, datetime, timedelta
from storage.db import get_session
from storage.models import TrendsDaily, RawPost, HourlyAggregate
from dashboard.components.charts import sentiment_gauge
from dashboard.components.metrics import confidence_badge

PARTIES = ["DMK+", "ADMK+", "TVK", "NTK"]

st.title("TN Election 2026 — Sentiment Overview")

session = get_session()
today = date.today()
cutoff_dt = datetime.utcnow() - timedelta(days=1)

try:
    rows = (
        session.query(TrendsDaily)
        .filter(TrendsDaily.state == "TN")
        .filter(TrendsDaily.date >= today - timedelta(days=1))
        .all()
    )
    total_posts_24h = session.query(RawPost).filter(RawPost.collected_at >= cutoff_dt).count()
finally:
    session.close()

if not rows:
    st.info("No data yet. Run `python scheduler.py` to start collecting posts.")
    st.stop()

latest = {r.party: r for r in rows}

st.caption(f"Last 24h: **{total_posts_24h:,} posts** collected across all sources")

cols = st.columns(len(PARTIES))
for i, party in enumerate(PARTIES):
    with cols[i]:
        if party in latest:
            r = latest[party]
            fig = sentiment_gauge(party, r.sentiment_index or 0.0)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(confidence_badge(r.confidence_level or "low"))
            st.caption(f"{r.volume_index or 0:,} posts")
        else:
            st.metric(party, "No data")

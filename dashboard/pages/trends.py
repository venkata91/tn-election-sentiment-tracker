import streamlit as st
import pandas as pd
from datetime import date, timedelta
from storage.db import get_session
from storage.models import TrendsDaily
from dashboard.components.charts import sentiment_timeline

PARTIES = ["DMK+", "ADMK+", "TVK", "NTK"]

st.title("Party Sentiment Trends")

col1, col2 = st.columns([3, 1])
with col2:
    days = st.selectbox("Time range", [7, 30, 90], index=0)
with col1:
    selected = st.multiselect("Parties", PARTIES, default=["DMK", "AIADMK", "BJP"])

session = get_session()
rows = (
    session.query(TrendsDaily)
    .filter(TrendsDaily.state == "TN")
    .filter(TrendsDaily.date >= date.today() - timedelta(days=days))
    .filter(TrendsDaily.party.in_(selected))
    .order_by(TrendsDaily.date)
    .all()
)
session.close()

if not rows:
    st.info("No trend data available yet.")
    st.stop()

df = pd.DataFrame([{
    "date": r.date,
    "party": r.party,
    "sentiment_index": r.sentiment_index or 0.0,
} for r in rows])

fig = sentiment_timeline(df, selected)
st.plotly_chart(fig, use_container_width=True)

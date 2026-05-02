import streamlit as st
import pandas as pd
from storage.db import get_session
from storage.models import SentimentScore
from dashboard.components.charts import topic_heatmap

st.title("Party × Topic Heatmap")
st.caption("Driven by Claude API daily sampling (~200–300 posts/day). Refreshes after 2 AM.")

session = get_session()
rows = session.query(SentimentScore).filter(SentimentScore.topic.isnot(None)).all()
session.close()

if not rows:
    st.info("No topic labels yet. Claude API daily sampling runs at 2 AM.")
    st.stop()

df = pd.DataFrame([{"party": r.party, "topic": r.topic, "count": 1} for r in rows])
df = df.groupby(["party", "topic"]).sum().reset_index()

fig = topic_heatmap(df)
st.plotly_chart(fig, use_container_width=True)

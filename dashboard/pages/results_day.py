import streamlit as st
import pandas as pd
from datetime import date, timedelta
from storage.db import get_session
from storage.models import TrendsDaily

PARTIES = ["DMK", "AIADMK", "BJP", "VCK", "PMK"]
TOTAL_SEATS = 234

st.title("Results Day — Predicted vs. Actual")
st.warning("Results Day mode is active. Set `RESULTS_DAY=false` in `.env` to return to normal view.")

session = get_session()
rows = (
    session.query(TrendsDaily)
    .filter(TrendsDaily.state == "TN")
    .filter(TrendsDaily.date >= date.today() - timedelta(days=30))
    .all()
)
session.close()

avg_sentiment: dict = {p: 0.0 for p in PARTIES}
if rows:
    df = pd.DataFrame([{"party": r.party, "sentiment_index": r.sentiment_index or 0.0} for r in rows])
    avg_sentiment = df.groupby("party")["sentiment_index"].mean().to_dict()

st.subheader("Pre-Election Sentiment (30-day average)")
pred_cols = st.columns(len(PARTIES))
for i, party in enumerate(PARTIES):
    with pred_cols[i]:
        score = avg_sentiment.get(party, 0.0)
        st.metric(party, f"{score:+.3f}", help="Average sentiment index -1 to +1")

st.divider()
st.subheader("Enter Actual Results (ECI official)")

actual_seats: dict = {}
res_cols = st.columns(len(PARTIES))
for i, party in enumerate(PARTIES):
    with res_cols[i]:
        actual_seats[party] = st.number_input(
            party, min_value=0, max_value=TOTAL_SEATS, value=0, key=f"seats_{party}"
        )

if sum(actual_seats.values()) > 0:
    st.divider()
    st.subheader("Sentiment Rank vs. Seat Rank")

    sent_rank = sorted(PARTIES, key=lambda p: avg_sentiment.get(p, 0.0), reverse=True)
    seat_rank = sorted(PARTIES, key=lambda p: actual_seats.get(p, 0), reverse=True)

    comparison = pd.DataFrame({
        "Party": PARTIES,
        "Avg Sentiment": [f"{avg_sentiment.get(p, 0.0):+.3f}" for p in PARTIES],
        "Sentiment Rank": [sent_rank.index(p) + 1 for p in PARTIES],
        "Actual Seats": [actual_seats[p] for p in PARTIES],
        "Seat Rank": [seat_rank.index(p) + 1 for p in PARTIES],
        "Rank Match": ["✅" if sent_rank.index(p) == seat_rank.index(p) else "❌" for p in PARTIES],
    })
    st.dataframe(comparison.set_index("Party"))

    matches = sum(1 for p in PARTIES if sent_rank.index(p) == seat_rank.index(p))
    st.metric("Rank accuracy", f"{matches}/{len(PARTIES)} parties correctly ranked")

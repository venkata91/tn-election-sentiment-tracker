from datetime import date
from pytrends.request import TrendReq
from storage.db import get_session, init_db
from storage.models import SearchInterest
from config import PARTY_KEYWORDS

_TREND_TERMS = list(PARTY_KEYWORDS.keys())  # ["DMK", "AIADMK", "BJP", "VCK", "PMK"]

def fetch_and_store() -> int:
    """Fetch Google Trends interest for TN parties and persist to search_interest. Returns count stored."""
    pytrends = TrendReq(hl="en-IN", tz=330)
    pytrends.build_payload(_TREND_TERMS, geo="IN-TN", timeframe="today 3-m")
    df = pytrends.interest_over_time()

    if df.empty:
        return 0

    init_db()
    session = get_session()
    today = date.today()
    count = 0

    for party in _TREND_TERMS:
        if party not in df.columns:
            continue
        value = int(df[party].iloc[-1])
        existing = session.query(SearchInterest).filter_by(party=party, date=today).first()
        if existing:
            existing.interest_value = value
        else:
            session.add(SearchInterest(party=party, date=today, interest_value=value, geo="IN-TN"))
        count += 1

    session.commit()
    session.close()
    return count

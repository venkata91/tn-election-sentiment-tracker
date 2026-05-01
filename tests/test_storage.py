import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base, RawPost, PartyMention, SentimentScore, HourlyAggregate, SearchInterest, TrendsDaily
from datetime import datetime, date

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()

def test_insert_raw_post(session):
    post = RawPost(source="youtube", post_id="yt_test_1", text="DMK rally today", lang="en", engagement=10)
    session.add(post)
    session.commit()
    fetched = session.query(RawPost).filter_by(post_id="yt_test_1").first()
    assert fetched is not None
    assert fetched.source == "youtube"
    assert fetched.collected_at is not None

def test_unique_post_id(session):
    post1 = RawPost(source="youtube", post_id="dup_id", text="First post", lang="en")
    post2 = RawPost(source="youtube", post_id="dup_id", text="Duplicate post", lang="en")
    session.add(post1)
    session.commit()
    session.add(post2)
    with pytest.raises(Exception):
        session.commit()

def test_party_mention(session):
    post = RawPost(source="reddit", post_id="r_1", text="AIADMK rally", lang="en")
    session.add(post)
    session.flush()
    mention = PartyMention(post_id=post.id, party="AIADMK", mention_type="direct")
    session.add(mention)
    session.commit()
    fetched = session.query(PartyMention).filter_by(post_id=post.id).first()
    assert fetched.party == "AIADMK"
    assert fetched.mention_type == "direct"

def test_sentiment_score(session):
    post = RawPost(source="telegram", post_id="tg_1", text="BJP meeting", lang="ta")
    session.add(post)
    session.flush()
    score = SentimentScore(post_id=post.id, party="BJP", model_score=0.8, model_confidence=0.75, final_score=0.8)
    session.add(score)
    session.commit()
    fetched = session.query(SentimentScore).filter_by(post_id=post.id).first()
    assert fetched.model_score == 0.8
    assert fetched.llm_score is None

def test_search_interest(session):
    record = SearchInterest(party="DMK", date=date.today(), interest_value=75, geo="IN-TN")
    session.add(record)
    session.commit()
    fetched = session.query(SearchInterest).filter_by(party="DMK").first()
    assert fetched.interest_value == 75
    assert fetched.geo == "IN-TN"

def test_trends_daily(session):
    row = TrendsDaily(state="TN", party="DMK", date=date.today(), sentiment_index=0.45, volume_index=500, confidence_level="medium")
    session.add(row)
    session.commit()
    fetched = session.query(TrendsDaily).filter_by(party="DMK").first()
    assert fetched.sentiment_index == 0.45

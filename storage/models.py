from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class RawPost(Base):
    __tablename__ = "raw_posts"
    id = Column(Integer, primary_key=True)
    source = Column(String(20), nullable=False)
    post_id = Column(String(200), nullable=False, unique=True)
    url = Column(Text)
    text = Column(Text, nullable=False)
    lang = Column(String(5))
    author = Column(String(200))
    engagement = Column(Integer, default=0)
    posted_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow)

class PartyMention(Base):
    __tablename__ = "party_mentions"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, nullable=False)
    party = Column(String(20), nullable=False)
    mention_type = Column(String(20))

class SentimentScore(Base):
    __tablename__ = "sentiment_scores"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, nullable=False)
    party = Column(String(20), nullable=False)
    model_score = Column(Float)
    model_confidence = Column(Float)
    llm_score = Column(Float)
    llm_confidence = Column(String(10))
    topic = Column(String(30))
    final_score = Column(Float)
    scored_at = Column(DateTime, default=datetime.utcnow)

class HourlyAggregate(Base):
    __tablename__ = "hourly_aggregates"
    id = Column(Integer, primary_key=True)
    state = Column(String(10), nullable=False)
    party = Column(String(20), nullable=False)
    hour = Column(DateTime, nullable=False)
    avg_sentiment = Column(Float)
    post_count = Column(Integer, default=0)
    source_breakdown = Column(JSON)
    confidence_level = Column(String(10))

class SearchInterest(Base):
    __tablename__ = "search_interest"
    id = Column(Integer, primary_key=True)
    party = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    interest_value = Column(Integer)
    geo = Column(String(10), default="IN-TN")
    collected_at = Column(DateTime, default=datetime.utcnow)

class TrendsDaily(Base):
    __tablename__ = "trends_daily"
    id = Column(Integer, primary_key=True)
    state = Column(String(10), nullable=False)
    party = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    sentiment_index = Column(Float)
    volume_index = Column(Integer, default=0)
    confidence_level = Column(String(10))
    dominant_topic = Column(String(30))

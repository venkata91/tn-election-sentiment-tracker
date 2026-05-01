# TN Election Sentiment Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Tamil Nadu 2026 election sentiment tracker that collects social media posts from YouTube/Reddit/Telegram every 2 hours, scores them for per-party sentiment using XLM-RoBERTa + Claude API daily calibration, and displays trends in a Streamlit dashboard with a Results Day mode.

**Architecture:** Free data sources (YouTube comments, Reddit, Telegram public channels, Google Trends) feed a Python pipeline that performs party attribution via keyword matching and sentiment scoring via a multilingual transformer model. A SQLite database stores raw posts through daily aggregates. A Streamlit dashboard renders 5 pages: Overview, Trends, Sources, Topics, and Results Day.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.x (SQLite), `cardiffnlp/twitter-xlm-roberta-base-sentiment` (HuggingFace transformers), Anthropic Claude API (haiku model for LLM judge), Streamlit 1.35+, Plotly, APScheduler, PRAW, Telethon, google-api-python-client, pytrends, langdetect.

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`
- Create: `storage/__init__.py`, `ingest/__init__.py`, `pipeline/__init__.py`, `dashboard/__init__.py`, `dashboard/components/__init__.py`, `dashboard/pages/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/vsowrira/git/elections
mkdir -p storage ingest pipeline dashboard/components dashboard/pages tests
touch storage/__init__.py ingest/__init__.py pipeline/__init__.py
touch dashboard/__init__.py dashboard/components/__init__.py dashboard/pages/__init__.py
touch tests/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
anthropic>=0.20.0
google-api-python-client>=2.0.0
praw>=7.7.0
telethon>=1.30.0
pytrends>=4.9.0
transformers>=4.40.0
torch>=2.0.0
sqlalchemy>=2.0.0
streamlit>=1.35.0
plotly>=5.20.0
pandas>=2.0.0
langdetect>=1.0.9
apscheduler>=3.10.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 3: Write `.env.example`**

```
YOUTUBE_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=elections-tracker/1.0
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
ANTHROPIC_API_KEY=
DATABASE_URL=sqlite:///elections.db
TARGET_STATE=TN
RESULTS_DAY=false
LOG_LEVEL=INFO
```

- [ ] **Step 4: Write `config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "elections-tracker/1.0")
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///elections.db")
TARGET_STATE = os.getenv("TARGET_STATE", "TN")
RESULTS_DAY = os.getenv("RESULTS_DAY", "false").lower() == "true"

PARTY_KEYWORDS = {
    "DMK": [
        "dmk", "திமுக", "#dmk", "mkstalin", "mk stalin", "stalin",
        "உதயநிதி", "udhayanidhi", "tr baalu", "duraimurugan",
    ],
    "AIADMK": [
        "aiadmk", "அதிமுக", "#aiadmk", "eps", "edappadi", "palaniswami",
        "இபிஎஸ்", "o panneerselvam", "ops",
    ],
    "BJP": [
        "bjp", "பாஜக", "#bjp", "annamalai", "அண்ணாமலை", "modi",
        "நரேந்திர மோடி", "tamilnadu bjp", "tamilisai",
    ],
    "VCK": [
        "vck", "விடுதலை சிறுத்தைகள்", "thirumavalavan", "thiruma",
        "திருமாவளவன்",
    ],
    "PMK": [
        "pmk", "பாமக", "ramadoss", "anbumani", "அன்புமணி",
    ],
}

YOUTUBE_CHANNELS = {
    # Verify channel IDs at youtube.com/@<handle> → About → Share → Copy channel ID
    "thanthi_tv": "UCu6HHfxLzniTEGJhYnqpAew",
    "sun_news": "UCn0QyOr3mNWNrFDzGJ5TnXA",
    "puthiya_thalaimurai": "UCiJbpLSiQbRFxzUVD2k25cw",
    "polimer_news": "UC9R3_MBmQKl8kGH4oY9byQA",
    "news_j": "UC6GoBiRtfoBZZB3c2U9Q7zg",
}

YOUTUBE_SEARCH_QUERIES = [
    "தமிழ்நாடு தேர்தல்",
    "TN election 2026",
    "DMK AIADMK BJP Tamil Nadu",
    "Stalin Annamalai EPS election",
]

TELEGRAM_CHANNELS = [
    "tamilpoliticsnews",
    "tnpoliticsupdates",
]

REDDIT_SUBREDDITS = ["Chennai", "TamilNadu", "india"]
REDDIT_SEARCH_TERMS = [
    "DMK", "AIADMK", "Stalin", "Edappadi", "Annamalai",
    "Tamil Nadu election", "TN BJP",
]
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error. `torch` may take a few minutes.

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt .env.example config.py storage/__init__.py ingest/__init__.py pipeline/__init__.py dashboard/__init__.py dashboard/components/__init__.py dashboard/pages/__init__.py tests/__init__.py
git commit -m "feat: project scaffold, config, and dependencies"
```

---

## Task 2: Storage Layer

**Files:**
- Create: `storage/models.py`
- Create: `storage/db.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing test `tests/test_storage.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_storage.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'storage.models'`

- [ ] **Step 3: Write `storage/models.py`**

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, JSON, UniqueConstraint
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
```

- [ ] **Step 4: Write `storage/db.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
from config import DATABASE_URL

_engine = None
_Session = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
    return _engine

def init_db():
    Base.metadata.create_all(get_engine())

def get_session():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine())
    return _Session()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_storage.py -v
```

Expected: 6 PASSED

- [ ] **Step 6: Commit**

```bash
git add storage/models.py storage/db.py tests/test_storage.py
git commit -m "feat: SQLAlchemy storage models and db session factory"
```

---

## Task 3: Ingest Base + Party Extractor

**Files:**
- Create: `ingest/base.py`
- Create: `pipeline/party_extractor.py`
- Create: `tests/test_party_extractor.py`

- [ ] **Step 1: Write failing test `tests/test_party_extractor.py`**

```python
import pytest
from pipeline.party_extractor import extract_mentions

def test_extract_dmk_english():
    mentions = extract_mentions("I support DMK in this election")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties

def test_extract_dmk_tamil_script():
    mentions = extract_mentions("திமுக இந்த தேர்தலில் வெல்லும்")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties

def test_extract_candidate_name_direct_type():
    mentions = extract_mentions("Stalin is a great leader for Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties
    types = [m[1] for m in mentions if m[0] == "DMK"]
    assert "candidate" in types

def test_extract_hashtag_type():
    mentions = extract_mentions("#DMK is trending today in Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties
    types = [m[1] for m in mentions if m[0] == "DMK"]
    assert "hashtag" in types

def test_extract_multiple_parties():
    mentions = extract_mentions("DMK and AIADMK are competing fiercely in Tamil Nadu 2026")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties
    assert "AIADMK" in parties

def test_no_party_mention():
    mentions = extract_mentions("The weather today is nice in Chennai")
    assert mentions == []

def test_extract_bjp_candidate():
    mentions = extract_mentions("Annamalai held a rally in Coimbatore")
    parties = [m[0] for m in mentions]
    assert "BJP" in parties

def test_extract_aiadmk_eps():
    mentions = extract_mentions("EPS addressed a press conference about Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "AIADMK" in parties

def test_no_duplicate_party_in_result():
    mentions = extract_mentions("DMK DMK DMK wins the election")
    dmk_mentions = [m for m in mentions if m[0] == "DMK"]
    assert len(dmk_mentions) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_party_extractor.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `ingest/base.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class RawPostData:
    source: str
    post_id: str
    text: str
    url: Optional[str] = None
    lang: Optional[str] = None
    author: Optional[str] = None
    engagement: int = 0
    posted_at: Optional[datetime] = None

class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self) -> List[RawPostData]:
        """Fetch posts and return as RawPostData list."""
        ...
```

- [ ] **Step 4: Write `pipeline/party_extractor.py`**

```python
from config import PARTY_KEYWORDS
from typing import List, Tuple

_DIRECT_NAMES = {"dmk", "aiadmk", "bjp", "vck", "pmk",
                  "திமுக", "அதிமுக", "பாஜக", "பாமக",
                  "விடுதலை சிறுத்தைகள்"}

def extract_mentions(text: str) -> List[Tuple[str, str]]:
    """
    Return list of (party, mention_type) for each party mentioned in text.
    mention_type: 'direct' | 'candidate' | 'hashtag'
    One entry per party maximum (first matching keyword wins).
    """
    text_lower = text.lower()
    results = []
    for party, keywords in PARTY_KEYWORDS.items():
        for keyword in keywords:
            kw_lower = keyword.lower()
            if kw_lower in text_lower:
                if kw_lower.startswith("#"):
                    mention_type = "hashtag"
                elif kw_lower in _DIRECT_NAMES:
                    mention_type = "direct"
                else:
                    mention_type = "candidate"
                results.append((party, mention_type))
                break  # one entry per party
    return results
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_party_extractor.py -v
```

Expected: 9 PASSED

- [ ] **Step 6: Commit**

```bash
git add ingest/base.py pipeline/party_extractor.py tests/test_party_extractor.py
git commit -m "feat: ingest base types and party keyword extractor"
```

---

## Task 4: Preprocessor

**Files:**
- Create: `pipeline/preprocessor.py`
- Create: `tests/test_preprocessor.py`

- [ ] **Step 1: Write failing test `tests/test_preprocessor.py`**

```python
import pytest
from ingest.base import RawPostData
from pipeline.preprocessor import is_spam, detect_language, preprocess

def _post(text: str, post_id: str = "1") -> RawPostData:
    return RawPostData(source="youtube", post_id=post_id, text=text)

def test_is_spam_too_short():
    assert is_spam("hi") is True

def test_is_spam_one_word():
    assert is_spam("DMK") is True

def test_is_spam_hashtag_heavy():
    assert is_spam("#a #b #c #d #e some text") is True

def test_is_spam_normal_text():
    assert is_spam("I think DMK will win the Tamil Nadu election this time around") is False

def test_detect_language_english():
    lang = detect_language("I love cricket and Tamil Nadu politics is very interesting")
    assert lang == "en"

def test_detect_language_unknown_short():
    lang = detect_language("xyz")
    assert lang == "unknown"

def test_preprocess_dedup_same_text():
    same = "DMK is going to win in Tamil Nadu 2026 for sure this time"
    posts = [_post(same, "1"), _post(same, "2")]
    # Reset seen set between test runs by re-importing or using fresh call
    result = preprocess(posts)
    assert len(result) == 1

def test_preprocess_filters_spam():
    posts = [_post("hi", "1"), _post("DMK is going to win in Tamil Nadu 2026", "2")]
    result = preprocess(posts)
    assert len(result) == 1
    assert result[0].post_id == "2"

def test_preprocess_adds_language():
    posts = [_post("I support the Tamil Nadu election outcome this year", "1")]
    result = preprocess(posts)
    assert result[0].lang is not None
    assert result[0].lang != "unknown"

def test_preprocess_keeps_lang_if_set():
    post = _post("Some text here about Tamil Nadu elections clearly", "1")
    post.lang = "ta"
    result = preprocess([post])
    assert result[0].lang == "ta"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_preprocessor.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `pipeline/preprocessor.py`**

```python
import hashlib
from langdetect import detect, LangDetectException
from typing import List
from ingest.base import RawPostData

_seen_hashes: set = set()

def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def is_spam(text: str) -> bool:
    words = text.split()
    if len(words) < 4:
        return True
    hashtag_ratio = sum(1 for w in words if w.startswith("#")) / len(words)
    return hashtag_ratio > 0.5

def preprocess(posts: List[RawPostData]) -> List[RawPostData]:
    """Deduplicate within batch, filter spam, detect language."""
    clean = []
    local_seen: set = set()
    for post in posts:
        if is_spam(post.text):
            continue
        h = _content_hash(post.text)
        if h in _seen_hashes or h in local_seen:
            continue
        local_seen.add(h)
        _seen_hashes.add(h)
        if not post.lang:
            post.lang = detect_language(post.text)
        clean.append(post)
    return clean
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_preprocessor.py -v
```

Expected: 10 PASSED. (Note: `langdetect` is probabilistic; if `test_detect_language_english` is flaky, run it 3 times — it should pass consistently on longer text.)

- [ ] **Step 5: Commit**

```bash
git add pipeline/preprocessor.py tests/test_preprocessor.py
git commit -m "feat: text preprocessor with spam filter, lang detect, dedup"
```

---

## Task 5: Sentiment Model

**Files:**
- Create: `pipeline/sentiment_model.py`
- Create: `tests/test_sentiment_model.py`

- [ ] **Step 1: Write failing test `tests/test_sentiment_model.py`**

```python
import pytest
from unittest.mock import patch, MagicMock
from pipeline.sentiment_model import score_text, LABEL_TO_SCORE

def _mock_classifier(label: str, prob: float):
    mock = MagicMock()
    mock.return_value = [[{"label": label, "score": prob}]]
    return mock

def test_positive_returns_positive_score():
    with patch("pipeline.sentiment_model._get_classifier", return_value=_mock_classifier("positive", 0.9)):
        score, confidence = score_text("DMK is doing great work for Tamil Nadu")
    assert score == 1.0
    assert confidence == 0.9

def test_negative_returns_negative_score():
    with patch("pipeline.sentiment_model._get_classifier", return_value=_mock_classifier("negative", 0.85)):
        score, confidence = score_text("AIADMK corruption scandal exposed")
    assert score == -1.0
    assert confidence == 0.85

def test_neutral_returns_zero():
    with patch("pipeline.sentiment_model._get_classifier", return_value=_mock_classifier("neutral", 0.7)):
        score, confidence = score_text("BJP held a meeting in Chennai today")
    assert score == 0.0
    assert confidence == 0.7

def test_label_to_score_completeness():
    assert LABEL_TO_SCORE["positive"] == 1.0
    assert LABEL_TO_SCORE["negative"] == -1.0
    assert LABEL_TO_SCORE["neutral"] == 0.0

def test_score_bounds():
    with patch("pipeline.sentiment_model._get_classifier", return_value=_mock_classifier("positive", 0.99)):
        score, confidence = score_text("some text")
    assert -1.0 <= score <= 1.0
    assert 0.0 <= confidence <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_sentiment_model.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `pipeline/sentiment_model.py`**

```python
from transformers import pipeline as hf_pipeline
from typing import Tuple

_classifier = None

LABEL_TO_SCORE: dict[str, float] = {
    "positive": 1.0,
    "neutral": 0.0,
    "negative": -1.0,
}

def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = hf_pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            top_k=1,
            truncation=True,
            max_length=512,
        )
    return _classifier

def score_text(text: str) -> Tuple[float, float]:
    """
    Returns (sentiment_score, confidence) where:
      sentiment_score: -1.0 (negative) to 1.0 (positive)
      confidence: 0.0 to 1.0 (model softmax probability)
    """
    classifier = _get_classifier()
    result = classifier(text[:512])[0]
    label = result["label"].lower()
    confidence = float(result["score"])
    score = LABEL_TO_SCORE.get(label, 0.0)
    return score, confidence
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sentiment_model.py -v
```

Expected: 5 PASSED (all use mocks, no model download needed)

- [ ] **Step 5: Verify model loads (manual smoke test — requires internet)**

```bash
python -c "from pipeline.sentiment_model import score_text; print(score_text('DMK will win Tamil Nadu elections'))"
```

Expected: something like `(1.0, 0.87)` or `(0.0, 0.72)` — a tuple of two floats. Model downloads ~500MB on first run.

- [ ] **Step 6: Commit**

```bash
git add pipeline/sentiment_model.py tests/test_sentiment_model.py
git commit -m "feat: XLM-RoBERTa sentiment scorer with lazy-loaded classifier"
```

---

## Task 6: Aggregator

**Files:**
- Create: `pipeline/aggregator.py`
- Create: `tests/test_aggregator.py`

- [ ] **Step 1: Write failing test `tests/test_aggregator.py`**

```python
import pytest
from pipeline.aggregator import compute_confidence, confidence_label

def test_high_volume_high_confidence():
    score = compute_confidence(model_prob=0.9, source_count=3, post_volume_24h=10000)
    assert score >= 0.7

def test_single_source_low_confidence():
    score = compute_confidence(model_prob=0.9, source_count=1, post_volume_24h=10)
    assert score < 0.6

def test_llm_agreement_boosts_confidence():
    without_llm = compute_confidence(0.6, 2, 1000)
    with_llm = compute_confidence(0.6, 2, 1000, llm_agreement_rate=0.9)
    assert with_llm > without_llm

def test_llm_disagreement_lowers_confidence():
    without_llm = compute_confidence(0.6, 2, 1000)
    with_llm = compute_confidence(0.6, 2, 1000, llm_agreement_rate=0.1)
    assert with_llm < without_llm

def test_confidence_label_high():
    assert confidence_label(0.8) == "high"

def test_confidence_label_medium():
    assert confidence_label(0.55) == "medium"

def test_confidence_label_low():
    assert confidence_label(0.3) == "low"

def test_confidence_score_range():
    score = compute_confidence(0.5, 2, 500)
    assert 0.0 <= score <= 1.0

def test_zero_volume_doesnt_crash():
    score = compute_confidence(0.5, 1, 0)
    assert score >= 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_aggregator.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `pipeline/aggregator.py`**

```python
import math
from datetime import datetime, timedelta
from typing import Optional
from storage.db import get_session
from storage.models import SentimentScore, RawPost, HourlyAggregate, TrendsDaily

def compute_confidence(
    model_prob: float,
    source_count: int,
    post_volume_24h: int,
    llm_agreement_rate: Optional[float] = None,
) -> float:
    volume_factor = min(1.0, math.log10(max(post_volume_24h, 1)) / 3.0)
    diversity_factor = {1: 0.5, 2: 0.75}.get(source_count, 1.0)
    base = (model_prob * 0.4) + (volume_factor * 0.3) + (diversity_factor * 0.3)
    if llm_agreement_rate is not None:
        base = (base * 0.5) + (llm_agreement_rate * 0.5)
    return round(min(max(base, 0.0), 1.0), 3)

def confidence_label(score: float) -> str:
    if score >= 0.7:
        return "high"
    elif score >= 0.45:
        return "medium"
    return "low"

def roll_up_hourly(target_hour: Optional[datetime] = None) -> None:
    """Aggregate sentiment_scores into hourly_aggregates for the given hour."""
    session = get_session()
    if target_hour is None:
        target_hour = datetime.utcnow()
    hour_start = target_hour.replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)

    parties = ["DMK", "AIADMK", "BJP", "VCK", "PMK"]
    for party in parties:
        rows = (
            session.query(SentimentScore, RawPost)
            .join(RawPost, SentimentScore.post_id == RawPost.id)
            .filter(SentimentScore.party == party)
            .filter(RawPost.collected_at >= hour_start)
            .filter(RawPost.collected_at < hour_end)
            .all()
        )
        if not rows:
            continue

        final_scores = [r.SentimentScore.final_score for r in rows if r.SentimentScore.final_score is not None]
        if not final_scores:
            continue

        avg_sentiment = sum(final_scores) / len(final_scores)
        source_counts: dict = {}
        for r in rows:
            src = r.RawPost.source
            source_counts[src] = source_counts.get(src, 0) + 1

        conf = compute_confidence(
            model_prob=abs(avg_sentiment),
            source_count=len(source_counts),
            post_volume_24h=len(rows) * 24,
        )

        existing = (
            session.query(HourlyAggregate)
            .filter_by(state="TN", party=party, hour=hour_start)
            .first()
        )
        if existing:
            existing.avg_sentiment = avg_sentiment
            existing.post_count = len(rows)
            existing.source_breakdown = source_counts
            existing.confidence_level = confidence_label(conf)
        else:
            session.add(HourlyAggregate(
                state="TN",
                party=party,
                hour=hour_start,
                avg_sentiment=avg_sentiment,
                post_count=len(rows),
                source_breakdown=source_counts,
                confidence_level=confidence_label(conf),
            ))

    session.commit()
    session.close()

def roll_up_daily() -> None:
    """Aggregate hourly_aggregates into trends_daily for today."""
    from datetime import date, time
    session = get_session()
    today = date.today()

    parties = ["DMK", "AIADMK", "BJP", "VCK", "PMK"]
    for party in parties:
        rows = (
            session.query(HourlyAggregate)
            .filter_by(state="TN", party=party)
            .filter(HourlyAggregate.hour >= datetime.combine(today, time.min))
            .all()
        )
        if not rows:
            continue

        sentiments = [r.avg_sentiment for r in rows if r.avg_sentiment is not None]
        if not sentiments:
            continue

        avg = sum(sentiments) / len(sentiments)
        volume = sum(r.post_count for r in rows)
        conf_scores = [0.7 if r.confidence_level == "high" else 0.55 if r.confidence_level == "medium" else 0.3
                       for r in rows]
        avg_conf = sum(conf_scores) / len(conf_scores)

        existing = session.query(TrendsDaily).filter_by(state="TN", party=party, date=today).first()
        if existing:
            existing.sentiment_index = round(avg, 4)
            existing.volume_index = volume
            existing.confidence_level = confidence_label(avg_conf)
        else:
            session.add(TrendsDaily(
                state="TN",
                party=party,
                date=today,
                sentiment_index=round(avg, 4),
                volume_index=volume,
                confidence_level=confidence_label(avg_conf),
            ))

    session.commit()
    session.close()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_aggregator.py -v
```

Expected: 9 PASSED

- [ ] **Step 5: Commit**

```bash
git add pipeline/aggregator.py tests/test_aggregator.py
git commit -m "feat: confidence scorer and hourly/daily aggregator"
```

---

## Task 7: LLM Judge

**Files:**
- Create: `pipeline/llm_judge.py`
- Create: `tests/test_llm_judge.py`

- [ ] **Step 1: Write failing test `tests/test_llm_judge.py`**

```python
import pytest
from unittest.mock import patch, MagicMock
from pipeline.llm_judge import _build_prompt, _parse_response, SENTIMENT_TO_SCORE

def test_build_prompt_contains_text():
    prompt = _build_prompt("DMK is winning Tamil Nadu")
    assert "DMK is winning Tamil Nadu" in prompt

def test_build_prompt_contains_instructions():
    prompt = _build_prompt("some text")
    assert "party" in prompt.lower()
    assert "sentiment" in prompt.lower()
    assert "JSON" in prompt

def test_parse_valid_json():
    raw = '{"party": "DMK", "sentiment": "positive", "confidence": "high", "topic": "leadership"}'
    result = _parse_response(raw)
    assert result is not None
    assert result["party"] == "DMK"
    assert result["sentiment"] == "positive"
    assert result["confidence"] == "high"
    assert result["topic"] == "leadership"

def test_parse_invalid_json_returns_none():
    result = _parse_response("not json at all")
    assert result is None

def test_parse_missing_field_returns_none():
    raw = '{"party": "DMK"}'
    result = _parse_response(raw)
    assert result is None

def test_sentiment_to_score_mapping():
    assert SENTIMENT_TO_SCORE["positive"] == 1.0
    assert SENTIMENT_TO_SCORE["negative"] == -1.0
    assert SENTIMENT_TO_SCORE["neutral"] == 0.0
    assert SENTIMENT_TO_SCORE["mixed"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm_judge.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `pipeline/llm_judge.py`**

```python
import json
from typing import Optional
import anthropic
from config import ANTHROPIC_API_KEY
from storage.db import get_session
from storage.models import SentimentScore, RawPost

SENTIMENT_TO_SCORE: dict[str, float] = {
    "positive": 1.0,
    "neutral": 0.0,
    "negative": -1.0,
    "mixed": 0.0,
}

_REQUIRED_FIELDS = {"party", "sentiment", "confidence", "topic"}

def _build_prompt(text: str) -> str:
    return (
        "Analyze this Tamil Nadu political social media post. "
        "Return ONLY a JSON object with no other text:\n"
        '{"party": "DMK|AIADMK|BJP|VCK|PMK|OTHER|MULTIPLE", '
        '"sentiment": "positive|negative|neutral|mixed", '
        '"confidence": "high|medium|low", '
        '"topic": "development|corruption|welfare|leadership|caste|religion|other"}\n'
        f"Post: {text[:1000]}"
    )

def _parse_response(raw: str) -> Optional[dict]:
    try:
        data = json.loads(raw.strip())
        if not _REQUIRED_FIELDS.issubset(data.keys()):
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None

def sample_and_score(n: int = 200) -> int:
    """Score up to n borderline posts via Claude API. Returns count successfully scored."""
    session = get_session()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    candidates = (
        session.query(SentimentScore, RawPost)
        .join(RawPost, SentimentScore.post_id == RawPost.id)
        .filter(SentimentScore.llm_score.is_(None))
        .filter(SentimentScore.model_confidence >= 0.40)
        .filter(SentimentScore.model_confidence <= 0.65)
        .order_by(RawPost.engagement.desc())
        .limit(n)
        .all()
    )

    scored = 0
    for score_row, post_row in candidates:
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[{"role": "user", "content": _build_prompt(post_row.text)}],
            )
            raw = message.content[0].text
            data = _parse_response(raw)
            if data is None:
                continue
            score_row.llm_score = SENTIMENT_TO_SCORE.get(data["sentiment"], 0.0)
            score_row.llm_confidence = data["confidence"]
            score_row.topic = data["topic"]
            score_row.final_score = (score_row.model_score * 0.4) + (score_row.llm_score * 0.6)
            scored += 1
        except Exception:
            continue

    session.commit()
    session.close()
    return scored
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm_judge.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add pipeline/llm_judge.py tests/test_llm_judge.py
git commit -m "feat: Claude API LLM judge for daily high-confidence sample scoring"
```

---

## Task 8: YouTube Fetcher

**Files:**
- Create: `ingest/youtube_fetcher.py`

> Note: This task fetches from a live API. Unit tests would require mocking the entire Google API client — skip that here in favour of a manual smoke test with a real API key.

- [ ] **Step 1: Write `ingest/youtube_fetcher.py`**

```python
from datetime import datetime, timedelta
from typing import List
from googleapiclient.discovery import build
from ingest.base import BaseFetcher, RawPostData
from config import YOUTUBE_API_KEY, YOUTUBE_SEARCH_QUERIES

class YouTubeFetcher(BaseFetcher):
    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        return self._service

    def _search_video_ids(self, query: str, max_results: int = 10) -> List[str]:
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = (
            self._get_service()
            .search()
            .list(
                q=query,
                type="video",
                part="id",
                maxResults=max_results,
                publishedAfter=since,
                relevanceLanguage="ta",
                regionCode="IN",
            )
            .execute()
        )
        return [item["id"]["videoId"] for item in response.get("items", [])]

    def _fetch_comments(self, video_id: str, max_results: int = 100) -> List[RawPostData]:
        try:
            response = (
                self._get_service()
                .commentThreads()
                .list(videoId=video_id, part="snippet", maxResults=max_results, order="relevance")
                .execute()
            )
        except Exception:
            return []

        posts = []
        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            posts.append(RawPostData(
                source="youtube",
                post_id=item["snippet"]["topLevelComment"]["id"],
                text=top["textOriginal"],
                url=f"https://youtube.com/watch?v={video_id}",
                author=top.get("authorDisplayName"),
                engagement=top.get("likeCount", 0),
                posted_at=datetime.fromisoformat(top["publishedAt"].replace("Z", "+00:00")).replace(tzinfo=None),
            ))
        return posts

    def fetch(self) -> List[RawPostData]:
        all_posts: List[RawPostData] = []
        seen_ids: set = set()
        for query in YOUTUBE_SEARCH_QUERIES:
            try:
                for video_id in self._search_video_ids(query):
                    if video_id not in seen_ids:
                        seen_ids.add(video_id)
                        all_posts.extend(self._fetch_comments(video_id))
            except Exception:
                continue
        return all_posts
```

- [ ] **Step 2: Smoke test (requires `YOUTUBE_API_KEY` in `.env`)**

```bash
python -c "
from ingest.youtube_fetcher import YouTubeFetcher
posts = YouTubeFetcher().fetch()
print(f'Fetched {len(posts)} posts')
if posts:
    print(f'Sample: [{posts[0].lang}] {posts[0].text[:80]}')
"
```

Expected: `Fetched N posts` where N > 0. If N=0, check that `YOUTUBE_API_KEY` is set and not quota-exhausted.

- [ ] **Step 3: Commit**

```bash
git add ingest/youtube_fetcher.py
git commit -m "feat: YouTube comments fetcher for Tamil news channels"
```

---

## Task 9: Reddit Fetcher

**Files:**
- Create: `ingest/reddit_fetcher.py`

- [ ] **Step 1: Write `ingest/reddit_fetcher.py`**

```python
from datetime import datetime
from typing import List
import praw
from ingest.base import BaseFetcher, RawPostData
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SUBREDDITS, REDDIT_SEARCH_TERMS

class RedditFetcher(BaseFetcher):
    def __init__(self):
        self._reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

    def fetch(self) -> List[RawPostData]:
        posts: List[RawPostData] = []
        for sub_name in REDDIT_SUBREDDITS:
            sub = self._reddit.subreddit(sub_name)
            for term in REDDIT_SEARCH_TERMS:
                try:
                    for submission in sub.search(term, time_filter="week", limit=20):
                        post_text = f"{submission.title}\n{submission.selftext}".strip()
                        if len(post_text) > 20:
                            posts.append(RawPostData(
                                source="reddit",
                                post_id=f"post_{submission.id}",
                                text=post_text,
                                url=f"https://reddit.com{submission.permalink}",
                                author=str(submission.author) if submission.author else None,
                                engagement=submission.score,
                                posted_at=datetime.utcfromtimestamp(submission.created_utc),
                            ))
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments.list()[:15]:
                            if len(comment.body) > 20:
                                posts.append(RawPostData(
                                    source="reddit",
                                    post_id=f"comment_{comment.id}",
                                    text=comment.body,
                                    url=f"https://reddit.com{submission.permalink}",
                                    author=str(comment.author) if comment.author else None,
                                    engagement=comment.score,
                                    posted_at=datetime.utcfromtimestamp(comment.created_utc),
                                ))
                except Exception:
                    continue
        return posts
```

- [ ] **Step 2: Smoke test (requires Reddit API credentials in `.env`)**

```bash
python -c "
from ingest.reddit_fetcher import RedditFetcher
posts = RedditFetcher().fetch()
print(f'Fetched {len(posts)} posts from Reddit')
if posts:
    print(f'Sample: {posts[0].text[:80]}')
"
```

Expected: `Fetched N posts from Reddit`. If 0, verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set.

- [ ] **Step 3: Commit**

```bash
git add ingest/reddit_fetcher.py
git commit -m "feat: Reddit fetcher for TN election posts and comments"
```

---

## Task 10: Telegram Fetcher

**Files:**
- Create: `ingest/telegram_fetcher.py`

> Telegram requires a phone-number-authenticated session on first run. The session file (`elections_session.session`) persists after that.

- [ ] **Step 1: Write `ingest/telegram_fetcher.py`**

```python
import asyncio
from datetime import datetime, timedelta
from typing import List
from telethon import TelegramClient
from ingest.base import BaseFetcher, RawPostData
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNELS

class TelegramFetcher(BaseFetcher):
    def fetch(self) -> List[RawPostData]:
        return asyncio.run(self._async_fetch())

    async def _async_fetch(self) -> List[RawPostData]:
        posts: List[RawPostData] = []
        cutoff = datetime.utcnow() - timedelta(hours=24)
        async with TelegramClient("elections_session", TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            for channel in TELEGRAM_CHANNELS:
                try:
                    async for message in client.iter_messages(channel, limit=200):
                        msg_time = message.date.replace(tzinfo=None)
                        if msg_time < cutoff:
                            break
                        if message.text and len(message.text) > 20:
                            posts.append(RawPostData(
                                source="telegram",
                                post_id=f"{channel}_{message.id}",
                                text=message.text,
                                url=f"https://t.me/{channel}/{message.id}",
                                engagement=getattr(message, "views", 0) or 0,
                                posted_at=msg_time,
                            ))
                except Exception:
                    continue
        return posts
```

- [ ] **Step 2: First-run auth (interactive — run in terminal, not automated)**

```bash
python -c "
from ingest.telegram_fetcher import TelegramFetcher
posts = TelegramFetcher().fetch()
print(f'Fetched {len(posts)} posts from Telegram')
"
```

On first run, Telethon will prompt for your phone number and SMS code. After that, `elections_session.session` is saved and future runs are automatic.

- [ ] **Step 3: Add session file to `.gitignore`**

```bash
echo "elections_session.session" >> .gitignore
echo "*.session" >> .gitignore
echo ".env" >> .gitignore
```

- [ ] **Step 4: Commit**

```bash
git add ingest/telegram_fetcher.py .gitignore
git commit -m "feat: Telegram public channel fetcher for Tamil political content"
```

---

## Task 11: Google Trends Fetcher

**Files:**
- Create: `ingest/google_trends_fetcher.py`

- [ ] **Step 1: Write `ingest/google_trends_fetcher.py`**

```python
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
```

- [ ] **Step 2: Smoke test**

```bash
python -c "
from ingest.google_trends_fetcher import fetch_and_store
n = fetch_and_store()
print(f'Stored {n} trend records')
"
```

Expected: `Stored 5 trend records`

- [ ] **Step 3: Commit**

```bash
git add ingest/google_trends_fetcher.py
git commit -m "feat: Google Trends search interest fetcher for TN parties"
```

---

## Task 12: Scheduler (End-to-End Pipeline)

**Files:**
- Create: `scheduler.py`

- [ ] **Step 1: Write `scheduler.py`**

```python
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from storage.db import init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

scheduler = BlockingScheduler()

def run_full_ingest():
    from ingest.youtube_fetcher import YouTubeFetcher
    from ingest.reddit_fetcher import RedditFetcher
    from ingest.telegram_fetcher import TelegramFetcher
    from pipeline.preprocessor import preprocess
    from pipeline.party_extractor import extract_mentions
    from pipeline.sentiment_model import score_text
    from storage.db import get_session
    from storage.models import RawPost, PartyMention, SentimentScore

    session = get_session()
    fetchers = [YouTubeFetcher(), RedditFetcher(), TelegramFetcher()]
    all_posts = []

    for fetcher in fetchers:
        try:
            posts = fetcher.fetch()
            log.info(f"{fetcher.__class__.__name__}: fetched {len(posts)} posts")
            all_posts.extend(posts)
        except Exception as e:
            log.error(f"{fetcher.__class__.__name__} failed: {e}")

    clean = preprocess(all_posts)
    log.info(f"After preprocessing: {len(clean)} posts")
    saved = 0

    for post_data in clean:
        if session.query(RawPost).filter_by(post_id=post_data.post_id).first():
            continue
        raw = RawPost(
            source=post_data.source,
            post_id=post_data.post_id,
            text=post_data.text,
            url=post_data.url,
            lang=post_data.lang,
            author=post_data.author,
            engagement=post_data.engagement,
            posted_at=post_data.posted_at,
        )
        session.add(raw)
        session.flush()

        for party, mention_type in extract_mentions(post_data.text):
            model_score, model_confidence = score_text(post_data.text)
            session.add(PartyMention(post_id=raw.id, party=party, mention_type=mention_type))
            session.add(SentimentScore(
                post_id=raw.id,
                party=party,
                model_score=model_score,
                model_confidence=model_confidence,
                final_score=model_score,
            ))
        saved += 1

    session.commit()
    session.close()
    log.info(f"Saved {saved} new posts")

def run_aggregation():
    from pipeline.aggregator import roll_up_hourly, roll_up_daily
    roll_up_hourly()
    roll_up_daily()

def run_trends_ingest():
    from ingest.google_trends_fetcher import fetch_and_store
    n = fetch_and_store()
    log.info(f"Google Trends: stored {n} records")

def run_llm_judge():
    from pipeline.llm_judge import sample_and_score
    n = sample_and_score(n=200)
    log.info(f"LLM judge: scored {n} posts")


scheduler.add_job(run_full_ingest, "interval", hours=2, id="full_ingest")
scheduler.add_job(run_aggregation, "interval", hours=1, id="aggregation")
scheduler.add_job(run_trends_ingest, "interval", hours=6, id="trends_ingest")
scheduler.add_job(run_llm_judge, "cron", hour=2, id="llm_judge")

if __name__ == "__main__":
    init_db()
    log.info("Running initial ingest on startup...")
    run_full_ingest()
    run_aggregation()
    log.info("Starting scheduler...")
    scheduler.start()
```

- [ ] **Step 2: Test end-to-end pipeline manually**

```bash
python -c "
from storage.db import init_db
from scheduler import run_full_ingest, run_aggregation
init_db()
run_full_ingest()
run_aggregation()
print('Pipeline run complete')
"
```

Expected: Log lines showing fetched counts, no unhandled exceptions.

```bash
python -c "
from storage.db import get_session
from storage.models import RawPost, TrendsDaily
session = get_session()
print('Raw posts:', session.query(RawPost).count())
print('Trends daily:', session.query(TrendsDaily).count())
"
```

Expected: non-zero `Raw posts` count.

- [ ] **Step 3: Commit**

```bash
git add scheduler.py
git commit -m "feat: APScheduler pipeline orchestrating ingest, sentiment, aggregation"
```

---

## Task 13: Dashboard Components

**Files:**
- Create: `dashboard/components/metrics.py`
- Create: `dashboard/components/charts.py`

- [ ] **Step 1: Write `dashboard/components/metrics.py`**

```python
def confidence_badge(level: str) -> str:
    badges = {
        "high": "🟢 High confidence",
        "medium": "🟡 Medium confidence",
        "low": "🔴 Low confidence",
    }
    return badges.get(level, "⚪ Unknown")

def sentiment_label(score: float) -> str:
    if score > 0.33:
        return "Positive"
    elif score < -0.33:
        return "Negative"
    return "Neutral"
```

- [ ] **Step 2: Write `dashboard/components/charts.py`**

```python
from typing import List
import pandas as pd
import plotly.graph_objects as go

PARTY_COLORS = {
    "DMK": "#E41E20",
    "AIADMK": "#00A651",
    "BJP": "#FF671F",
    "VCK": "#0066CC",
    "PMK": "#FFD700",
}

def sentiment_timeline(df: pd.DataFrame, parties: List[str]) -> go.Figure:
    """
    df columns: date, party, sentiment_index
    """
    fig = go.Figure()
    for party in parties:
        pdata = df[df["party"] == party].sort_values("date")
        if pdata.empty:
            continue
        fig.add_trace(go.Scatter(
            x=pdata["date"],
            y=pdata["sentiment_index"],
            name=party,
            mode="lines+markers",
            line={"color": PARTY_COLORS.get(party, "#999"), "width": 2},
        ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
    fig.update_layout(
        title="Party Sentiment Index Over Time",
        xaxis_title="Date",
        yaxis_title="Sentiment (-1 to +1)",
        yaxis={"range": [-1, 1]},
        hovermode="x unified",
        legend_title="Party",
    )
    return fig

def source_stacked_bar(df: pd.DataFrame) -> go.Figure:
    """
    df columns: date, source, post_count
    """
    fig = go.Figure()
    for source in df["source"].unique():
        sdata = df[df["source"] == source].sort_values("date")
        fig.add_trace(go.Bar(x=sdata["date"], y=sdata["post_count"], name=source))
    fig.update_layout(barmode="stack", title="Post Volume by Source", xaxis_title="Date", yaxis_title="Posts")
    return fig

def topic_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    df columns: party, topic, count
    """
    pivot = df.pivot_table(index="party", columns="topic", values="count", fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="RdYlGn",
        zmid=0,
    ))
    fig.update_layout(title="Party × Topic Frequency")
    return fig

def sentiment_gauge(party: str, value: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 2),
        title={"text": party, "font": {"size": 14}},
        number={"font": {"size": 18}},
        gauge={
            "axis": {"range": [-1, 1], "tickwidth": 1},
            "bar": {"color": "#2ecc71" if value > 0 else "#e74c3c"},
            "steps": [
                {"range": [-1, -0.33], "color": "#ffcccc"},
                {"range": [-0.33, 0.33], "color": "#ffffcc"},
                {"range": [0.33, 1], "color": "#ccffcc"},
            ],
        },
    ))
    fig.update_layout(height=200, margin={"l": 10, "r": 10, "t": 40, "b": 10})
    return fig
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/components/metrics.py dashboard/components/charts.py
git commit -m "feat: Plotly chart builders and confidence metrics for dashboard"
```

---

## Task 14: Overview Page

**Files:**
- Create: `dashboard/pages/overview.py`

- [ ] **Step 1: Write `dashboard/pages/overview.py`**

```python
import streamlit as st
from datetime import date, timedelta
from storage.db import get_session
from storage.models import TrendsDaily, RawPost, HourlyAggregate
from dashboard.components.charts import sentiment_gauge
from dashboard.components.metrics import confidence_badge

PARTIES = ["DMK", "AIADMK", "BJP", "VCK", "PMK"]

st.title("TN Election 2026 — Sentiment Overview")

session = get_session()
today = date.today()

rows = (
    session.query(TrendsDaily)
    .filter(TrendsDaily.state == "TN")
    .filter(TrendsDaily.date >= today - timedelta(days=1))
    .all()
)
total_posts_24h = session.query(RawPost).filter(RawPost.collected_at >= today - timedelta(days=1)).count()
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
```

- [ ] **Step 2: Smoke test (run from `elections/` directory)**

```bash
streamlit run dashboard/app.py
```

Navigate to Overview — should show gauges for each party (or "No data" if DB is empty).

- [ ] **Step 3: Commit**

```bash
git add dashboard/pages/overview.py
git commit -m "feat: dashboard overview page with per-party sentiment gauges"
```

---

## Task 15: Trends Page

**Files:**
- Create: `dashboard/pages/trends.py`

- [ ] **Step 1: Write `dashboard/pages/trends.py`**

```python
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from storage.db import get_session
from storage.models import TrendsDaily
from dashboard.components.charts import sentiment_timeline

PARTIES = ["DMK", "AIADMK", "BJP", "VCK", "PMK"]

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
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/pages/trends.py
git commit -m "feat: dashboard trends page with time-series party sentiment chart"
```

---

## Task 16: Sources Page

**Files:**
- Create: `dashboard/pages/sources.py`

- [ ] **Step 1: Write `dashboard/pages/sources.py`**

```python
import streamlit as st
import pandas as pd
import json
from datetime import date, timedelta
from storage.db import get_session
from storage.models import HourlyAggregate, RawPost
from dashboard.components.charts import source_stacked_bar

st.title("Source Breakdown")

session = get_session()
rows = (
    session.query(HourlyAggregate)
    .filter(HourlyAggregate.state == "TN")
    .filter(HourlyAggregate.hour >= date.today() - timedelta(days=7))
    .all()
)

lang_rows = (
    session.query(RawPost.lang, RawPost.source)
    .filter(RawPost.collected_at >= date.today() - timedelta(days=7))
    .all()
)
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
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/pages/sources.py
git commit -m "feat: dashboard source breakdown page"
```

---

## Task 17: Topics Page

**Files:**
- Create: `dashboard/pages/topics.py`

- [ ] **Step 1: Write `dashboard/pages/topics.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/pages/topics.py
git commit -m "feat: dashboard topic heatmap page driven by LLM labels"
```

---

## Task 18: Results Day Page

**Files:**
- Create: `dashboard/pages/results_day.py`

- [ ] **Step 1: Write `dashboard/pages/results_day.py`**

```python
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
```

- [ ] **Step 2: Test Results Day mode**

Set `RESULTS_DAY=true` in `.env`, restart Streamlit, verify "Results Day" page appears and the results input form renders.

- [ ] **Step 3: Commit**

```bash
git add dashboard/pages/results_day.py
git commit -m "feat: results day page with predicted vs actual seat comparison"
```

---

## Task 19: Dashboard Entry Point

**Files:**
- Create: `dashboard/app.py`

- [ ] **Step 1: Write `dashboard/app.py`**

```python
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
```

- [ ] **Step 2: Full dashboard smoke test**

```bash
streamlit run dashboard/app.py
```

- Open browser at `http://localhost:8501`
- Verify all 4 pages (or 5 if `RESULTS_DAY=true`) are listed in sidebar
- Verify Overview loads without Python exceptions
- Verify Trends page loads
- Verify Sources page loads
- Verify Topics page shows "No topic labels yet" if LLM hasn't run

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add dashboard/app.py
git commit -m "feat: Streamlit multi-page app with conditional Results Day mode"
```

---

## Task 20: Deployment Setup

**Files:**
- Create: `.streamlit/config.toml`
- Create: `Procfile` (for Railway/Heroku)
- Modify: `scheduler.py` (make `DATABASE_URL` point to PostgreSQL)

> Deployment target: Streamlit Community Cloud (dashboard) + Railway/VPS (scheduler). The scheduler cannot run on Streamlit Community Cloud — it needs a separate process.

- [ ] **Step 1: Create `.streamlit/config.toml`**

```toml
[server]
headless = true
port = 8501

[theme]
primaryColor = "#E41E20"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

- [ ] **Step 2: Create `Procfile` for Railway (scheduler process)**

```
worker: python scheduler.py
```

- [ ] **Step 3: Verify PostgreSQL migration**

Switch `DATABASE_URL` in `.env` to your PostgreSQL connection string (Railway provides one). Run:

```bash
python -c "from storage.db import init_db; init_db(); print('DB initialized')"
```

Expected: `DB initialized` — all 6 tables created in PostgreSQL.

- [ ] **Step 4: Deploy dashboard to Streamlit Community Cloud**

1. Push the repo to GitHub
2. Go to share.streamlit.io
3. New app → select repo → main file: `dashboard/app.py`
4. Add secrets (same as `.env`) in the Streamlit secrets manager

- [ ] **Step 5: Deploy scheduler to Railway**

1. `railway init` in project root
2. `railway up` — deploys the `worker` Procfile process
3. Add environment variables in Railway dashboard (same as `.env`)

- [ ] **Step 6: Final commit**

```bash
git add .streamlit/config.toml Procfile
git commit -m "feat: deployment config for Streamlit Cloud + Railway scheduler"
```

---

## Verification Checklist

- [ ] `pytest tests/ -v` — all tests pass
- [ ] `python scheduler.py` — runs full ingest + aggregation without unhandled exceptions
- [ ] DB has non-zero `raw_posts`, `party_mentions`, `sentiment_scores` after one ingest run
- [ ] `streamlit run dashboard/app.py` — all pages load without errors
- [ ] Overview gauges show non-zero sentiment after DB is populated
- [ ] Trends page shows time-series chart for at least one party
- [ ] `RESULTS_DAY=true` — Results Day page appears in sidebar, results input renders
- [ ] Google Trends smoke: `search_interest` table populated after `run_trends_ingest()`
- [ ] LLM judge smoke: run `sample_and_score(n=5)` with real `ANTHROPIC_API_KEY`, verify topic labels appear in `sentiment_scores`

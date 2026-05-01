# Tamil Nadu 2026 Election Sentiment Tracker — Design Spec

**Date:** 2026-05-01
**Target:** Tamil Nadu Assembly Elections (due May 2026)
**Use case:** Personal/research — track per-party sentiment trends leading up to and on results day

---

## Problem

Indian state elections generate massive social media discourse in both regional languages and English. There's no lightweight, free tool that aggregates this signal into a coherent party-level sentiment tracker with calibrated confidence scores. This project fills that gap for Tamil Nadu 2026.

---

## Goals

1. Collect social media posts about TN election parties (DMK, AIADMK, BJP, VCK, PMK) from free sources every 2 hours
2. Score each post's sentiment toward the mentioned party using a multilingual transformer model
3. Run a daily high-confidence calibration sample through Claude API (200–300 posts)
4. Display sentiment trends in a Streamlit dashboard with confidence indicators
5. On results day: show live sentiment during counting + predicted-vs-actual comparison

---

## Architecture

```
[Data Sources]          [Pipeline]              [Storage]        [Dashboard]
YouTube comments ──┐
Reddit posts       ├── Preprocess → Party   ── SQLite/PG ────── Streamlit
Telegram channels  ┘   Extract  → XLM-RoBERTa  └─ hourly_agg       + Plotly
                                 ↓ daily sample
Google Trends ──────────────────────────────── search_interest
(interest index, not text)       Claude API
                                 (calibration)
```

Google Trends returns a search interest index (0–100), not text — it bypasses the NLP pipeline and goes directly to the `search_interest` table as a corroborating volume/momentum signal.

---

## Data Sources

| Source | Library | Content | Est. Volume/Day | Language |
|---|---|---|---|---|
| YouTube Data API v3 | `google-api-python-client` | Comments on Thanthi TV, SunNews, Puthiya Thalaimurai, Polimer News videos | 5K–30K/video | Tamil + English |
| Reddit | `praw` | r/Chennai, r/TamilNadu, r/india (TN posts) | 200–500 | English |
| Telegram public channels | `telethon` | Tamil political public channels | 1K–5K | Tamil |
| Google Trends | `pytrends` | Party name search interest, geo=IN-TN | Index only | N/A |
| Claude API (sample) | `anthropic` | Daily calibration batch | 200–300 | Tamil + English |

Fetch schedule: YouTube/Reddit/Telegram every 2h. Google Trends every 6h.

---

## Party Keyword Dictionary

```python
PARTY_KEYWORDS = {
    "DMK":    ["dmk", "திமுக", "#dmk", "mkstalin", "mk stalin", "stalin",
               "உதயநிதி", "udhayanidhi", "tr baalu", "duraimurugan"],
    "AIADMK": ["aiadmk", "அதிமுக", "#aiadmk", "eps", "edappadi", "palaniswami",
               "இபிஎஸ்", "o panneerselvam", "ops"],
    "BJP":    ["bjp", "பாஜக", "#bjp", "annamalai", "அண்ணாமலை", "modi",
               "நரேந்திர மோடி", "tamilnadu bjp", "tamilisai"],
    "VCK":    ["vck", "விடுதலை சிறுத்தைகள்", "thirumavalavan", "thiruma",
               "திருமாவளவன்"],
    "PMK":    ["pmk", "பாமக", "ramadoss", "anbumani", "அன்புமணி"],
}
```

---

## NLP Pipeline

### Fast Path (all posts, every run)

**Model:** `cardiffnlp/twitter-xlm-roberta-base-sentiment`
- Multilingual RoBERTa fine-tuned on Twitter; handles Tamil natively
- Output: `positive / negative / neutral` + softmax probability (0–1)
- Party attribution via keyword match before inference
- Multi-party posts: each party mention scored independently

### High-Confidence Path (daily, Claude API)

Sample 200–300 posts/day from: borderline model confidence (0.40–0.65), top-50 engagement posts, multi-party mentions.

Claude prompt returns structured JSON:
```json
{
  "party": "DMK|AIADMK|BJP|VCK|PMK|OTHER|MULTIPLE",
  "sentiment": "positive|negative|neutral|mixed",
  "confidence": "high|medium|low",
  "topic": "development|corruption|welfare|leadership|caste|religion|other"
}
```

### Confidence Score Formula

```python
def compute_confidence(model_prob, source_count, post_volume_24h, llm_agreement_rate=None):
    volume_factor = min(1.0, math.log10(max(post_volume_24h, 1)) / 3.0)
    diversity_factor = {1: 0.5, 2: 0.75}.get(source_count, 1.0)
    base = (model_prob * 0.4) + (volume_factor * 0.3) + (diversity_factor * 0.3)
    if llm_agreement_rate is not None:
        base = (base * 0.5) + (llm_agreement_rate * 0.5)
    return round(base, 3)
```

**Sentiment Index:** Normalized -1.0 to +1.0, rolling 24h exponential weighted mean.

---

## Storage Schema (SQLite → PostgreSQL)

### `raw_posts`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| source | TEXT | youtube/reddit/telegram |
| post_id | TEXT | Source-native ID (dedup key) |
| url | TEXT | |
| text | TEXT | |
| lang | TEXT | ISO 639-1: ta/en |
| author | TEXT | |
| engagement | INTEGER | likes/upvotes/views |
| posted_at | DATETIME | |
| collected_at | DATETIME | |

### `party_mentions`
| Column | Type |
|---|---|
| id | INTEGER PK |
| post_id | INTEGER FK → raw_posts |
| party | TEXT |
| mention_type | TEXT: direct/candidate/hashtag |

### `sentiment_scores`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| post_id | INTEGER FK | |
| party | TEXT | |
| model_score | FLOAT | -1 to 1 |
| model_confidence | FLOAT | 0–1 |
| llm_score | FLOAT | NULL until sampled |
| llm_confidence | TEXT | high/medium/low |
| topic | TEXT | NULL until sampled |
| final_score | FLOAT | weighted combination |
| scored_at | DATETIME | |

### `hourly_aggregates`
| Column | Type |
|---|---|
| state | TEXT |
| party | TEXT |
| hour | DATETIME (truncated to hour) |
| avg_sentiment | FLOAT |
| post_count | INTEGER |
| source_breakdown | JSON |
| confidence_level | TEXT |

### `search_interest` (Google Trends)
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| party | TEXT | |
| date | DATE | |
| interest_value | INTEGER | 0–100 |
| geo | TEXT | IN-TN |
| collected_at | DATETIME | |

### `trends_daily`
| Column | Type |
|---|---|
| state | TEXT |
| party | TEXT |
| date | DATE |
| sentiment_index | FLOAT (-1 to 1) |
| volume_index | INTEGER |
| confidence_level | TEXT |
| dominant_topic | TEXT |

---

## Dashboard (Streamlit + Plotly)

### Pages

| Page | Key Content |
|---|---|
| Overview | Gauge charts per party (current sentiment index), confidence badge, 24h post count |
| Trend Lines | Time-series line chart with confidence bands, 7/30/90 day selector, per-party toggles |
| Source Breakdown | Stacked bar (volume by source), language split pie |
| Topic Heatmap | Party × topic heatmap (intensity = frequency × valence), powered by LLM labels |
| Results Day | Live sentiment during counting; predicted-vs-actual seat comparison after results |

Results Day mode unlocks via `RESULTS_DAY=true` in `.env`.

---

## Scheduler

| Job | Interval | Action |
|---|---|---|
| Full ingest | Every 2h | YouTube + Reddit + Telegram |
| Aggregation | Every 1h | Roll up to `hourly_aggregates` + `trends_daily` |
| Trends ingest | Every 6h | Google Trends → `search_interest` |
| LLM judge | Daily 2 AM | Claude API sample → update sentiment_scores |

---

## Why Not Spark or Flink

At ~10K–50K posts/day, the full pipeline runs in under 5 minutes on a single process. Flink is only justified with a genuine real-time event stream (Kafka + X API Filtered Stream). Current sources are polled every 2h — plain Python is the right call. Revisit if X API is added.

---

## Key Dependencies

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
```

---

## Implementation Phases

| Phase | Steps | Deliverable |
|---|---|---|
| 1: Foundation | Project structure, SQLAlchemy models, YouTube fetcher, preprocessor, party extractor | Can collect Tamil YouTube comments and identify party mentions |
| 2: Sentiment Engine | XLM-RoBERTa inference, aggregator, LLM judge, confidence calculator | End-to-end: post → scored → DB |
| 3: Remaining Sources | Reddit, Telegram, Google Trends fetchers + APScheduler | All sources collecting on schedule |
| 4: Dashboard | All 5 Streamlit pages | Runnable dashboard with real data |
| 5: Deployment | SQLite → PostgreSQL, Streamlit Community Cloud / VPS | Accessible publicly, runs 24/7 |

---

## Verification Checklist

- [ ] Unit tests: party keyword extraction, sentiment normalization, confidence formula
- [ ] Integration test: 50-post sample runs end-to-end with correct DB rows
- [ ] Dashboard: all 5 pages load without error (`streamlit run dashboard/app.py`)
- [ ] LLM test: 5 posts through Claude API, JSON response parsed correctly
- [ ] Results Day: `RESULTS_DAY=true` enables mode, results input form renders

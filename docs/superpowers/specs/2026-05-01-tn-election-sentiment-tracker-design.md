# Tamil Nadu 2026 Election Sentiment Tracker — Design Spec

**Date:** 2026-05-01
**Target:** Tamil Nadu Assembly Elections (May 4, 2026)
**Use case:** Personal/research — track per-party sentiment trends leading up to and on results day

> **As-built note:** This document reflects the final implemented state. The original design used 5 individual parties (DMK, AIADMK, BJP, VCK, PMK) and XLM-RoBERTa as the primary scorer. Both were revised during implementation — see [Deviations from original design](#deviations-from-original-design).

---

## Problem

Indian state elections generate massive social media discourse in both Tamil and English. There's no lightweight, free tool that aggregates this signal into a coherent party-level sentiment tracker with calibrated confidence scores. This project fills that gap for Tamil Nadu 2026.

---

## Goals

1. Collect social media posts about TN election parties from YouTube and Telegram every 2 hours
2. Score each post's **electoral support** (not just generic sentiment) toward the mentioned party
3. Run LLM-based scoring on all posts using a local or cloud model
4. Display sentiment trends in a Streamlit dashboard with confidence indicators
5. On results day: show predicted sentiment vs actual seat counts per party

---

## Architecture

```
[Data Sources]           [Pipeline]                [Storage]       [Dashboard]
YouTube (17 channels) ──┐
Telegram (11 channels) ─┼── Preprocess ──── Party ── SQLite ──────── Streamlit
Reddit (disabled) ───── ┘   (dedup,         Extract   hourly_agg      + Plotly
                             spam filter,    (keyword  trends_daily    5 pages
                             lang detect)    /regex)       │
                                  │                        │
                             XLM-RoBERTa             LLM Judge
                             (base score)          (vote-intent,
                                                  batch scoring)
Google Trends ────────────────────────────── search_interest
(interest index, not text — bypasses NLP)
```

---

## Party Structure (as-built)

TN 2026 is contested by 4 alliance blocks, not 5 individual parties:

| Alliance | Parties | Key Figures |
|---|---|---|
| **DMK+** | DMK + VCK + Congress + Left | Stalin, Udhayanidhi, Thirumavalavan |
| **ADMK+** | AIADMK + BJP + PMK | Edappadi, Annamalai, Anbumani |
| **TVK** | Thalapathy Vijay's new party | Vijay (Thalapathy) |
| **NTK** | Naam Tamilar Katchi | Seeman |

---

## Data Sources (as-built)

| Source | Library | Content | Language |
|---|---|---|---|
| YouTube Data API v3 | `google-api-python-client` | 17 channels: 5 original Tamil regional + 5 additional Tamil news + 7 national English news. 50 videos/query, 3 comment pages/video | Tamil + English |
| Telegram | `telethon` | 11 channels: Tamil news + NTK/TVK/DMK political channels. 7-day lookback, 500 msg/channel | Tamil |
| Reddit | `praw` | Disabled — Reddit Responsible Builder Policy blocked new API access | English |
| Google Trends | `pytrends` | Party search interest index, geo=IN-TN | N/A (index only) |

Fetch schedule: YouTube + Telegram every 2h. Google Trends every 6h.

---

## NLP Pipeline (as-built)

### Stage 1: XLM-RoBERTa base scoring (all posts)

**Model:** `cardiffnlp/twitter-xlm-roberta-base-sentiment`

Uses `top_k=3` to get all three class probabilities, then computes a **probability-weighted score**:

```python
score = P(positive) * 1.0 + P(neutral) * 0.0 + P(negative) * (-1.0)
```

This gives a continuous score in [-1, +1] rather than hard -1/0/+1 labels. Stored as `model_score` and initially as `final_score`.

**Why this matters:** The original design used `top_k=1` (hard labels), which produced scores clustered around 0 with most posts landing in the neutral zone. Probability weighting gives meaningful differentiation.

### Stage 2: LLM vote-intent scoring (all posts, every 2h)

**Key insight:** Generic sentiment ("positive/negative") is a weak predictor of election outcomes. Fan enthusiasm about Vijay ≠ TVK vote intent. Criticism of EPS that still shows respect ≠ ADMK support. The LLM stage reframes scoring as:

> *Does this post indicate electoral support or opposition for [PARTY] in the Tamil Nadu 2026 election?*

**Backends** (switchable via `LLM_BACKEND` in `.env`):

| Backend | Model | Cost | Tamil quality |
|---|---|---|---|
| `ollama` (default) | `qwen2.5:7b` local | Free | Good |
| `openai` | `gpt-4o-mini` | ~$0.45/6K posts | Good |
| `anthropic` | `claude-haiku-4-5-20251001` | ~$0.30/6K posts | Best |

Posts are scored in batches of 10. `final_score` is set entirely from the LLM score, overriding XLM-RoBERTa.

**Prompt (abbreviated):**
```
You are analyzing Tamil Nadu 2026 state assembly election social media posts.
For each post, score the ELECTORAL SUPPORT for the specified party.
- Celebrity/fan admiration ≠ electoral support
- Just mentioning a party without stance = 0
Score: +1.0 = strong support, 0.0 = neutral, -1.0 = strong opposition
Return JSON array: [{"score": float, "confidence": "high|medium|low", "topic": "..."}]
```

### Confidence score formula

```python
def compute_confidence(model_prob, source_count, post_volume_24h, llm_agreement_rate=None):
    volume_factor = min(1.0, math.log10(max(post_volume_24h, 1)) / 3.0)
    diversity_factor = {1: 0.4, 2: 0.75}.get(source_count, 1.0)
    base = (model_prob * 0.35) + (volume_factor * 0.35) + (diversity_factor * 0.3)
    if llm_agreement_rate is not None:
        base = (base * 0.5) + (llm_agreement_rate * 0.5)
    return round(min(max(base, 0.0), 1.0), 3)
```

---

## Storage Schema

### `raw_posts`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| source | TEXT | youtube / telegram / reddit |
| post_id | TEXT | Source-native ID (dedup key) |
| url | TEXT | |
| text | TEXT | |
| lang | TEXT | ISO 639-1 (ta/en) — unreliable for Tamil, langdetect misidentifies Tamil as Indonesian/Estonian |
| author | TEXT | |
| engagement | INTEGER | likes/upvotes/views |
| posted_at | DATETIME | |
| collected_at | DATETIME | |

### `party_mentions`
| Column | Type |
|---|---|
| id | INTEGER PK |
| post_id | INTEGER FK → raw_posts |
| party | TEXT: DMK+ / ADMK+ / TVK / NTK |
| mention_type | TEXT: direct / candidate / hashtag |

### `sentiment_scores`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| post_id | INTEGER FK | |
| party | TEXT | |
| model_score | FLOAT | XLM-RoBERTa probability-weighted score |
| model_confidence | FLOAT | max class probability |
| llm_score | FLOAT | NULL until LLM scored |
| llm_confidence | TEXT | high / medium / low |
| topic | TEXT | LLM-assigned topic label |
| final_score | FLOAT | = llm_score when available, else model_score |
| scored_at | DATETIME | |

### `hourly_aggregates`
| Column | Type |
|---|---|
| state | TEXT (TN) |
| party | TEXT |
| hour | DATETIME (truncated to hour) |
| avg_sentiment | FLOAT |
| post_count | INTEGER |
| source_breakdown | JSON |
| confidence_level | TEXT: high / medium / low |

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
| **Overview** | Gauge charts per party. Sentiment index -1 to +1, labelled Negative/Neutral/Positive. Neutral zone is ±0.15. Confidence badge + 24h post count. |
| **Trend Lines** | Time-series line chart. 7/30/90 day range selector. Per-party colour-coded lines. |
| **Source Breakdown** | Stacked bar chart by source, language split pie. |
| **Topic Heatmap** | Party × topic heatmap. Intensity = frequency × valence. Powered by LLM topic labels. |
| **Results Day** | Unlocks via `RESULTS_DAY=true`. Shows 30-day avg sentiment + actual seat input form + rank accuracy score. |

**Gauge threshold:** Neutral zone ±0.15 (original design used ±0.33, which caused most parties to display as neutral).

---

## Scheduler (as-built)

| Job | Interval | Notes |
|---|---|---|
| Full ingest | Every 2h | YouTube + Telegram (Reddit disabled) |
| LLM scoring | Every 2.5h | Scores all posts with `llm_score IS NULL` |
| Aggregation | Every 1h | Roll up to `hourly_aggregates` + `trends_daily` |
| Google Trends | Every 6h | `search_interest` table |

---

## Why Not Spark or Flink

At ~40K posts/day, the full pipeline runs in under 10 minutes on a single process. Flink is only justified with a genuine real-time event stream (Kafka + X API Filtered Stream). Current sources are polled every 2h — plain Python + APScheduler is the right call. Revisit if X API Basic ($100/mo) is added.

---

## Deviations from original design

| Original | As-built | Reason |
|---|---|---|
| 5 parties: DMK, AIADMK, BJP, VCK, PMK | 4 alliance blocks: DMK+, ADMK+, TVK, NTK | TN 2026 reality — parties contest as alliances; VCK is within DMK+, BJP within ADMK+ |
| XLM-RoBERTa hard labels (top_k=1) as primary scorer | Probability-weighted XLM-R + LLM vote-intent scoring as primary | Hard labels produced 66% of posts with <0.60 confidence; all parties appeared neutral |
| Claude API for 200-post daily calibration sample | LLM scores ALL posts, every 2h, via configurable backend | Sampling 200 posts/day was insufficient to move the aggregate signal |
| Neutral zone ±0.33 | Neutral zone ±0.15 | ±0.33 caused parties with avg score of -0.32 to display as yellow/neutral |
| Reddit as data source | Reddit disabled | Reddit Responsible Builder Policy blocked new API access |
| 5 YouTube channels | 17 YouTube channels | Added 5 Tamil news + 7 national English news channels for volume |
| LLM judge runs daily at 2 AM | LLM judge runs every 2.5h | Daily run meant new posts sat unscored for up to 24h |

---

## Future evolution

### Short term (post May 4)
- **Tamil-specific model:** Add `l3cube-pune/tamil-sentiment-lg` as a free local scorer for Tamil posts, replacing Qwen for that language segment. Route by detected language.
- **Language detection fix:** Replace `langdetect` with Unicode range check for Tamil script — langdetect misidentifies Tamil as Swahili/Indonesian/Estonian ~35% of the time.
- **Engagement weighting:** High-engagement posts (many likes/views) should carry more weight in aggregation than zero-engagement comments.

### Medium term
- **X/Twitter API:** X API Basic ($100/mo) would add the highest-signal source for TN election discourse. At that scale, consider Kafka + Flink for sub-second results-day updates.
- **PostgreSQL migration:** Move from SQLite to PostgreSQL (Railway or Supabase free tier) for concurrent access and better query performance at scale.
- **Deployment:** Streamlit Community Cloud (dashboard) + Railway (scheduler worker). Procfile is already set up.

### Long term
- **Multi-state expansion:** Karnataka, Andhra Pradesh, Delhi — parameterise state/party config, add language-specific models for Kannada/Telugu/Hindi.
- **Seat prediction model:** Train a simple regression on historical sentiment → seat count data once May 4 results are in. Use as a calibration layer for future elections.
- **Confidence calibration:** After results day, compute Brier score (predicted sentiment rank vs actual seat rank) and use it to re-weight the confidence formula.

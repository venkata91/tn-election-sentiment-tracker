# TN Election 2026 Sentiment Tracker

Real-time sentiment analysis tracker for the Tamil Nadu 2026 Assembly Elections. Collects social media posts from YouTube and Telegram, scores electoral support per party using a local or cloud LLM, and displays trends in a Streamlit dashboard.

## What it tracks

Four alliance blocks for TN 2026:

| Alliance | Key parties / leaders |
|---|---|
| **DMK+** | DMK, VCK, Congress, Left — Stalin, Udhayanidhi, Thirumavalavan |
| **ADMK+** | AIADMK, BJP, PMK — Edappadi, Annamalai, Anbumani |
| **TVK** | Thalapathy Vijay's new party |
| **NTK** | Naam Tamilar Katchi — Seeman |

## Architecture

```
YouTube (17 channels) ──┐
Telegram (11 channels) ─┼── Preprocess ── Party Extractor ── LLM Scorer ── SQLite ── Streamlit
                         │   (dedup,         (keyword                       (hourly +   (5 pages)
                         └── spam filter)     regex)                         daily agg)
```

**LLM scoring** uses a vote-intent prompt (electoral support, not generic sentiment) and supports three interchangeable backends:
- **Ollama** (default, free) — `qwen2.5:7b` running locally
- **OpenAI** — `gpt-4o-mini`
- **Anthropic** — `claude-haiku-4-5-20251001`

XLM-RoBERTa provides probability-weighted base scores; the LLM backend re-scores using a vote-intent framing and overrides `final_score`.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For local LLM scoring (default), install [Ollama](https://ollama.com) and pull the model:

```bash
ollama pull qwen2.5:7b
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Minimum required to run:
```
YOUTUBE_API_KEY=       # Google Cloud Console → YouTube Data API v3
```

Optional (each enables an additional data source or LLM backend):
```
TELEGRAM_API_ID=       # my.telegram.org → API development tools
TELEGRAM_API_HASH=
OPENAI_API_KEY=        # platform.openai.com
ANTHROPIC_API_KEY=     # console.anthropic.com
LLM_BACKEND=ollama     # ollama | openai | anthropic
```

### 3. Initialise the database and run first ingest

```bash
PYTHONPATH=. python run_ingest.py
```

### 4. Start the dashboard

```bash
PYTHONPATH=. streamlit run dashboard/app.py
```

### 5. Start the scheduler (background ingestion every 2h)

```bash
PYTHONPATH=. python scheduler.py &
```

## Telegram one-time auth

Telethon requires a one-time phone verification to create a session file:

```bash
PYTHONPATH=. python3 -c "
import asyncio
from telethon import TelegramClient
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH
async def auth():
    async with TelegramClient('elections_session', TELEGRAM_API_ID, TELEGRAM_API_HASH) as c:
        print('Authorised:', await c.get_me())
asyncio.run(auth())
"
```

After this runs once, `elections_session.session` is saved and future fetches are silent.

## Dashboard pages

| Page | Description |
|---|---|
| **Overview** | Sentiment gauges per party (-1 negative → +1 positive), 24h post count |
| **Trend Lines** | Party sentiment over 7 / 30 / 90 days |
| **Source Breakdown** | Post volume by source and language split |
| **Topic Heatmap** | Party × topic heatmap from LLM topic labels |
| **Results Day** | Unlocks on election day (`RESULTS_DAY=true`) — predicted sentiment vs actual seats |

## Scheduler jobs

| Job | Interval |
|---|---|
| Full ingest (YouTube + Telegram) | Every 2h |
| LLM scoring of new posts | Every 2.5h |
| Hourly + daily aggregation | Every 1h |
| Google Trends | Every 6h |

## Project structure

```
elections/
├── ingest/
│   ├── youtube_fetcher.py      # 17 channels + search queries, 3 comment pages
│   ├── telegram_fetcher.py     # 11 Tamil political/news channels, 7-day lookback
│   ├── reddit_fetcher.py       # r/Chennai, r/TamilNadu (needs API key)
│   └── google_trends_fetcher.py
├── pipeline/
│   ├── preprocessor.py         # dedup, spam filter, lang detect
│   ├── party_extractor.py      # keyword/regex party attribution
│   ├── sentiment_model.py      # XLM-RoBERTa probability-weighted base scores
│   ├── llm_judge.py            # vote-intent LLM scoring (Ollama/OpenAI/Anthropic)
│   └── aggregator.py           # hourly + daily roll-ups
├── storage/
│   ├── db.py
│   └── models.py               # 5 SQLAlchemy tables
├── dashboard/
│   ├── app.py
│   ├── pages/                  # 5 Streamlit pages
│   └── components/             # Plotly chart builders, confidence metrics
├── tests/
├── scheduler.py                # APScheduler
├── config.py                   # All config + party keyword dict
├── run_ingest.py               # One-shot ingest script
└── .env.example
```

## Results Day (May 4, 2026)

Set `RESULTS_DAY=true` in `.env` before starting the dashboard. The Results Day page shows:
- 30-day average sentiment per party (pre-election prediction)
- Input fields for actual ECI seat counts
- Side-by-side rank comparison: sentiment rank vs seat rank
- Rank accuracy score

## Future improvements

See [`docs/superpowers/specs/2026-05-01-tn-election-sentiment-tracker-design.md`](docs/superpowers/specs/2026-05-01-tn-election-sentiment-tracker-design.md) for full design spec and evolution roadmap including:
- Twitter/X API integration (requires Basic tier, $100/mo)
- PostgreSQL migration for production deployment
- Fine-tuned Tamil sentiment model (`l3cube-pune/tamil-sentiment-lg`) as free LLM fallback
- Streamlit Community Cloud or Railway deployment

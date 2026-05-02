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

    try:
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
        log.info(f"Saved {saved} new posts")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

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

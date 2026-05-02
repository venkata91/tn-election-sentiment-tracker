import math
from datetime import datetime, timedelta, time
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
    diversity_factor = {1: 0.4, 2: 0.75}.get(source_count, 1.0)
    base = (model_prob * 0.35) + (volume_factor * 0.35) + (diversity_factor * 0.3)
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

    parties = ["DMK+", "ADMK+", "TVK", "NTK"]
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
    from datetime import date
    session = get_session()
    today = date.today()

    parties = ["DMK+", "ADMK+", "TVK", "NTK"]
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

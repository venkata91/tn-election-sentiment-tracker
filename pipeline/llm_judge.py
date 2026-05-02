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

_client: Optional[anthropic.Anthropic] = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client

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
        if data["sentiment"] not in ("positive", "negative", "neutral", "mixed"):
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None

def sample_and_score(n: int = 200) -> int:
    """Score up to n borderline posts via Claude API. Returns count successfully scored."""
    session = get_session()
    try:
        client = _get_client()

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
                if score_row.model_score is None:
                    continue
                score_row.llm_score = SENTIMENT_TO_SCORE.get(data["sentiment"], 0.0)
                score_row.llm_confidence = data["confidence"]
                score_row.topic = data["topic"]
                score_row.final_score = (score_row.model_score * 0.4) + (score_row.llm_score * 0.6)
                scored += 1
            except anthropic.AuthenticationError:
                raise
            except anthropic.RateLimitError:
                break
            except Exception:
                continue

        session.commit()
        return scored
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

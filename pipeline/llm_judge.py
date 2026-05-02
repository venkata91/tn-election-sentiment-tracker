import json
import logging
from typing import Optional
from config import ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENAI_MODEL, LLM_BACKEND, OLLAMA_MODEL, OLLAMA_BASE_URL
from storage.db import get_session
from storage.models import SentimentScore, RawPost

log = logging.getLogger(__name__)

_BATCH_SIZE = 10


def _build_batch_prompt(items: list[tuple[str, str]]) -> str:
    entries = []
    for i, (text, party) in enumerate(items, 1):
        entries.append(f"[{i}] Party: {party}\nPost: {text[:300]}")

    return (
        "You are analyzing Tamil Nadu 2026 state assembly election social media posts.\n"
        "For each post, score the ELECTORAL SUPPORT for the specified party.\n\n"
        "Important distinctions:\n"
        "- Celebrity/fan admiration ≠ electoral support (e.g. liking Vijay ≠ voting TVK)\n"
        "- Criticism of a party = negative score even if politely stated\n"
        "- Just mentioning a party without a clear stance = 0\n"
        "- Posts may be in Tamil, Tanglish (Tamil+English mix), or English\n\n"
        "Score: +1.0 = strong electoral support/vote intent, "
        "0.0 = neutral/just mentioning, "
        "-1.0 = strong opposition/criticism\n\n"
        + "\n\n".join(entries)
        + f"\n\nReturn ONLY a JSON array of exactly {len(items)} objects, no other text:\n"
        '[{"score": <float -1.0 to 1.0>, "confidence": "high|medium|low", '
        '"topic": "development|corruption|welfare|leadership|caste|religion|candidate|other"}]'
    )


def _parse_batch_response(raw: str, expected: int) -> list[Optional[dict]]:
    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return [None] * expected
        data = json.loads(raw[start:end])
        if not isinstance(data, list) or len(data) != expected:
            return [None] * expected
        results = []
        for item in data:
            if not isinstance(item, dict) or "score" not in item:
                results.append(None)
                continue
            score = item["score"]
            if not isinstance(score, (int, float)):
                results.append(None)
                continue
            results.append({
                "score": round(max(-1.0, min(1.0, float(score))), 4),
                "confidence": item.get("confidence", "low"),
                "topic": item.get("topic", "other"),
            })
        return results
    except (json.JSONDecodeError, ValueError):
        return [None] * expected


def _call_ollama(prompt: str) -> str:
    import ollama
    client = ollama.Client(host=OLLAMA_BASE_URL)
    response = client.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": 400},
    )
    return response["response"]


def _call_anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=400,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _call_llm(prompt: str) -> str:
    if LLM_BACKEND == "anthropic":
        return _call_anthropic(prompt)
    if LLM_BACKEND == "openai":
        return _call_openai(prompt)
    return _call_ollama(prompt)


def score_all_unscored(batch_size: int = _BATCH_SIZE) -> int:
    """Score all posts with no llm_score. Returns count scored."""
    session = get_session()
    try:
        candidates = (
            session.query(SentimentScore, RawPost)
            .join(RawPost, SentimentScore.post_id == RawPost.id)
            .filter(SentimentScore.llm_score.is_(None))
            .order_by(RawPost.engagement.desc(), RawPost.collected_at.desc())
            .all()
        )

        if not candidates:
            return 0

        _model_label = {"ollama": OLLAMA_MODEL, "anthropic": "claude-haiku", "openai": OPENAI_MODEL}.get(LLM_BACKEND, LLM_BACKEND)
        log.info(f"LLM judge ({LLM_BACKEND}/{_model_label}): scoring {len(candidates)} posts")
        scored = 0

        for i in range(0, len(candidates), batch_size):
            batch = candidates[i : i + batch_size]
            items = [(post.text, score_row.party) for score_row, post in batch]

            try:
                raw = _call_llm(_build_batch_prompt(items))
                results = _parse_batch_response(raw, len(batch))

                for j, result in enumerate(results):
                    if result is None:
                        continue
                    score_row = batch[j][0]
                    score_row.llm_score = result["score"]
                    score_row.llm_confidence = result["confidence"]
                    score_row.topic = result["topic"]
                    score_row.final_score = result["score"]
                    scored += 1

                if scored > 0 and scored % 500 == 0:
                    session.commit()
                    log.info(f"LLM judge: {scored}/{len(candidates)} scored")

            except Exception as e:
                log.warning(f"LLM judge batch {i // batch_size} failed: {e}")
                continue

        session.commit()
        log.info(f"LLM judge: finished, scored {scored} posts")
        return scored

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def sample_and_score(n: int = 200) -> int:
    """Legacy entry point — delegates to score_all_unscored."""
    return score_all_unscored()

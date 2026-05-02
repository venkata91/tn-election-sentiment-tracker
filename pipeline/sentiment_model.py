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
    result = classifier(text[:512])[0][0]
    label = result["label"].lower()
    confidence = float(result["score"])
    score = LABEL_TO_SCORE.get(label, 0.0)
    return score, confidence

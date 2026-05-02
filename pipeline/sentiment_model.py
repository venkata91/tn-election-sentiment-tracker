from transformers import pipeline as hf_pipeline
from typing import Tuple

_classifier = None

def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = hf_pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            top_k=3,
            truncation=True,
            max_length=512,
        )
    return _classifier

def score_text(text: str) -> Tuple[float, float]:
    """
    Returns (sentiment_score, confidence) where:
      sentiment_score: probability-weighted score in [-1.0, +1.0]
        = P(positive)*1.0 + P(neutral)*0.0 + P(negative)*(-1.0)
      confidence: highest class probability (0.0 to 1.0)
    """
    classifier = _get_classifier()
    results = classifier(text[:512])[0]  # list of 3 {label, score} dicts
    probs = {r["label"].lower(): float(r["score"]) for r in results}
    weighted = probs.get("positive", 0.0) - probs.get("negative", 0.0)
    confidence = max(probs.values())
    return round(weighted, 4), round(confidence, 4)

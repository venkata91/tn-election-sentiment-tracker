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

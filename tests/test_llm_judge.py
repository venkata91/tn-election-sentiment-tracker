import pytest
from unittest.mock import patch, MagicMock
from pipeline.llm_judge import _build_prompt, _parse_response, SENTIMENT_TO_SCORE

def test_build_prompt_contains_text():
    prompt = _build_prompt("DMK is winning Tamil Nadu")
    assert "DMK is winning Tamil Nadu" in prompt

def test_build_prompt_contains_instructions():
    prompt = _build_prompt("some text")
    assert "party" in prompt.lower()
    assert "sentiment" in prompt.lower()
    assert "JSON" in prompt

def test_parse_valid_json():
    raw = '{"party": "DMK", "sentiment": "positive", "confidence": "high", "topic": "leadership"}'
    result = _parse_response(raw)
    assert result is not None
    assert result["party"] == "DMK"
    assert result["sentiment"] == "positive"
    assert result["confidence"] == "high"
    assert result["topic"] == "leadership"

def test_parse_invalid_json_returns_none():
    result = _parse_response("not json at all")
    assert result is None

def test_parse_missing_field_returns_none():
    raw = '{"party": "DMK"}'
    result = _parse_response(raw)
    assert result is None

def test_sentiment_to_score_mapping():
    assert SENTIMENT_TO_SCORE["positive"] == 1.0
    assert SENTIMENT_TO_SCORE["negative"] == -1.0
    assert SENTIMENT_TO_SCORE["neutral"] == 0.0
    assert SENTIMENT_TO_SCORE["mixed"] == 0.0

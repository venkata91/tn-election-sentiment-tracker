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

def test_sample_and_score_returns_count():
    from unittest.mock import patch, MagicMock
    from pipeline.llm_judge import sample_and_score

    mock_score_row = MagicMock()
    mock_score_row.llm_score = None
    mock_score_row.model_confidence = 0.5
    mock_score_row.model_score = 0.3
    mock_post_row = MagicMock()
    mock_post_row.text = "DMK is winning"
    mock_post_row.engagement = 100

    mock_session = MagicMock()
    mock_session.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        (mock_score_row, mock_post_row)
    ]

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"party": "DMK", "sentiment": "positive", "confidence": "high", "topic": "leadership"}')]

    with patch("pipeline.llm_judge.get_session", return_value=mock_session):
        with patch("pipeline.llm_judge._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_message
            mock_get_client.return_value = mock_client
            result = sample_and_score(n=1)

    assert result == 1
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()

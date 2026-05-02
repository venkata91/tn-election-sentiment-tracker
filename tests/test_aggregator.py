import pytest
from pipeline.aggregator import compute_confidence, confidence_label

def test_high_volume_high_confidence():
    score = compute_confidence(model_prob=0.9, source_count=3, post_volume_24h=10000)
    assert score >= 0.7

def test_single_source_low_confidence():
    score = compute_confidence(model_prob=0.9, source_count=1, post_volume_24h=10)
    assert score < 0.6

def test_llm_agreement_boosts_confidence():
    without_llm = compute_confidence(0.6, 2, 1000)
    with_llm = compute_confidence(0.6, 2, 1000, llm_agreement_rate=0.9)
    assert with_llm > without_llm

def test_llm_disagreement_lowers_confidence():
    without_llm = compute_confidence(0.6, 2, 1000)
    with_llm = compute_confidence(0.6, 2, 1000, llm_agreement_rate=0.1)
    assert with_llm < without_llm

def test_confidence_label_high():
    assert confidence_label(0.8) == "high"

def test_confidence_label_medium():
    assert confidence_label(0.55) == "medium"

def test_confidence_label_low():
    assert confidence_label(0.3) == "low"

def test_confidence_score_range():
    score = compute_confidence(0.5, 2, 500)
    assert 0.0 <= score <= 1.0

def test_zero_volume_doesnt_crash():
    score = compute_confidence(0.5, 1, 0)
    assert score >= 0.0

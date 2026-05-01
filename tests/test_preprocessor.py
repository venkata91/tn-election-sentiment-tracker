import pytest
from ingest.base import RawPostData
from pipeline.preprocessor import is_spam, detect_language, preprocess, _reset_seen_hashes

@pytest.fixture(autouse=True)
def reset_seen():
    _reset_seen_hashes()
    yield
    _reset_seen_hashes()

def _post(text: str, post_id: str = "1") -> RawPostData:
    return RawPostData(source="youtube", post_id=post_id, text=text)

def test_is_spam_too_short():
    assert is_spam("hi") is True

def test_is_spam_one_word():
    assert is_spam("DMK") is True

def test_is_spam_hashtag_heavy():
    assert is_spam("#a #b #c #d #e some text") is True

def test_is_spam_normal_text():
    assert is_spam("I think DMK will win the Tamil Nadu election this time around") is False

def test_detect_language_english():
    lang = detect_language("I love cricket and Tamil Nadu politics is very interesting")
    assert lang == "en"

def test_detect_language_unknown_short():
    lang = detect_language("xyz")
    assert lang == "unknown"

def test_preprocess_dedup_same_text():
    same = "DMK is going to win in Tamil Nadu 2026 for sure this time"
    posts = [_post(same, "1"), _post(same, "2")]
    result = preprocess(posts)
    assert len(result) == 1

def test_preprocess_filters_spam():
    posts = [_post("hi", "1"), _post("DMK is going to win in Tamil Nadu 2026", "2")]
    result = preprocess(posts)
    assert len(result) == 1
    assert result[0].post_id == "2"

def test_preprocess_adds_language():
    posts = [_post("I support the Tamil Nadu election outcome this year", "1")]
    result = preprocess(posts)
    assert result[0].lang is not None
    assert result[0].lang != "unknown"

def test_preprocess_keeps_lang_if_set():
    post = _post("Some text here about Tamil Nadu elections clearly", "1")
    post.lang = "ta"
    result = preprocess([post])
    assert result[0].lang == "ta"

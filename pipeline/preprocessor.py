import hashlib
from langdetect import detect
from typing import List
from ingest.base import RawPostData

_seen_hashes: set = set()

def _reset_seen_hashes() -> None:
    """Reset cross-batch dedup state. Call in tests to ensure isolation."""
    _seen_hashes.clear()

def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def detect_language(text: str) -> str:
    if len(text) <= 3:
        return "unknown"
    try:
        return detect(text)
    except Exception:
        return "unknown"

def is_spam(text: str) -> bool:
    words = text.split()
    if len(words) < 4:
        return True
    hashtag_ratio = sum(1 for w in words if w.startswith("#")) / len(words)
    return hashtag_ratio > 0.5

def preprocess(posts: List[RawPostData]) -> List[RawPostData]:
    """Deduplicate within batch, filter spam, detect language."""
    clean = []
    local_seen: set = set()
    for post in posts:
        if is_spam(post.text):
            continue
        h = _content_hash(post.text)
        if h in _seen_hashes or h in local_seen:
            continue
        local_seen.add(h)
        _seen_hashes.add(h)
        if not post.lang:
            post.lang = detect_language(post.text)
        clean.append(post)
    return clean

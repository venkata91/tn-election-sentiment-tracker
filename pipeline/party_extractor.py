import re
from config import PARTY_KEYWORDS
from typing import List, Tuple

_DIRECT_NAMES = {"dmk", "aiadmk", "bjp", "vck", "pmk",
                  "திமுக", "அதிமுக", "பாஜக", "பாமக",
                  "விடுதலை சிறுத்தைகள்"}

def _matches(keyword: str, text_lower: str) -> bool:
    """Word-boundary-aware keyword match. Hashtags must be preceded by whitespace or start of string."""
    if keyword.startswith("#"):
        # hashtag: must be at word boundary (whitespace or start)
        pattern = r"(?:^|\s)" + re.escape(keyword)
        return bool(re.search(pattern, text_lower))
    else:
        # regular keyword: whole-word match using word boundaries
        # negative lookbehind for '#' prevents matching inside hashtags (e.g. "dmk" inside "#dmk")
        pattern = r"(?<!#)\b" + re.escape(keyword) + r"\b"
        return bool(re.search(pattern, text_lower))

def extract_mentions(text: str) -> List[Tuple[str, str]]:
    """
    Return list of (party, mention_type) for each party mentioned in text.
    mention_type: 'direct' | 'candidate' | 'hashtag'
    One entry per party maximum (first matching keyword wins).
    """
    text_lower = text.lower()
    results = []
    for party, keywords in PARTY_KEYWORDS.items():
        for keyword in keywords:
            kw_lower = keyword.lower()
            if _matches(kw_lower, text_lower):
                if kw_lower.startswith("#"):
                    mention_type = "hashtag"
                elif kw_lower in _DIRECT_NAMES:
                    mention_type = "direct"
                else:
                    mention_type = "candidate"
                results.append((party, mention_type))
                break  # one entry per party
    return results

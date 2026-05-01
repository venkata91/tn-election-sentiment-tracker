from config import PARTY_KEYWORDS
from typing import List, Tuple

_DIRECT_NAMES = {"dmk", "aiadmk", "bjp", "vck", "pmk",
                  "திமுக", "அதிமுக", "பாஜக", "பாமக",
                  "விடுதலை சிறுத்தைகள்"}

def extract_mentions(text: str) -> List[Tuple[str, str]]:
    """
    Return list of (party, mention_type) for each party mentioned in text.
    mention_type: 'direct' | 'candidate' | 'hashtag'
    One entry per party maximum (first matching keyword wins).
    """
    text_lower = text.lower()
    results = []
    for party, keywords in PARTY_KEYWORDS.items():
        # Sort keywords: hashtags first, then direct names, then candidates
        sorted_keywords = sorted(keywords, key=lambda kw: (not kw.startswith("#"), kw.lower() not in _DIRECT_NAMES))
        for keyword in sorted_keywords:
            kw_lower = keyword.lower()
            if kw_lower in text_lower:
                if kw_lower.startswith("#"):
                    mention_type = "hashtag"
                elif kw_lower in _DIRECT_NAMES:
                    mention_type = "direct"
                else:
                    mention_type = "candidate"
                results.append((party, mention_type))
                break  # one entry per party
    return results

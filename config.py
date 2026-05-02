import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "elections-tracker/1.0")
_raw_telegram_id = os.getenv("TELEGRAM_API_ID", "0").strip()
TELEGRAM_API_ID = int(_raw_telegram_id) if _raw_telegram_id else 0
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///elections.db")
TARGET_STATE = os.getenv("TARGET_STATE", "TN")
RESULTS_DAY = os.getenv("RESULTS_DAY", "false").lower() == "true"

PARTY_KEYWORDS = {
    "DMK": [
        "dmk", "திமுக", "#dmk", "mkstalin", "mk stalin", "stalin",
        "உதயநிதி", "udhayanidhi", "tr baalu", "duraimurugan",
    ],
    "AIADMK": [
        "aiadmk", "அதிமுக", "#aiadmk", "eps", "edappadi", "palaniswami",
        "இபிஎஸ்", "o panneerselvam", "ops",
    ],
    "BJP": [
        "bjp", "பாஜக", "#bjp", "annamalai", "அண்ணாமலை", "modi",
        "நரேந்திர மோடி", "tamilnadu bjp", "tamilisai",
    ],
    "VCK": [
        "vck", "விடுதலை சிறுத்தைகள்", "thirumavalavan", "thiruma",
        "திருமாவளவன்",
    ],
    "PMK": [
        "pmk", "பாமக", "ramadoss", "anbumani", "அன்புமணி",
    ],
}

YOUTUBE_CHANNELS = {
    # Verify channel IDs at youtube.com/@<handle> → About → Share → Copy channel ID
    "thanthi_tv": "UCu6HHfxLzniTEGJhYnqpAew",
    "sun_news": "UCn0QyOr3mNWNrFDzGJ5TnXA",
    "puthiya_thalaimurai": "UCiJbpLSiQbRFxzUVD2k25cw",
    "polimer_news": "UC9R3_MBmQKl8kGH4oY9byQA",
    "news_j": "UC6GoBiRtfoBZZB3c2U9Q7zg",
}

YOUTUBE_SEARCH_QUERIES = [
    "தமிழ்நாடு தேர்தல்",
    "TN election 2026",
    "DMK AIADMK BJP Tamil Nadu",
    "Stalin Annamalai EPS election",
]

TELEGRAM_CHANNELS = [
    "tamilpoliticsnews",
    "tnpoliticsupdates",
]

REDDIT_SUBREDDITS = ["Chennai", "TamilNadu", "india"]
REDDIT_SEARCH_TERMS = [
    "DMK", "AIADMK", "Stalin", "Edappadi", "Annamalai",
    "Tamil Nadu election", "TN BJP",
]

import warnings as _warnings
_OPTIONAL_KEYS = {
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
    "REDDIT_CLIENT_SECRET": REDDIT_CLIENT_SECRET,
    "TELEGRAM_API_HASH": TELEGRAM_API_HASH,
    "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
}
for _name, _val in _OPTIONAL_KEYS.items():
    if not _val:
        _warnings.warn(f"{_name} is not set — related features will be unavailable.", stacklevel=2)

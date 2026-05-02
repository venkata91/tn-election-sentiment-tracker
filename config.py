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
    "DMK+": [
        # DMK core
        "dmk", "திமுக", "#dmk", "mkstalin", "mk stalin", "stalin",
        "உதயநிதி", "udhayanidhi", "duraimurugan", "tr baalu",
        # Alliance partners (VCK, Congress, Left)
        "vck", "திருமாவளவன்", "thirumavalavan", "thiruma",
        "dmk alliance", "dmk அணி", "இந்திய கூட்டணி",
    ],
    "ADMK+": [
        # AIADMK core
        "aiadmk", "admk", "அதிமுக", "#aiadmk", "eps", "edappadi", "palaniswami",
        "இபிஎஸ்", "எடப்பாடி",
        # BJP alliance
        "bjp", "பாஜக", "#bjp", "annamalai", "அண்ணாமலை", "tamilisai",
        # PMK (likely with ADMK+)
        "pmk", "பாமக", "ramadoss", "anbumani", "அன்புமணி",
        "nda", "nda tamil",
    ],
    "TVK": [
        "tvk", "தமிழக வெற்றி கழகம்", "#tvk",
        "vijay", "விஜய்", "thalapathy vijay", "தலபதி விஜய்", "thalapathy",
        "actor vijay", "விஜய் கட்சி",
    ],
    "NTK": [
        "ntk", "நாம் தமிழர்", "நாம் தமிழர் கட்சி", "#ntk",
        "seeman", "சீமான்", "naam tamilar",
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
    "தமிழ்நாடு தேர்தல் 2026",
    "TN election 2026",
    "DMK ADMK TVK NTK Tamil Nadu",
    "Stalin Edappadi Vijay Seeman election",
    "தலபதி விஜய் TVK",
    "சீமான் NTK தேர்தல்",
]

TELEGRAM_CHANNELS = [
    "tamilpoliticsnews",
    "tnpoliticsupdates",
]

REDDIT_SUBREDDITS = ["Chennai", "TamilNadu", "india"]
REDDIT_SEARCH_TERMS = [
    "DMK", "AIADMK", "TVK", "NTK", "Seeman",
    "Stalin", "Edappadi", "Vijay TVK", "Thalapathy Vijay politics",
    "Tamil Nadu election 2026",
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

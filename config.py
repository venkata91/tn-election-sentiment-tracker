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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")   # "ollama" | "anthropic" | "openai"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
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
    # Verified channel IDs — confirm at youtube.com/@<handle> → Share → Copy channel ID
    "thanthi_tv":         "UCu6HHfxLzniTEGJhYnqpAew",
    "sun_news":           "UCn0QyOr3mNWNrFDzGJ5TnXA",
    "puthiya_thalaimurai":"UCiJbpLSiQbRFxzUVD2k25cw",
    "polimer_news":       "UC9R3_MBmQKl8kGH4oY9byQA",
    "news_j":             "UC6GoBiRtfoBZZB3c2U9Q7zg",
    # Additional Tamil news channels — verify IDs before enabling
    "raj_tv":             "UCbEBg43vl8ZBhWYFYGMiK0Q",
    "kalaignar_tv":       "UCcNEBFBjrWrATqOIhF6kMPg",
    "captain_tv":         "UCVTTPpYPMiMiJh-yQoN1BEg",
    "vendhar_tv":         "UCRWFSbif-RFENbBrSiez1DA",
    "sathiyam_tv":        "UCXv4GFWRqZfMSuMSEZFOF0A",
    # National English news channels
    "india_today":        "UCYPvAwZP8pZhSMW8qs7cVCw",
    "ndtv":               "UCZFMm1mMw0F81Z37aaEzTUA",
    "times_now":          "UC6RJ7-PaXg6TIH2BzZfTV7w",
    "republic_world":     "UCwqusr8YDwM-3mEYTDeJHzw",
    "cnn_news18":         "UCef1-8eOpJgud7szVPlZQAQ",
    "news18_india":       "UCPP3etACgdUWvizcES1dJ8Q",
    "mirror_now":         "UCWCEYVwSqr7Epo6sSCfUgiw",
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
    # Tamil news channels (broadcast — no join required)
    "thanthitv",
    "sunnewstamil",
    "puthiyathalaimurai",
    "polimernews",
    "rajtvnews",
    "kalaignartv",
    # Political / commentary channels
    "tamilpoliticsnews",
    "tnpoliticsupdates",
    "naamtamilar",          # NTK / Seeman updates
    "tvkofficial",          # TVK / Vijay's party
    "dmkofficialnews",      # DMK news
]

REDDIT_SUBREDDITS = ["Chennai", "TamilNadu", "india"]
REDDIT_SEARCH_TERMS = [
    "DMK", "AIADMK", "TVK", "NTK", "Seeman",
    "Stalin", "Edappadi", "Vijay TVK", "Thalapathy Vijay politics",
    "Tamil Nadu election 2026",
]

YOUTUBE_ENABLED = bool(YOUTUBE_API_KEY)
REDDIT_ENABLED = bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)
TELEGRAM_ENABLED = bool(TELEGRAM_API_ID and TELEGRAM_API_HASH)
ANTHROPIC_ENABLED = bool(ANTHROPIC_API_KEY)

import warnings as _warnings
_FLAGS = {
    "YOUTUBE": (YOUTUBE_ENABLED, "YOUTUBE_API_KEY"),
    "REDDIT": (REDDIT_ENABLED, "REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET"),
    "TELEGRAM": (TELEGRAM_ENABLED, "TELEGRAM_API_ID + TELEGRAM_API_HASH"),
    "ANTHROPIC (LLM judge)": (ANTHROPIC_ENABLED, "ANTHROPIC_API_KEY"),
}
for _source, (_ok, _keys) in _FLAGS.items():
    if not _ok:
        _warnings.warn(f"{_source} disabled — set {_keys} in .env to enable.", stacklevel=2)

"""
Configuration constants for WF Auto-Scouter.
Countries, tiers, genre tags, API keys, and filter thresholds.
"""

# ========================== API KEYS ==========================

### make your own apis and add them here.
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
LASTFM_API_KEY = ""  # Get from https://www.last.fm/api/account/create (free, instant)

MB_APP_NAME = "WF-AutoScouter"
MB_APP_VERSION = "3.0"
MB_CONTACT = "worldfestshows@saarang.org"

# ========================== COUNTRIES ==========================

COUNTRY_TIERS = {
    "Tier 1": ["Germany", "Finland", "Belgium", "Norway", "Philippines", "Italy", "Spain", "South Africa", "Singapore"],
    "Tier 2": ["France", "Malaysia", "United Kingdom", "Denmark", "Japan", "Netherlands", "Australia", "Canada", "Sweden"],
    "Tier 3": ["United States", "Indonesia", "Portugal", "Croatia", "Thailand", "Hungary", "Austria", "Argentina", "New Zealand", "Poland", "Switzerland", "South Korea", "Israel"],
    "Tier 4": ["Saudi Arabia", "Malta", "Czech Republic", "Mexico", "Nepal", "Bulgaria", "Mauritius", "Hong Kong", "Ireland", "Morocco", "Brazil", "Estonia"],
}

ALL_TARGET_COUNTRIES = [c for tier in COUNTRY_TIERS.values() for c in tier]

COUNTRY_TO_MB = {
    "Germany": "DE", "Finland": "FI", "Belgium": "BE", "Norway": "NO",
    "Philippines": "PH", "Italy": "IT", "Spain": "ES", "South Africa": "ZA",
    "Singapore": "SG", "France": "FR", "Malaysia": "MY", "United Kingdom": "GB",
    "Denmark": "DK", "Japan": "JP", "Netherlands": "NL", "Australia": "AU",
    "Canada": "CA", "Sweden": "SE", "United States": "US", "Indonesia": "ID",
    "Portugal": "PT", "Croatia": "HR", "Thailand": "TH", "Hungary": "HU",
    "Austria": "AT", "Argentina": "AR", "New Zealand": "NZ", "Poland": "PL",
    "Switzerland": "CH", "South Korea": "KR", "Israel": "IL", "Saudi Arabia": "SA",
    "Malta": "MT", "Czech Republic": "CZ", "Mexico": "MX", "Nepal": "NP",
    "Bulgaria": "BG", "Mauritius": "MU", "Ireland": "IE", "Morocco": "MA",
    "Brazil": "BR", "Estonia": "EE", "Hong Kong": "HK",
}

MB_TO_COUNTRY = {v: k for k, v in COUNTRY_TO_MB.items()}

# ========================== GENRE TAGS ==========================

GENRE_TAGS = [
    # Rock
    "rock", "indie rock", "alternative rock", "post-rock", "punk", "garage rock", "grunge",
    # Metal
    "metal", "heavy metal", "progressive metal", "metalcore", "death metal", "doom metal", "folk metal", "black metal", "thrash metal",
    # Electronic
    "electronic", "edm", "techno", "house", "synthwave", "ambient", "drum and bass",
    # Hip-hop
    "hip-hop", "hip hop", "rap", "grime",
    # Folk/Acoustic
    "folk", "indie folk", "folk rock", "singer-songwriter", "acoustic",
    # Jazz/Soul
    "jazz", "soul", "r&b", "neo-soul", "funk", "blues",
    # Pop
    "indie pop", "art pop", "synth-pop", "dream pop", "pop", "bedroom pop",
    # World/Other
    "world music", "fusion", "experimental", "psychedelic", "ska", "reggae",
    # Performance
    "beatbox", "lo-fi",
]

# Tags that indicate WF-relevant genres (for scoring)
WF_RELEVANT_GENRE_KEYWORDS = [
    'rock', 'metal', 'electronic', 'hip', 'rap', 'folk', 'jazz', 'soul',
    'pop', 'indie', 'punk', 'world', 'fusion', 'beat', 'reggae', 'funk',
    'blues', 'ska', 'grunge', 'ambient', 'techno', 'house', 'drum',
]

# ========================== FILTER THRESHOLDS ==========================

# Last.fm listener ranges for size classification
LASTFM_LISTENERS_TOO_BIG = 500000       # Above this = definitely too big for WF
LASTFM_LISTENERS_BIG = 100000           # 100K-500K = borderline big
LASTFM_LISTENERS_MEDIUM_HIGH = 50000    # 50K-100K = upper WF range
LASTFM_LISTENERS_MEDIUM_LOW = 5000      # 5K-50K = WF sweet spot
LASTFM_LISTENERS_SMALL = 1000           # 1K-5K = small but viable
LASTFM_LISTENERS_TOO_SMALL = 100        # Below this = probably too obscure

# Minimum tracks for a 40-50 min set
MIN_TRACKS_FOR_SET = 8

# Recent activity: must have released within this many years
MAX_YEARS_SINCE_RELEASE = 5

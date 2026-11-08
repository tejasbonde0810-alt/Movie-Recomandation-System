"""
Configuration settings for the Movie & Web Series Recommendation Engine.
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env", override=True)

class Config:
    # Flask settings
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    PORT = int(os.getenv("PORT", 5000))

    # TMDB API
    @classmethod
    def get_tmdb_token(cls) -> str:
        """Dynamically reload .env to detect newly added tokens without restarting."""
        load_dotenv(BASE_DIR / ".env", override=True)
        return (os.getenv("TMDB_BEARER_TOKEN") or "").strip()

    TMDB_BEARER_TOKEN = (os.getenv("TMDB_BEARER_TOKEN") or "").strip()
    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_REQUEST_TIMEOUT = 8  # seconds
    TMDB_MAX_RETRIES = 2

    # Database & Cache settings
    DATA_DIR = BASE_DIR / "data"
    DATABASE_PATH = DATA_DIR / "app_cache.db"
    CACHE_EXPIRATION_SECONDS = 86400  # 24 hours

    # Configurable Language Support
    # Note: 'original_language' indicates the language spoken, not necessarily the country of production.
    LANGUAGES = [
        {"code": "", "name": "All Languages", "industry": "Global"},
        {"code": "hi", "name": "Hindi", "industry": "Bollywood / Hindi Cinema"},
        {"code": "en", "name": "English", "industry": "Hollywood / English-language"},
        {"code": "te", "name": "Telugu", "industry": "Telugu Cinema (Tollywood)"},
        {"code": "ta", "name": "Tamil", "industry": "Tamil Cinema (Kollywood)"},
        {"code": "ml", "name": "Malayalam", "industry": "Malayalam Cinema (Mollywood)"},
        {"code": "kn", "name": "Kannada", "industry": "Kannada Cinema (Sandalwood)"},
        {"code": "bn", "name": "Bengali", "industry": "Bengali Cinema"},
        {"code": "mr", "name": "Marathi", "industry": "Marathi Cinema"},
        {"code": "pa", "name": "Punjabi", "industry": "Punjabi Cinema"},
        {"code": "ko", "name": "Korean", "industry": "Korean Cinema / K-Drama"},
        {"code": "ja", "name": "Japanese", "industry": "Japanese Cinema / Anime"},
        {"code": "zh", "name": "Chinese", "industry": "Chinese Cinema"},
        {"code": "es", "name": "Spanish", "industry": "Spanish-language Cinema"},
        {"code": "fr", "name": "French", "industry": "French Cinema"},
        {"code": "de", "name": "German", "industry": "German Cinema"},
        {"code": "it", "name": "Italian", "industry": "Italian Cinema"},
        {"code": "pt", "name": "Portuguese", "industry": "Portuguese Cinema"},
        {"code": "ru", "name": "Russian", "industry": "Russian Cinema"},
        {"code": "tr", "name": "Turkish", "industry": "Turkish Cinema / Dizi"},
        {"code": "ar", "name": "Arabic", "industry": "Arabic Cinema"},
        {"code": "th", "name": "Thai", "industry": "Thai Cinema"},
        {"code": "id", "name": "Indonesian", "industry": "Indonesian Cinema"},
        {"code": "fa", "name": "Persian", "industry": "Iranian Cinema"}
    ]

    # Pre-mapped standard TMDB movie genres
    MOVIE_GENRES = [
        {"id": 28, "name": "Action"},
        {"id": 12, "name": "Adventure"},
        {"id": 16, "name": "Animation"},
        {"id": 35, "name": "Comedy"},
        {"id": 80, "name": "Crime"},
        {"id": 99, "name": "Documentary"},
        {"id": 18, "name": "Drama"},
        {"id": 10751, "name": "Family"},
        {"id": 14, "name": "Fantasy"},
        {"id": 36, "name": "History"},
        {"id": 27, "name": "Horror"},
        {"id": 10402, "name": "Music"},
        {"id": 9648, "name": "Mystery"},
        {"id": 10749, "name": "Romance"},
        {"id": 878, "name": "Science Fiction"},
        {"id": 10770, "name": "TV Movie"},
        {"id": 53, "name": "Thriller"},
        {"id": 10752, "name": "War"},
        {"id": 37, "name": "Western"}
    ]

    # Pre-mapped standard TMDB TV genres
    TV_GENRES = [
        {"id": 10759, "name": "Action & Adventure"},
        {"id": 16, "name": "Animation"},
        {"id": 35, "name": "Comedy"},
        {"id": 80, "name": "Crime"},
        {"id": 99, "name": "Documentary"},
        {"id": 18, "name": "Drama"},
        {"id": 10751, "name": "Family"},
        {"id": 10762, "name": "Kids"},
        {"id": 9648, "name": "Mystery"},
        {"id": 10763, "name": "News"},
        {"id": 10764, "name": "Reality"},
        {"id": 10765, "name": "Sci-Fi & Fantasy"},
        {"id": 10766, "name": "Soap"},
        {"id": 10767, "name": "Talk"},
        {"id": 10768, "name": "War & Politics"},
        {"id": 37, "name": "Western"}
    ]

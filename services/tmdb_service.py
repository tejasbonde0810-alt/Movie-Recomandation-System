"""
TMDB API Integration Service.
Handles HTTP requests, timeouts, retries, caching, fallback mock data,
and normalization for Movies and TV Series.
"""
import requests
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from config import Config
from services.db import get_cached_api_response, set_cached_api_response
from services.mock_data import MOCK_MOVIES, MOCK_TV_SHOWS

logger = logging.getLogger(__name__)

# Fast genre lookup dictionaries
MOVIE_GENRE_MAP = {g["id"]: g["name"] for g in Config.MOVIE_GENRES}
TV_GENRE_MAP = {g["id"]: g["name"] for g in Config.TV_GENRES}
LANG_MAP = {lang["code"]: lang["name"] for lang in Config.LANGUAGES if lang["code"]}


class TMDBService:
    def __init__(self, bearer_token: Optional[str] = None):
        self._custom_token = bearer_token
        self.base_url = Config.TMDB_BASE_URL
        self.timeout = Config.TMDB_REQUEST_TIMEOUT
        self.session = requests.Session()
        self._cached_token = None
        self.auth_headers = {}
        self.api_key_param = None
        self._sync_token()

    def _sync_token(self) -> str:
        """Dynamically detect and reload token from .env."""
        token = self._custom_token if self._custom_token is not None else Config.get_tmdb_token()
        if token != self._cached_token:
            self._cached_token = token
            if token and len(token) > 10 and not token.startswith("your_"):
                # Bearer token (JWT v4) or v3 api_key
                if len(token) == 32 and "-" not in token and "." not in token:
                    self.auth_headers = {}
                    self.api_key_param = token
                else:
                    self.auth_headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json;charset=utf-8"
                    }
                    self.api_key_param = None
            else:
                self.auth_headers = {}
                self.api_key_param = None
        return self._cached_token or ""

    @property
    def has_token(self) -> bool:
        token = self._sync_token()
        return bool(token and len(token) > 10 and not token.startswith("your_"))

    @property
    def bearer_token(self) -> str:
        return self._sync_token()

    def _make_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Create a deterministic cache key from the endpoint and query params."""
        clean_params = {k: str(v) for k, v in sorted(params.items()) if v is not None and v != ""}
        serialized = f"{endpoint}:{json.dumps(clean_params, sort_keys=True)}"
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Execute request with retry logic and SQLite response caching.
        Returns empty dict or raises friendly Exception on failure.
        """
        if params is None:
            params = {}

        if self.api_key_param:
            params["api_key"] = self.api_key_param

        cache_key = self._make_cache_key(endpoint, params)
        if use_cache:
            cached = get_cached_api_response(cache_key)
            if cached is not None:
                return cached

        if not self.has_token:
            # Token not provided - caller can handle fallback
            raise PermissionError("TMDB Bearer token not configured. Please add your token to the .env file.")

        url = f"{self.base_url}{endpoint}"
        retries = Config.TMDB_MAX_RETRIES

        for attempt in range(retries + 1):
            try:
                response = self.session.get(
                    url,
                    headers=self.auth_headers,
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    if use_cache:
                        set_cached_api_response(cache_key, url, data)
                    return data
                elif response.status_code == 401:
                    raise PermissionError("Invalid TMDB API credentials. Please check your TMDB_BEARER_TOKEN in .env.")
                elif response.status_code == 404:
                    return {}
                elif response.status_code >= 500 and attempt < retries:
                    continue  # Retry on 5xx server errors
                else:
                    response.raise_for_status()
            except requests.RequestException as e:
                if attempt >= retries:
                    logger.error(f"TMDB request failed for {url}: {e}")
                    raise ConnectionError(f"Failed to communicate with TMDB API: {str(e)}")

        return {}

    # -------------------------------------------------------------
    # Formatting & Normalization Helpers
    # -------------------------------------------------------------
    @staticmethod
    def format_movie(item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a movie object into a standard schema."""
        movie_id = item.get("id")
        title = item.get("title") or item.get("original_title") or "Untitled"
        release_date = item.get("release_date") or ""
        year = release_date.split("-")[0] if release_date and "-" in release_date else (release_date or "N/A")
        lang = item.get("original_language", "en")
        lang_full = LANG_MAP.get(lang, lang.upper())
        vote_avg = round(float(item.get("vote_average", 0.0)), 1)
        overview = item.get("overview") or "No overview available."

        # Extract genres
        genres = []
        if "genres" in item and isinstance(item["genres"], list):
            genres = [g.get("name") for g in item["genres"] if g.get("name")]
        elif "genre_ids" in item and isinstance(item["genre_ids"], list):
            genres = [MOVIE_GENRE_MAP.get(gid) for gid in item["genre_ids"] if gid in MOVIE_GENRE_MAP]
        if not genres:
            genres = ["General"]

        # Extract director and cast if present
        credits = item.get("credits", {})
        directors = []
        for crew_member in credits.get("crew", []):
            if crew_member.get("job") == "Director":
                directors.append(crew_member.get("name"))
        director = ", ".join(directors[:2]) if directors else ""

        cast_list = [c.get("name") for c in credits.get("cast", [])[:4] if c.get("name")]

        # Extract keywords
        keywords_obj = item.get("keywords", {})
        keyword_list = []
        if isinstance(keywords_obj, dict):
            k_items = keywords_obj.get("keywords") or keywords_obj.get("results") or []
            keyword_list = [k.get("name") for k in k_items if k.get("name")]

        # Extract production countries and origin countries
        prod_countries = []
        for pc in item.get("production_countries", []):
            if pc.get("name"):
                prod_countries.append(pc["name"])
        origin_countries = item.get("origin_country", [])
        if isinstance(origin_countries, list) and not prod_countries:
            prod_countries = origin_countries

        return {
            "id": movie_id,
            "title": title,
            "release_year": year,
            "release_date": release_date,
            "original_language": lang,
            "language_name": lang_full,
            "production_countries": prod_countries,
            "production_country_string": ", ".join(prod_countries[:2]) if prod_countries else "",
            "genres": genres,
            "genre_string": ", ".join(genres),
            "vote_average": vote_avg,
            "overview": overview,
            "director": director,
            "cast": cast_list,
            "keywords": keyword_list,
            "media_type": "movie"
        }

    @staticmethod
    def format_tv(item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a TV series object into a standard schema."""
        tv_id = item.get("id")
        title = item.get("name") or item.get("original_name") or "Untitled"
        first_air_date = item.get("first_air_date") or ""
        year = first_air_date.split("-")[0] if first_air_date and "-" in first_air_date else (first_air_date or "N/A")
        lang = item.get("original_language", "en")
        lang_full = LANG_MAP.get(lang, lang.upper())
        vote_avg = round(float(item.get("vote_average", 0.0)), 1)
        overview = item.get("overview") or "No overview available."

        # Extract genres
        genres = []
        if "genres" in item and isinstance(item["genres"], list):
            genres = [g.get("name") for g in item["genres"] if g.get("name")]
        elif "genre_ids" in item and isinstance(item["genre_ids"], list):
            genres = [TV_GENRE_MAP.get(gid) for gid in item["genre_ids"] if gid in TV_GENRE_MAP]
        if not genres:
            genres = ["General"]

        # Extract creators and cast if present
        creators = [c.get("name") for c in item.get("created_by", []) if c.get("name")]
        credits = item.get("credits", {})
        if not creators:
            for crew_member in credits.get("crew", []):
                if crew_member.get("job") in ("Creator", "Executive Producer", "Director"):
                    creators.append(crew_member.get("name"))
        creator = ", ".join(creators[:2]) if creators else ""

        cast_list = [c.get("name") for c in credits.get("cast", [])[:4] if c.get("name")]

        # Extract keywords
        keywords_obj = item.get("keywords", {})
        keyword_list = []
        if isinstance(keywords_obj, dict):
            k_items = keywords_obj.get("results") or keywords_obj.get("keywords") or []
            keyword_list = [k.get("name") for k in k_items if k.get("name")]

        # Extract production countries and origin countries
        prod_countries = []
        for pc in item.get("production_countries", []):
            if pc.get("name"):
                prod_countries.append(pc["name"])
        origin_countries = item.get("origin_country", [])
        if isinstance(origin_countries, list) and not prod_countries:
            prod_countries = origin_countries

        return {
            "id": tv_id,
            "title": title,
            "release_year": year,
            "release_date": first_air_date,
            "original_language": lang,
            "language_name": lang_full,
            "production_countries": prod_countries,
            "production_country_string": ", ".join(prod_countries[:2]) if prod_countries else "",
            "genres": genres,
            "genre_string": ", ".join(genres),
            "vote_average": vote_avg,
            "overview": overview,
            "director": creator,
            "cast": cast_list,
            "keywords": keyword_list,
            "media_type": "tv"
        }

    # -------------------------------------------------------------
    # Movie Endpoints
    # -------------------------------------------------------------
    def search_movies(self, query: str, page: int = 1, language: str = "", year: str = "", genre: str = "") -> Dict[str, Any]:
        """Search movies with optional post-filtering."""
        if not self.has_token:
            return self._mock_movie_search(query, language=language, year=year, genre=genre)

        params = {"query": query, "page": page, "include_adult": "false"}
        if year:
            params["primary_release_year"] = year

        try:
            data = self._request("/search/movie", params)
            results = [self.format_movie(m) for m in data.get("results", [])]
            
            # Apply language/genre filters on search results if requested
            if language:
                results = [m for m in results if m["original_language"] == language]
            if genre:
                genre_lower = genre.lower()
                results = [m for m in results if any(g.lower() == genre_lower for g in m["genres"])]

            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": len(results),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Live movie search failed ({e}), falling back to mock dataset")
            return self._mock_movie_search(query, language=language, year=year, genre=genre)

    def get_trending_movies(self, time_window: str = "week", page: int = 1) -> Dict[str, Any]:
        """Fetch trending movies."""
        if not self.has_token:
            return self._mock_movie_list(page=page)

        try:
            data = self._request(f"/trending/movie/{time_window}", {"page": page})
            results = [self.format_movie(m) for m in data.get("results", [])]
            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": data.get("total_results", len(results)),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Trending movies failed ({e}), using mock dataset")
            return self._mock_movie_list(page=page)

    def discover_movies(self, language: str = "", genre: str = "", year: str = "",
                        sort_by: str = "popularity.desc", page: int = 1) -> Dict[str, Any]:
        """Discover movies with language, genre, year, and sorting filters."""
        if not self.has_token:
            return self._mock_movie_discover(language=language, genre=genre, year=year, sort_by=sort_by)

        params = {
            "page": page,
            "sort_by": sort_by,
            "include_adult": "false"
        }
        if language:
            params["with_original_language"] = language
        if year:
            params["primary_release_year"] = year
        if genre:
            # Check if genre is ID or name
            gid = None
            if str(genre).isdigit():
                gid = genre
            else:
                for k, v in MOVIE_GENRE_MAP.items():
                    if v.lower() == genre.lower():
                        gid = str(k)
                        break
            if gid:
                params["with_genres"] = gid

        try:
            data = self._request("/discover/movie", params)
            results = [self.format_movie(m) for m in data.get("results", [])]
            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": data.get("total_results", len(results)),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Discover movies failed ({e}), using mock dataset")
            return self._mock_movie_discover(language=language, genre=genre, year=year, sort_by=sort_by)

    def _mock_movie_detail(self, movie_id: int) -> Dict[str, Any]:
        for m in MOCK_MOVIES:
            if m["id"] == movie_id:
                return self.format_movie(m)
        return {
            "id": movie_id,
            "title": f"Movie #{movie_id}",
            "release_year": "2023",
            "original_language": "en",
            "genres": ["Drama"],
            "genre_string": "Drama",
            "vote_average": 7.5,
            "overview": "Detailed overview unavailable in offline mode.",
            "director": "",
            "cast": [],
            "keywords": [],
            "media_type": "movie"
        }

    def _mock_tv_detail(self, series_id: int) -> Dict[str, Any]:
        for s in MOCK_TV_SHOWS:
            if s["id"] == series_id:
                return self.format_tv(s)
        return {
            "id": series_id,
            "title": f"TV Series #{series_id}",
            "release_year": "2023",
            "original_language": "en",
            "genres": ["Drama"],
            "genre_string": "Drama",
            "vote_average": 7.8,
            "overview": "Detailed overview unavailable in offline mode.",
            "director": "",
            "cast": [],
            "keywords": [],
            "media_type": "tv"
        }

    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Fetch movie details including credits, keywords, and recommendations."""
        if not self.has_token:
            return self._mock_movie_detail(movie_id)

        try:
            data = self._request(
                f"/movie/{movie_id}",
                {"append_to_response": "credits,keywords,recommendations,similar"}
            )
            if not data:
                return self._mock_movie_detail(movie_id)
            return self.format_movie(data)
        except Exception as e:
            logger.warning(f"Get movie details failed for {movie_id}: {e}")
            return self._mock_movie_detail(movie_id)

    def get_movie_recommendation_candidates(self, movie_id: int) -> List[Dict[str, Any]]:
        """Fetch candidate movies for recommendation (TMDB recommendations + similar)."""
        candidates = []
        seen_ids = {movie_id}

        if not self.has_token:
            for m in MOCK_MOVIES:
                if m["id"] != movie_id:
                    candidates.append(self.format_movie(m))
            return candidates

        # 1. Fetch recommendations endpoint
        try:
            rec_data = self._request(f"/movie/{movie_id}/recommendations")
            for m in rec_data.get("results", []):
                mid = m.get("id")
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    candidates.append(self.format_movie(m))
        except Exception as e:
            logger.warning(f"Failed to fetch /movie/{movie_id}/recommendations: {e}")

        # 2. Fetch similar endpoint
        try:
            sim_data = self._request(f"/movie/{movie_id}/similar")
            for m in sim_data.get("results", []):
                mid = m.get("id")
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    candidates.append(self.format_movie(m))
        except Exception as e:
            logger.warning(f"Failed to fetch /movie/{movie_id}/similar: {e}")

        # Fallback to mock candidates if network failed or no candidates returned
        if not candidates:
            for m in MOCK_MOVIES:
                if m["id"] != movie_id:
                    candidates.append(self.format_movie(m))

        return candidates

    # -------------------------------------------------------------
    # TV Series Endpoints
    # -------------------------------------------------------------
    def search_tv(self, query: str, page: int = 1, language: str = "", year: str = "", genre: str = "") -> Dict[str, Any]:
        """Search TV series with optional post-filtering."""
        if not self.has_token:
            return self._mock_tv_search(query, language=language, year=year, genre=genre)

        params = {"query": query, "page": page, "include_adult": "false"}
        if year:
            params["first_air_date_year"] = year

        try:
            data = self._request("/search/tv", params)
            results = [self.format_tv(s) for s in data.get("results", [])]

            if language:
                results = [s for s in results if s["original_language"] == language]
            if genre:
                genre_lower = genre.lower()
                results = [s for s in results if any(g.lower() == genre_lower for g in s["genres"])]

            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": len(results),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Live TV search failed ({e}), using mock dataset")
            return self._mock_tv_search(query, language=language, year=year, genre=genre)

    def get_trending_tv(self, time_window: str = "week", page: int = 1) -> Dict[str, Any]:
        """Fetch trending TV shows."""
        if not self.has_token:
            return self._mock_tv_list(page=page)

        try:
            data = self._request(f"/trending/tv/{time_window}", {"page": page})
            results = [self.format_tv(s) for s in data.get("results", [])]
            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": data.get("total_results", len(results)),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Trending TV failed ({e}), using mock dataset")
            return self._mock_tv_list(page=page)

    def get_popular_tv(self, page: int = 1) -> Dict[str, Any]:
        """Fetch popular TV shows."""
        if not self.has_token:
            return self._mock_tv_list(page=page)

        try:
            data = self._request("/tv/popular", {"page": page})
            results = [self.format_tv(s) for s in data.get("results", [])]
            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": data.get("total_results", len(results)),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            return self._mock_tv_list(page=page)

    def get_top_rated_tv(self, page: int = 1) -> Dict[str, Any]:
        """Fetch top rated TV shows."""
        if not self.has_token:
            return self._mock_tv_list(page=page, sort_key="vote_average")

        try:
            data = self._request("/tv/top_rated", {"page": page})
            results = [self.format_tv(s) for s in data.get("results", [])]
            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": data.get("total_results", len(results)),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            return self._mock_tv_list(page=page, sort_key="vote_average")

    def discover_tv(self, language: str = "", genre: str = "", year: str = "",
                    sort_by: str = "popularity.desc", page: int = 1) -> Dict[str, Any]:
        """Discover TV series with filters."""
        if not self.has_token:
            return self._mock_tv_discover(language=language, genre=genre, year=year, sort_by=sort_by)

        params = {
            "page": page,
            "sort_by": sort_by,
            "include_adult": "false"
        }
        if language:
            params["with_original_language"] = language
        if year:
            params["first_air_date_year"] = year
        if genre:
            gid = None
            if str(genre).isdigit():
                gid = genre
            else:
                for k, v in TV_GENRE_MAP.items():
                    if v.lower() == genre.lower():
                        gid = str(k)
                        break
            if gid:
                params["with_genres"] = gid

        try:
            data = self._request("/discover/tv", params)
            results = [self.format_tv(s) for s in data.get("results", [])]
            return {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": data.get("total_results", len(results)),
                "results": results,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Discover TV failed ({e}), using mock dataset")
            return self._mock_tv_discover(language=language, genre=genre, year=year, sort_by=sort_by)

    def get_tv_details(self, series_id: int) -> Dict[str, Any]:
        """Fetch TV details including credits and keywords."""
        if not self.has_token:
            return self._mock_tv_detail(series_id)

        try:
            data = self._request(
                f"/tv/{series_id}",
                {"append_to_response": "credits,keywords,recommendations,similar"}
            )
            if not data:
                return self._mock_tv_detail(series_id)
            return self.format_tv(data)
        except Exception as e:
            logger.warning(f"Get TV details failed for {series_id}: {e}")
            return self._mock_tv_detail(series_id)

    def get_tv_recommendation_candidates(self, series_id: int) -> List[Dict[str, Any]]:
        """Fetch candidate TV shows for recommendation."""
        candidates = []
        seen_ids = {series_id}

        if not self.has_token:
            for s in MOCK_TV_SHOWS:
                if s["id"] != series_id:
                    candidates.append(self.format_tv(s))
            return candidates

        # 1. Recommendations endpoint
        try:
            rec_data = self._request(f"/tv/{series_id}/recommendations")
            for s in rec_data.get("results", []):
                sid = s.get("id")
                if sid and sid not in seen_ids:
                    seen_ids.add(sid)
                    candidates.append(self.format_tv(s))
        except Exception as e:
            logger.warning(f"Failed to fetch /tv/{series_id}/recommendations: {e}")

        # 2. Similar endpoint
        try:
            sim_data = self._request(f"/tv/{series_id}/similar")
            for s in sim_data.get("results", []):
                sid = s.get("id")
                if sid and sid not in seen_ids:
                    seen_ids.add(sid)
                    candidates.append(self.format_tv(s))
        except Exception as e:
            logger.warning(f"Failed to fetch /tv/{series_id}/similar: {e}")

        # Fallback to mock candidates if network failed or no candidates returned
        if not candidates:
            for s in MOCK_TV_SHOWS:
                if s["id"] != series_id:
                    candidates.append(self.format_tv(s))

        return candidates

    # -------------------------------------------------------------
    # Fallback / Mock implementations for offline or testing mode
    # -------------------------------------------------------------
    def _mock_movie_search(self, query: str, language: str = "", year: str = "", genre: str = "") -> Dict[str, Any]:
        q = query.lower()
        matched = []
        for m in MOCK_MOVIES:
            formatted = self.format_movie(m)
            title_match = q in formatted["title"].lower() or q in formatted["overview"].lower()
            lang_match = not language or formatted["original_language"] == language
            year_match = not year or formatted["release_year"] == year
            genre_match = not genre or any(genre.lower() == g.lower() for g in formatted["genres"])
            if (not query or title_match) and lang_match and year_match and genre_match:
                matched.append(formatted)
        return {"page": 1, "total_pages": 1, "total_results": len(matched), "results": matched, "is_mock": True}

    def _mock_movie_list(self, page: int = 1) -> Dict[str, Any]:
        results = [self.format_movie(m) for m in MOCK_MOVIES]
        return {"page": page, "total_pages": 1, "total_results": len(results), "results": results, "is_mock": True}

    def _mock_movie_discover(self, language: str = "", genre: str = "", year: str = "", sort_by: str = "popularity.desc") -> Dict[str, Any]:
        matched = []
        for m in MOCK_MOVIES:
            formatted = self.format_movie(m)
            lang_match = not language or formatted["original_language"] == language
            year_match = not year or formatted["release_year"] == year
            genre_match = not genre or any(genre.lower() == g.lower() for g in formatted["genres"])
            if lang_match and year_match and genre_match:
                matched.append(formatted)

        if "vote_average" in sort_by:
            matched.sort(key=lambda x: x["vote_average"], reverse=True)
        elif "primary_release_date" in sort_by:
            matched.sort(key=lambda x: x["release_date"], reverse=True)

        return {"page": 1, "total_pages": 1, "total_results": len(matched), "results": matched, "is_mock": True}

    def _mock_tv_search(self, query: str, language: str = "", year: str = "", genre: str = "") -> Dict[str, Any]:
        q = query.lower()
        matched = []
        for s in MOCK_TV_SHOWS:
            formatted = self.format_tv(s)
            title_match = q in formatted["title"].lower() or q in formatted["overview"].lower()
            lang_match = not language or formatted["original_language"] == language
            year_match = not year or formatted["release_year"] == year
            genre_match = not genre or any(genre.lower() == g.lower() for g in formatted["genres"])
            if (not query or title_match) and lang_match and year_match and genre_match:
                matched.append(formatted)
        return {"page": 1, "total_pages": 1, "total_results": len(matched), "results": matched, "is_mock": True}

    def _mock_tv_list(self, page: int = 1, sort_key: str = "popularity") -> Dict[str, Any]:
        results = [self.format_tv(s) for s in MOCK_TV_SHOWS]
        if sort_key == "vote_average":
            results.sort(key=lambda x: x["vote_average"], reverse=True)
        return {"page": page, "total_pages": 1, "total_results": len(results), "results": results, "is_mock": True}

    def _mock_tv_discover(self, language: str = "", genre: str = "", year: str = "", sort_by: str = "popularity.desc") -> Dict[str, Any]:
        matched = []
        for s in MOCK_TV_SHOWS:
            formatted = self.format_tv(s)
            lang_match = not language or formatted["original_language"] == language
            year_match = not year or formatted["release_year"] == year
            genre_match = not genre or any(genre.lower() == g.lower() for g in formatted["genres"])
            if lang_match and year_match and genre_match:
                matched.append(formatted)

        if "vote_average" in sort_by:
            matched.sort(key=lambda x: x["vote_average"], reverse=True)
        elif "first_air_date" in sort_by:
            matched.sort(key=lambda x: x["release_date"], reverse=True)

        return {"page": 1, "total_pages": 1, "total_results": len(matched), "results": matched, "is_mock": True}

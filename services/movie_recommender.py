"""
Movie Recommendation Service.
Implements content-based filtering using TF-IDF and Cosine Similarity
over metadata soups (genres, keywords, cast, director, and overview).
Handles newly discovered TMDB titles dynamically.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from services.tmdb_service import TMDBService
from services.db import save_title_metadata, get_title_metadata

logger = logging.getLogger(__name__)


def clean_token(name: str) -> str:
    """Normalize string into a single token suitable for TF-IDF (e.g. 'Christopher Nolan' -> 'ChristopherNolan')."""
    if not name:
        return ""
    return re.sub(r"[^\w]", "", name.strip())


def build_movie_metadata_soup(item: Dict[str, Any]) -> str:
    """
    Construct a weighted metadata soup for a movie.
    Heavily weights genres, director, and keywords, along with top cast and overview.
    """
    # 1. Genres (weighted 3x)
    genres = item.get("genres", [])
    genre_tokens = " ".join([f"genre_{clean_token(g)}" for g in genres if g])
    genre_soup = f"{genre_tokens} {genre_tokens} {genre_tokens}" if genre_tokens else ""

    # 2. Keywords (weighted 2x)
    keywords = item.get("keywords", [])
    keyword_tokens = " ".join([f"kw_{clean_token(k)}" for k in keywords if k])
    keyword_soup = f"{keyword_tokens} {keyword_tokens}" if keyword_tokens else ""

    # 3. Director (weighted 3x)
    director = item.get("director", "")
    dir_tokens = " ".join([f"dir_{clean_token(d)}" for d in director.split(",") if d.strip()])
    dir_soup = f"{dir_tokens} {dir_tokens} {dir_tokens}" if dir_tokens else ""

    # 4. Cast (top actors, weighted 2x)
    cast = item.get("cast", [])
    cast_tokens = " ".join([f"act_{clean_token(a)}" for a in cast if a])
    cast_soup = f"{cast_tokens} {cast_tokens}" if cast_tokens else ""

    # 5. Language code as a feature token
    lang = item.get("original_language", "")
    lang_token = f"lang_{lang}" if lang else ""

    # 6. Overview
    overview = item.get("overview", "")
    if overview == "No overview available.":
        overview = ""

    soup_parts = [genre_soup, keyword_soup, dir_soup, cast_soup, lang_token, overview]
    return " ".join([p for p in soup_parts if p.strip()])


class MovieRecommender:
    def __init__(self, tmdb_service: Optional[TMDBService] = None):
        self.tmdb = tmdb_service or TMDBService()

    def get_recommendations(self, movie_id: int, top_n: int = 10) -> Dict[str, Any]:
        """
        Produce content-based recommendations for a target movie.
        Works for any newly discovered TMDB movie.
        """
        # 1. Fetch full target movie metadata
        target_movie = self.tmdb.get_movie_details(movie_id)
        if not target_movie or not target_movie.get("id"):
            return {
                "target_movie": None,
                "recommendations": [],
                "error": f"Movie with ID {movie_id} was not found."
            }

        target_soup = build_movie_metadata_soup(target_movie)

        # Cache target metadata in SQLite
        save_title_metadata(
            media_type="movie",
            item_id=target_movie["id"],
            title=target_movie["title"],
            original_language=target_movie["original_language"],
            release_year=target_movie["release_year"],
            genre_names=target_movie["genre_string"],
            vote_average=target_movie["vote_average"],
            overview=target_movie["overview"],
            metadata_soup=target_soup
        )

        # 2. Collect candidate pool
        candidates = self.tmdb.get_movie_recommendation_candidates(movie_id)

        # If candidate pool is small (e.g. niche or foreign movie), supplement with discover
        if len(candidates) < 12 and target_movie.get("original_language"):
            genre_name = target_movie["genres"][0] if target_movie.get("genres") else ""
            supplemental = self.tmdb.discover_movies(
                language=target_movie["original_language"],
                genre=genre_name,
                sort_by="popularity.desc"
            ).get("results", [])

            seen_ids = {m["id"] for m in candidates}
            seen_ids.add(movie_id)
            for sm in supplemental:
                if sm["id"] not in seen_ids:
                    seen_ids.add(sm["id"])
                    candidates.append(sm)

        # Filter out the target movie itself and deduplicate
        unique_candidates = []
        seen = {movie_id}
        for c in candidates:
            cid = c.get("id")
            if cid and cid not in seen:
                seen.add(cid)
                unique_candidates.append(c)

        if not unique_candidates:
            return {
                "target_movie": target_movie,
                "recommendations": [],
                "message": "No matching candidates available for similarity computation."
            }

        # 3. Compute TF-IDF and Cosine Similarity
        candidate_soups = [build_movie_metadata_soup(c) for c in unique_candidates]
        corpus = [target_soup] + candidate_soups

        try:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            target_vector = tfidf_matrix[0:1]
            candidate_vectors = tfidf_matrix[1:]

            scores = cosine_similarity(target_vector, candidate_vectors)[0]

            scored_candidates = []
            for idx, candidate in enumerate(unique_candidates):
                sim_score = float(scores[idx])
                # Small blend with TMDB rating for quality
                rating_boost = min(candidate.get("vote_average", 0.0) / 100.0, 0.08)
                final_score = sim_score + rating_boost

                item_copy = dict(candidate)
                item_copy["similarity_score"] = round(sim_score, 3)
                item_copy["similarity_percent"] = max(1, min(99, int((sim_score * 0.85 + 0.15) * 100)))
                item_copy["ranking_score"] = round(final_score, 4)
                scored_candidates.append(item_copy)

            # Sort descending by ranking score
            scored_candidates.sort(key=lambda x: x["ranking_score"], reverse=True)
            top_recommendations = scored_candidates[:top_n]

        except Exception as e:
            logger.error(f"Error computing TF-IDF similarity for movie {movie_id}: {e}")
            # Fallback to returning raw candidates if TF-IDF fails
            top_recommendations = unique_candidates[:top_n]
            for r in top_recommendations:
                r["similarity_score"] = 0.5
                r["similarity_percent"] = 50

        return {
            "target_movie": target_movie,
            "recommendations": top_recommendations,
            "total_candidates_analyzed": len(unique_candidates)
        }

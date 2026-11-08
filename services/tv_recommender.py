"""
TV Series Recommendation Service.
Implements content-based filtering using TF-IDF and Cosine Similarity
over TV metadata soups (genres, keywords, cast, creators/directors, and overview).
Handles newly discovered TMDB TV series dynamically.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from services.tmdb_service import TMDBService
from services.db import save_title_metadata

logger = logging.getLogger(__name__)


def clean_token(name: str) -> str:
    """Normalize string into a single token suitable for TF-IDF."""
    if not name:
        return ""
    return re.sub(r"[^\w]", "", name.strip())


def build_tv_metadata_soup(item: Dict[str, Any]) -> str:
    """
    Construct a weighted metadata soup for a TV series.
    Heavily weights TV genres, creators, and keywords, along with cast and overview.
    """
    # 1. TV Genres (weighted 3x)
    genres = item.get("genres", [])
    genre_tokens = " ".join([f"tvgenre_{clean_token(g)}" for g in genres if g])
    genre_soup = f"{genre_tokens} {genre_tokens} {genre_tokens}" if genre_tokens else ""

    # 2. Keywords (weighted 2x)
    keywords = item.get("keywords", [])
    keyword_tokens = " ".join([f"kw_{clean_token(k)}" for k in keywords if k])
    keyword_soup = f"{keyword_tokens} {keyword_tokens}" if keyword_tokens else ""

    # 3. Creator / Showrunner (weighted 3x)
    creator = item.get("director", "")
    creator_tokens = " ".join([f"creator_{clean_token(c)}" for c in creator.split(",") if c.strip()])
    creator_soup = f"{creator_tokens} {creator_tokens} {creator_tokens}" if creator_tokens else ""

    # 4. Cast (top actors, weighted 2x)
    cast = item.get("cast", [])
    cast_tokens = " ".join([f"act_{clean_token(a)}" for a in cast if a])
    cast_soup = f"{cast_tokens} {cast_tokens}" if cast_tokens else ""

    # 5. Language code
    lang = item.get("original_language", "")
    lang_token = f"lang_{lang}" if lang else ""

    # 6. Overview
    overview = item.get("overview", "")
    if overview == "No overview available.":
        overview = ""

    soup_parts = [genre_soup, keyword_soup, creator_soup, cast_soup, lang_token, overview]
    return " ".join([p for p in soup_parts if p.strip()])


class TVRecommender:
    def __init__(self, tmdb_service: Optional[TMDBService] = None):
        self.tmdb = tmdb_service or TMDBService()

    def get_recommendations(self, series_id: int, top_n: int = 10) -> Dict[str, Any]:
        """
        Produce content-based recommendations for a target TV series.
        Works dynamically for any newly discovered TMDB TV series.
        """
        # 1. Fetch full target TV metadata
        target_tv = self.tmdb.get_tv_details(series_id)
        if not target_tv or not target_tv.get("id"):
            return {
                "target_tv": None,
                "recommendations": [],
                "error": f"TV Series with ID {series_id} was not found."
            }

        target_soup = build_tv_metadata_soup(target_tv)

        # Cache in SQLite
        save_title_metadata(
            media_type="tv",
            item_id=target_tv["id"],
            title=target_tv["title"],
            original_language=target_tv["original_language"],
            release_year=target_tv["release_year"],
            genre_names=target_tv["genre_string"],
            vote_average=target_tv["vote_average"],
            overview=target_tv["overview"],
            metadata_soup=target_soup
        )

        # 2. Collect candidate pool
        candidates = self.tmdb.get_tv_recommendation_candidates(series_id)

        # If candidate pool is small, supplement with discover
        if len(candidates) < 12 and target_tv.get("original_language"):
            genre_name = target_tv["genres"][0] if target_tv.get("genres") else ""
            supplemental = self.tmdb.discover_tv(
                language=target_tv["original_language"],
                genre=genre_name,
                sort_by="popularity.desc"
            ).get("results", [])

            seen_ids = {s["id"] for s in candidates}
            seen_ids.add(series_id)
            for ss in supplemental:
                if ss["id"] not in seen_ids:
                    seen_ids.add(ss["id"])
                    candidates.append(ss)

        # Filter out target show itself and deduplicate
        unique_candidates = []
        seen = {series_id}
        for c in candidates:
            cid = c.get("id")
            if cid and cid not in seen:
                seen.add(cid)
                unique_candidates.append(c)

        if not unique_candidates:
            return {
                "target_tv": target_tv,
                "recommendations": [],
                "message": "No matching candidates available for similarity computation."
            }

        # 3. Compute TF-IDF and Cosine Similarity
        candidate_soups = [build_tv_metadata_soup(c) for c in unique_candidates]
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
            logger.error(f"Error computing TF-IDF similarity for TV series {series_id}: {e}")
            top_recommendations = unique_candidates[:top_n]
            for r in top_recommendations:
                r["similarity_score"] = 0.5
                r["similarity_percent"] = 50

        return {
            "target_tv": target_tv,
            "recommendations": top_recommendations,
            "total_candidates_analyzed": len(unique_candidates)
        }

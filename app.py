"""
Flask Application for Global Movie & Web Series Recommendation Engine.
Provides clean REST API endpoints and serves the minimalist HTML/CSS/JS frontend.
"""
import os
import logging
from flask import Flask, render_template, request, jsonify
from config import Config
from services.db import init_db, get_cached_titles_count
from services.tmdb_service import TMDBService
from services.movie_recommender import MovieRecommender
from services.tv_recommender import TVRecommender

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("recommender_app")

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

# Initialize SQLite database
init_db()

# Initialize services
tmdb_service = TMDBService()
movie_recommender = MovieRecommender(tmdb_service)
tv_recommender = TVRecommender(tmdb_service)


# -------------------------------------------------------------
# Frontend Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """Render the single-page recommendation interface."""
    return render_template(
        "index.html",
        has_tmdb_token=tmdb_service.has_token,
        languages=Config.LANGUAGES,
        movie_genres=Config.MOVIE_GENRES,
        tv_genres=Config.TV_GENRES
    )


# -------------------------------------------------------------
# Metadata & System API Endpoints
# -------------------------------------------------------------
@app.route("/api/config/meta", methods=["GET"])
def get_metadata():
    """Return available languages, genres, and system status (without exposing secrets)."""
    stats = get_cached_titles_count()
    return jsonify({
        "status": "success",
        "has_token": tmdb_service.has_token,
        "languages": Config.LANGUAGES,
        "movie_genres": Config.MOVIE_GENRES,
        "tv_genres": Config.TV_GENRES,
        "cache_stats": stats
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "has_tmdb_token": tmdb_service.has_token
    })


@app.route("/api/sync", methods=["POST"])
def sync_cache():
    """
    Lightweight background synchronization process for pre-caching popular titles.
    Runs fast without blocking or downloading massive catalogs.
    """
    try:
        # Pre-cache trending movies and TV
        trending_m = tmdb_service.get_trending_movies(page=1)
        trending_tv = tmdb_service.get_trending_tv(page=1)
        
        # Also pre-cache top Bollywood (Hindi) titles for quick discovery
        hi_movies = tmdb_service.discover_movies(language="hi", sort_by="popularity.desc", page=1)
        hi_tv = tmdb_service.discover_tv(language="hi", sort_by="popularity.desc", page=1)

        total_synced = (
            len(trending_m.get("results", [])) +
            len(trending_tv.get("results", [])) +
            len(hi_movies.get("results", [])) +
            len(hi_tv.get("results", []))
        )
        return jsonify({
            "status": "success",
            "message": f"Successfully pre-cached {total_synced} popular titles into local SQLite store.",
            "synced_count": total_synced
        })
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return jsonify({
            "status": "error",
            "message": "Sync encountered an error. The app continues to operate on demand."
        }), 500


# -------------------------------------------------------------
# Movie Endpoints
# -------------------------------------------------------------
@app.route("/api/movies/search", methods=["GET"])
def search_movies():
    """Search movies with optional language, year, and genre filters."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Search query parameter 'q' is required."}), 400

    page = request.args.get("page", 1, type=int)
    language = request.args.get("language", "").strip()
    year = request.args.get("year", "").strip()
    genre = request.args.get("genre", "").strip()

    try:
        data = tmdb_service.search_movies(query=query, page=page, language=language, year=year, genre=genre)
        return jsonify({"status": "success", "data": data})
    except PermissionError as pe:
        return jsonify({"status": "error", "message": str(pe)}), 401
    except Exception as e:
        logger.error(f"Error in /api/movies/search: {e}")
        return jsonify({"status": "error", "message": "Failed to complete movie search. Please try again."}), 500


@app.route("/api/movies/trending", methods=["GET"])
def trending_movies():
    """Get trending movies."""
    page = request.args.get("page", 1, type=int)
    time_window = request.args.get("time_window", "week")
    if time_window not in ("day", "week"):
        time_window = "week"

    try:
        data = tmdb_service.get_trending_movies(time_window=time_window, page=page)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error in /api/movies/trending: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch trending movies."}), 500


@app.route("/api/movies/discover", methods=["GET"])
def discover_movies():
    """Discover movies by language, genre, year, and sort criteria."""
    language = request.args.get("language", "").strip()
    genre = request.args.get("genre", "").strip()
    year = request.args.get("year", "").strip()
    sort_by = request.args.get("sort_by", "popularity.desc").strip()
    page = request.args.get("page", 1, type=int)

    try:
        data = tmdb_service.discover_movies(language=language, genre=genre, year=year, sort_by=sort_by, page=page)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error in /api/movies/discover: {e}")
        return jsonify({"status": "error", "message": "Failed to discover movies."}), 500


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie_detail(movie_id: int):
    """Get full details for a specific movie."""
    try:
        data = tmdb_service.get_movie_details(movie_id)
        if not data:
            return jsonify({"status": "error", "message": f"Movie with ID {movie_id} not found."}), 404
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error in /api/movies/{movie_id}: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch movie details."}), 500


@app.route("/api/movies/<int:movie_id>/recommendations", methods=["GET"])
def get_movie_recommendations(movie_id: int):
    """
    Get content-based recommendations for a movie using TF-IDF and Cosine Similarity.
    """
    top_n = request.args.get("top_n", 10, type=int)
    top_n = max(1, min(top_n, 25))

    try:
        result = movie_recommender.get_recommendations(movie_id, top_n=top_n)
        if result.get("error"):
            return jsonify({"status": "error", "message": result["error"]}), 404
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        logger.error(f"Error in /api/movies/{movie_id}/recommendations: {e}")
        return jsonify({"status": "error", "message": "Failed to generate movie recommendations."}), 500


# -------------------------------------------------------------
# TV Series Endpoints
# -------------------------------------------------------------
@app.route("/api/tv/search", methods=["GET"])
def search_tv():
    """Search TV series with optional filters."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Search query parameter 'q' is required."}), 400

    page = request.args.get("page", 1, type=int)
    language = request.args.get("language", "").strip()
    year = request.args.get("year", "").strip()
    genre = request.args.get("genre", "").strip()

    try:
        data = tmdb_service.search_tv(query=query, page=page, language=language, year=year, genre=genre)
        return jsonify({"status": "success", "data": data})
    except PermissionError as pe:
        return jsonify({"status": "error", "message": str(pe)}), 401
    except Exception as e:
        logger.error(f"Error in /api/tv/search: {e}")
        return jsonify({"status": "error", "message": "Failed to complete TV search. Please try again."}), 500


@app.route("/api/tv/trending", methods=["GET"])
def trending_tv():
    """Get trending TV shows."""
    page = request.args.get("page", 1, type=int)
    time_window = request.args.get("time_window", "week")
    if time_window not in ("day", "week"):
        time_window = "week"

    try:
        data = tmdb_service.get_trending_tv(time_window=time_window, page=page)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error in /api/tv/trending: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch trending TV shows."}), 500


@app.route("/api/tv/discover", methods=["GET"])
def discover_tv():
    """Discover TV series by language, genre, year, and sort criteria."""
    language = request.args.get("language", "").strip()
    genre = request.args.get("genre", "").strip()
    year = request.args.get("year", "").strip()
    sort_by = request.args.get("sort_by", "popularity.desc").strip()
    page = request.args.get("page", 1, type=int)

    try:
        data = tmdb_service.discover_tv(language=language, genre=genre, year=year, sort_by=sort_by, page=page)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error in /api/tv/discover: {e}")
        return jsonify({"status": "error", "message": "Failed to discover TV series."}), 500


@app.route("/api/tv/<int:series_id>", methods=["GET"])
def get_tv_detail(series_id: int):
    """Get full details for a specific TV series."""
    try:
        data = tmdb_service.get_tv_details(series_id)
        if not data:
            return jsonify({"status": "error", "message": f"TV series with ID {series_id} not found."}), 404
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error in /api/tv/{series_id}: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch TV series details."}), 500


@app.route("/api/tv/<int:series_id>/recommendations", methods=["GET"])
def get_tv_recommendations(series_id: int):
    """
    Get content-based recommendations for a TV series using TF-IDF and Cosine Similarity.
    """
    top_n = request.args.get("top_n", 10, type=int)
    top_n = max(1, min(top_n, 25))

    try:
        result = tv_recommender.get_recommendations(series_id, top_n=top_n)
        if result.get("error"):
            return jsonify({"status": "error", "message": result["error"]}), 404
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        logger.error(f"Error in /api/tv/{series_id}/recommendations: {e}")
        return jsonify({"status": "error", "message": "Failed to generate TV recommendations."}), 500


# -------------------------------------------------------------
# Global Error Handlers (Never expose internal stack traces)
# -------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Requested endpoint not found."}), 404
    return render_template("index.html", error="Page not found"), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Unhandled 500 error: {error}")
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
    return render_template("index.html", error="Internal server error"), 500


if __name__ == "__main__":
    port = Config.PORT
    debug = Config.DEBUG
    print(f"Starting Movie & Web Series Recommendation Engine on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)

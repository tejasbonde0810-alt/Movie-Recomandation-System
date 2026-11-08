"""
Comprehensive test suite for the Global Movie & Web Series Recommendation Engine.
Tests Flask endpoints, TMDB service normalization, content-based TF-IDF recommender,
multilingual discovery (Hindi, English, Telugu, Korean, etc.), and security.
Compatible with standard unittest runner and pytest.
"""
import unittest
import json
from app import app
from services.tmdb_service import TMDBService
from services.movie_recommender import MovieRecommender, build_movie_metadata_soup
from services.tv_recommender import TVRecommender, build_tv_metadata_soup
from services.db import init_db


class RecommendationEngineTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        init_db()

    # =====================================================================
    # Security & Frontend Rendering Tests
    # =====================================================================
    def test_frontend_loads(self):
        """Verify that the homepage loads with status 200 and proper elements."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Global Movie & TV Series Recommendation Engine", html)
        self.assertIn("Movie Engine", html)
        self.assertIn("Web Series Engine", html)
        # Ensure no img tags or poster elements are injected
        self.assertNotIn("<img", html)

    def test_token_not_exposed_in_client_api(self):
        """Verify that TMDB Bearer token is NEVER exposed in API config or browser endpoints."""
        response = self.client.get("/api/config/meta")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("has_token", data)
        self.assertNotIn("bearer_token", data)
        self.assertNotIn("TMDB_BEARER_TOKEN", data)
        self.assertNotIn("token", data)

    def test_health_endpoint(self):
        """Verify health check returns status healthy."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")

    # =====================================================================
    # Movie API & Multilingual Discovery Tests
    # =====================================================================
    def test_movie_search_with_results(self):
        """Verify searching for a movie title works."""
        response = self.client.get("/api/movies/search?q=Inception")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        results = data["data"]["results"]
        self.assertGreater(len(results), 0)
        self.assertTrue(any("Inception" in m["title"] for m in results))

    def test_movie_search_validation(self):
        """Verify missing query string returns a 400 Bad Request error."""
        response = self.client.get("/api/movies/search")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["status"], "error")

    def test_hindi_movie_discovery(self):
        """Verify discovery filter for Hindi (Bollywood) cinema returns matching titles."""
        response = self.client.get("/api/movies/discover?language=hi")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        results = data["data"]["results"]
        self.assertGreater(len(results), 0)
        for movie in results:
            self.assertEqual(movie["original_language"], "hi")

    def test_english_movie_discovery(self):
        """Verify discovery filter for English cinema returns English titles."""
        response = self.client.get("/api/movies/discover?language=en")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        results = data["data"]["results"]
        self.assertGreater(len(results), 0)
        for movie in results:
            self.assertEqual(movie["original_language"], "en")

    def test_other_language_discovery_telugu_korean(self):
        """Verify Telugu and Korean cinema discovery."""
        # Telugu (Tollywood)
        res_te = self.client.get("/api/movies/discover?language=te")
        self.assertEqual(res_te.status_code, 200)
        te_results = res_te.get_json()["data"]["results"]
        self.assertGreater(len(te_results), 0)
        self.assertTrue(all(m["original_language"] == "te" for m in te_results))

        # Korean (K-Cinema)
        res_ko = self.client.get("/api/movies/discover?language=ko")
        self.assertEqual(res_ko.status_code, 200)
        ko_results = res_ko.get_json()["data"]["results"]
        self.assertGreater(len(ko_results), 0)
        self.assertTrue(any("Parasite" in m["title"] for m in ko_results))

    def test_movie_details_endpoint(self):
        """Verify fetching individual movie details."""
        response = self.client.get("/api/movies/27205")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        movie = data["data"]
        self.assertEqual(movie["id"], 27205)
        self.assertIn("Inception", movie["title"])
        self.assertEqual(movie["release_year"], "2010")

    # =====================================================================
    # TV Series API & Recommendations Tests
    # =====================================================================
    def test_tv_search_with_results(self):
        """Verify searching for a TV series works."""
        response = self.client.get("/api/tv/search?q=Breaking+Bad")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        results = data["data"]["results"]
        self.assertGreater(len(results), 0)
        self.assertTrue(any("Breaking Bad" in s["title"] for s in results))

    def test_tv_search_validation(self):
        """Verify missing query for TV returns 400 Bad Request."""
        response = self.client.get("/api/tv/search")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["status"], "error")

    def test_tv_discovery_multilingual(self):
        """Verify TV discovery in Hindi."""
        res_hi = self.client.get("/api/tv/discover?language=hi")
        self.assertEqual(res_hi.status_code, 200)
        hi_results = res_hi.get_json()["data"]["results"]
        self.assertGreater(len(hi_results), 0)
        self.assertTrue(all(s["original_language"] == "hi" for s in hi_results))

    def test_tv_details_endpoint(self):
        """Verify fetching individual TV series details."""
        response = self.client.get("/api/tv/1396")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        show = data["data"]
        self.assertEqual(show["id"], 1396)
        self.assertIn("Breaking Bad", show["title"])

    # =====================================================================
    # Recommendation Algorithm (TF-IDF & Cosine Similarity) Tests
    # =====================================================================
    def test_movie_recommendations_algorithm(self):
        """
        Verify MovieRecommender computes TF-IDF similarity,
        excludes the target itself, and returns ranked results.
        """
        response = self.client.get("/api/movies/27205/recommendations?top_n=5")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        recs = data["data"]["recommendations"]
        self.assertGreater(len(recs), 0)

        # Target movie itself must NOT be in recommendations
        for r in recs:
            self.assertNotEqual(r["id"], 27205)
            self.assertIn("similarity_score", r)
            self.assertIn("similarity_percent", r)
            self.assertGreaterEqual(r["similarity_score"], 0)

        # Interstellar (Christopher Nolan / Sci-Fi) should be recommended
        rec_titles = [r["title"] for r in recs]
        self.assertIn("Interstellar", rec_titles)

    def test_tv_recommendations_algorithm(self):
        """
        Verify TVRecommender computes content-based similarity for TV series.
        """
        response = self.client.get("/api/tv/1396/recommendations?top_n=5")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        recs = data["data"]["recommendations"]
        self.assertGreater(len(recs), 0)

        # Exclude target show
        for r in recs:
            self.assertNotEqual(r["id"], 1396)
            self.assertIn("similarity_score", r)

        # Better Call Saul (same creator/crime universe) should rank top
        rec_titles = [r["title"] for r in recs]
        self.assertIn("Better Call Saul", rec_titles)

    def test_newly_discovered_title_dynamic_vectorization(self):
        """
        Verify that an arbitrary, newly discovered TMDB title (not in any pre-existing dataset)
        is properly processed and vectorized dynamically.
        """
        new_movie = {
            "id": 999999,
            "title": "Quantum Odyssey",
            "original_language": "en",
            "release_year": "2026",
            "genres": ["Science Fiction", "Adventure"],
            "genre_string": "Science Fiction, Adventure",
            "vote_average": 8.1,
            "overview": "Astronauts travel through a newly opened quantum rift into parallel realities.",
            "director": "Christopher Nolan",
            "cast": ["Matthew McConaughey", "Anne Hathaway"],
            "keywords": ["quantum", "parallel reality", "space"],
            "media_type": "movie"
        }

        soup = build_movie_metadata_soup(new_movie)
        self.assertIn("genre_ScienceFiction", soup)
        self.assertIn("dir_ChristopherNolan", soup)
        self.assertIn("quantum", soup)

    def test_missing_metadata_graceful_handling(self):
        """Verify that items with missing/empty fields do not cause runtime errors."""
        sparse_item = {
            "id": 888888,
            "title": "Sparse Movie",
            "original_language": "",
            "release_year": "",
            "genres": [],
            "vote_average": 0.0,
            "overview": "No overview available.",
            "director": "",
            "cast": [],
            "keywords": [],
            "media_type": "movie"
        }
        soup = build_movie_metadata_soup(sparse_item)
        self.assertIsInstance(soup, str)

        sparse_tv = {
            "id": 777777,
            "title": "Sparse TV",
            "original_language": "",
            "release_year": "",
            "genres": [],
            "vote_average": 0.0,
            "overview": "",
            "director": "",
            "cast": [],
            "keywords": [],
            "media_type": "tv"
        }
        tv_soup = build_tv_metadata_soup(sparse_tv)
        self.assertIsInstance(tv_soup, str)

    def test_sync_cache_endpoint(self):
        """Verify that the cache sync endpoint completes successfully."""
        response = self.client.post("/api/sync")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["synced_count"], 0)


if __name__ == "__main__":
    unittest.main()

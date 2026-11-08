# Global Movie & Web Series Recommendation Engine

A lightweight, fast, content-based Movie and TV/Web Series Recommendation Engine built from scratch with Python Flask, vanilla JavaScript, HTML5, and CSS3. Integrates with TMDB (The Movie Database) API and uses TF-IDF vectorization with cosine similarity to recommend titles dynamically.

---

## 1. Project Overview

- **Content-Based Filtering**: Uses TF-IDF (Term Frequency-Inverse Document Frequency) and Cosine Similarity over metadata soups combining genres, keywords, directors/creators, cast, and overviews.
- **Dynamic TMDB Catalog Support**: Recommends any newly discovered title directly on the fly—without requiring pre-computed dense matrices or periodic full catalog downloads.
- **Dual Engines**:
  1. **Movie Recommendation Engine**: Full search, trending, popular, top-rated, and multi-language discovery for international cinema.
  2. **Web Series Recommendation Engine**: Full search, trending, popular, top-rated, and discovery using TMDB TV endpoints.
- **Multilingual Support**: First-class discovery for Hindi (Bollywood), Telugu (Tollywood), Tamil (Kollywood), Malayalam (Mollywood), Kannada (Sandalwood), Bengali, Marathi, Korean, Japanese, Chinese, Spanish, French, German, Italian, Portuguese, and configurable global languages.
- **Minimalist, Clean Interface**: Strictly text-based rows with dark theme and subtle indigo/purple accents. **No heavy posters, no image carousels, no autoplay videos, no frameworks (zero React/Streamlit/Next.js)**.
- **Local SQLite Caching**: Thread-safe caching of API responses and title metadata to prevent duplicate network calls and adhere to TMDB rate limits.
- **Robust Security**: Secret keys and TMDB Bearer tokens remain exclusively server-side and are never exposed to browser responses or JavaScript.

---

## 2. Project Structure

```
movie_recommendation_engine/
│
├── app.py                     # Flask main entrypoint, REST API routes & controllers
├── config.py                  # App configuration, language mappings & genre definitions
├── requirements.txt           # Python dependencies
├── .env                       # Local environment variables (Bearer token, secret key)
├── .env.example               # Example environment template
├── .gitignore                 # Git ignore rules (protecting .env, caches, and databases)
├── README.md                  # Comprehensive documentation and deployment guide
│
├── services/
│   ├── db.py                  # SQLite caching layer for raw responses & title metadata
│   ├── tmdb_service.py        # TMDB API client with timeouts, retries & normalizers
│   ├── movie_recommender.py   # TF-IDF & Cosine Similarity engine for movies
│   ├── tv_recommender.py      # TF-IDF & Cosine Similarity engine for TV series
│   └── mock_data.py           # Curated fallback/offline dataset for testing & demo mode
│
├── templates/
│   └── index.html             # Clean HTML5 single-page interface
│
├── static/
│   ├── css/
│   │   └── style.css          # Minimalist dark theme CSS
│   └── js/
│       └── app.js             # Vanilla JavaScript frontend controller
│
├── data/                      # Local storage directory (SQLite app_cache.db)
│
└── tests/
    └── test_app.py            # Unit & integration test suite (18 comprehensive tests)
```

---

## 3. Technology Stack

- **Backend**: Python 3.10+, Flask 3.x
- **Data Source**: TMDB API v3/v4
- **Recommendation Algorithm**: scikit-learn (`TfidfVectorizer`, `cosine_similarity`), NumPy
- **Database / Cache**: SQLite3 (built-in)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Testing**: `unittest` / `pytest`

---

## 4. Setup & Configuration

### Prerequisites
- Python 3.10 or higher
- A free TMDB API Read Access Token (Bearer token). Obtain one from [The Movie Database API Settings](https://www.themoviedb.org/settings/api).

### Step 1: Clone or Navigate to the Workspace
```bash
cd /path/to/WebMovie_Recommandation
```

### Step 2: Create and Activate Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure `.env`
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` in a text editor and add your TMDB Bearer Token:
```env
# TMDB API Bearer Token (v4 API Read Access Token or v3 API Key)
TMDB_BEARER_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Flask Configuration
FLASK_SECRET_KEY=generate_a_secure_random_key_here
FLASK_ENV=development
PORT=5000
```
> **Note**: If `TMDB_BEARER_TOKEN` is left blank, the application automatically runs in **Offline Demo Mode** with a curated set of multilingual movies and TV series, ensuring functionality is testable even without an active API key.

---

## 5. Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will bind to `http://127.0.0.1:5000`. Open this URL in any web browser.

---

## 6. How to Use the Recommendation Engines

### A. Movie Recommendation Engine
1. Select **Movie Engine** from the left sidebar navigation.
2. **Search by Title**: Type a movie name (e.g., `Inception`, `3 Idiots`, `RRR`, `Parasite`) in the search box and press `Enter` or click **Search**.
3. **Discover by Film Industry / Language**: Use the **Original Language** dropdown to filter by Hindi (`hi`), English (`en`), Telugu (`te`), Tamil (`ta`), Korean (`ko`), Spanish (`es`), etc.
4. **Discover Feeds**: Select between `Trending (This Week)`, `Popular`, `Top Rated`, `Recently Released`, or apply custom Genre and Year filters.
5. **Get Content-Based Recommendations**:
   - In any result row, click **Recommend Similar**.
   - The engine retrieves candidate titles, computes TF-IDF vector similarity against the target title's metadata soup, and returns ranked recommendations with a calculated similarity percentage (e.g., `89% Match`).
   - A context banner appears showing: *"Recommendations based on: [Title]"*. Click **Back to Browse** to clear the recommendation view.

### B. Web Series Recommendation Engine
1. Select **Web Series Engine** from the left sidebar navigation.
2. The interface switches to TMDB TV endpoints (`/tv/popular`, `/tv/top_rated`, `/discover/tv`, `/search/tv`).
3. Search or discover series across English, Hindi, Korean, Spanish, etc.
4. Click **Recommend Similar** on any TV series to trigger the dedicated TV recommendation pipeline (matching creators, TV genres, keywords, cast, and story elements).

---

## 7. Recommendation Algorithm Details

### Dynamic Metadata Soup
For both Movies and TV shows, a metadata soup is dynamically assembled from:
- **Genres** (weighted 3x with domain prefixes, e.g. `genre_Action`)
- **Keywords** (weighted 2x, e.g. `kw_heist`)
- **Directors / Creators** (weighted 3x, e.g. `dir_ChristopherNolan`)
- **Top Cast** (weighted 2x, e.g. `act_LeonardoDiCaprio`)
- **Language Code** (e.g. `lang_en`)
- **Overview Text** (tokenized and stop-words removed)

### Scalability Strategy for Newly Discovered Titles
1. When a user requests recommendations for a title ID:
   - Target metadata is fetched and cached in SQLite.
   - A candidate pool of 20–40 related titles is assembled using TMDB's recommendations endpoint, similar endpoint, and genre/language discover queries.
   - A `TfidfVectorizer(ngram_range=(1, 2), stop_words='english')` fits dynamically on the target + candidate corpus in ~15ms.
   - `cosine_similarity(target_vector, candidate_vectors)` computes pairwise similarity.
   - Candidates are ranked by cosine similarity blended with TMDB rating quality.
   - The target title itself is strictly excluded, duplicate IDs are removed, and top results are returned with similarity percentage badges.
2. **Advantage**: No need to store or retrain an $O(N^2)$ static similarity matrix across millions of titles. Any newly released TMDB title can be recommended immediately upon query.

---

## 8. Original Language vs. Production Country

> **Important Distinction**:
> In TMDB, `original_language` represents the primary spoken language of the film or series (e.g., `hi` for Hindi, `en` for English).
> - While `original_language=hi` strongly correlates with Bollywood / Hindi cinema, and `te` with Tollywood, a language code alone does not strictly define the producing country (for instance, an American or British film might be filmed in Hindi or Japanese).
> - The engine captures both `original_language` and `production_countries` (or `origin_country` for TV shows) and displays the production origin in title metadata rows.

---

## 9. Backend API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the main HTML5/CSS/JS frontend |
| `GET` | `/api/config/meta` | System configuration, supported languages, genres, cache stats |
| `GET` | `/api/health` | Health check endpoint |
| `POST` | `/api/sync` | Lightweight pre-caching of trending and popular titles |
| `GET` | `/api/movies/search?q={query}` | Search movies with optional language, year, and genre filters |
| `GET` | `/api/movies/trending?time_window=week` | Get trending movies |
| `GET` | `/api/movies/discover` | Discover movies with language, genre, year, and sort filters |
| `GET` | `/api/movies/<movie_id>` | Detailed metadata for a specific movie |
| `GET` | `/api/movies/<movie_id>/recommendations` | TF-IDF content-based recommendations for a movie |
| `GET` | `/api/tv/search?q={query}` | Search TV and web series |
| `GET` | `/api/tv/trending?time_window=week` | Get trending TV and web series |
| `GET` | `/api/tv/discover` | Discover TV series with language, genre, year, and sort filters |
| `GET` | `/api/tv/<series_id>` | Detailed metadata for a specific TV series |
| `GET` | `/api/tv/<series_id>/recommendations` | TF-IDF content-based recommendations for a TV series |

---

## 10. Running Tests

The test suite validates:
- Frontend loading and absence of poster images
- Server security: Bearer token is never exposed to client API
- Movie and TV title search
- Multi-language discovery (Hindi, English, Telugu, Korean, etc.)
- TF-IDF content-based recommendation calculations for movies and TV
- Handling of newly discovered titles without pre-existing training records
- Handling of sparse/missing metadata (no overview, missing director, missing genres)
- SQLite database caching and pre-sync process

To execute the test suite:
```bash
python -m unittest tests/test_app.py
```

### Test Output
```
Ran 18 tests in 0.263s
OK
```

---

## 11. Production Deployment

### Using Gunicorn (Linux/macOS)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Waitress (Windows/Cross-Platform)
```bash
pip install waitress
python -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=5000)"
```

### Reverse Proxy (Nginx Example)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /path/to/WebMovie_Recommandation/static/;
        expires 30d;
    }
}
```

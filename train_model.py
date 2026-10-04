import pandas as pd
import ast
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==========================================
# 1. LOAD DATA
# ==========================================

movies = pd.read_csv("tmdb_5000_movies.csv")
credits = pd.read_csv("tmdb_5000_credits.csv")


# ==========================================
# 2. MERGE DATA
# ==========================================

movies = movies.merge(
    credits,
    left_on="id",
    right_on="movie_id"
)


# ==========================================
# 3. SELECT IMPORTANT COLUMNS
# ==========================================

movies = movies[
    [
        "movie_id",
        "title_x",
        "genres",
        "keywords",
        "overview",
        "cast",
        "crew",
        "vote_average",
        "vote_count",
        "popularity"
    ]
]

movies = movies.rename(columns={"title_x": "title"})


# ==========================================
# 4. HANDLE MISSING VALUES
# ==========================================

movies["overview"] = movies["overview"].fillna("")
movies["genres"] = movies["genres"].fillna("[]")
movies["keywords"] = movies["keywords"].fillna("[]")
movies["cast"] = movies["cast"].fillna("[]")
movies["crew"] = movies["crew"].fillna("[]")


# ==========================================
# 5. CONVERT GENRES AND KEYWORDS
# ==========================================

def convert(obj):

    result = []

    for item in ast.literal_eval(obj):
        result.append(item["name"])

    return result


movies["genres"] = movies["genres"].apply(convert)
movies["keywords"] = movies["keywords"].apply(convert)


# ==========================================
# 6. CONVERT CAST
# ==========================================

def convert_cast(obj):

    result = []

    for i, item in enumerate(ast.literal_eval(obj)):

        if i < 3:
            result.append(item["name"])

        else:
            break

    return result


movies["cast"] = movies["cast"].apply(convert_cast)


# ==========================================
# 7. GET DIRECTOR
# ==========================================

def fetch_director(obj):

    result = []

    for item in ast.literal_eval(obj):

        if item["job"] == "Director":
            result.append(item["name"])

    return result


movies["crew"] = movies["crew"].apply(fetch_director)


# ==========================================
# 8. CREATE TAGS
# ==========================================

movies["tags"] = (
    movies["genres"].apply(lambda x: " ".join(x))
    + " "
    + movies["keywords"].apply(lambda x: " ".join(x))
    + " "
    + movies["overview"]
    + " "
    + movies["cast"].apply(lambda x: " ".join(x))
    + " "
    + movies["crew"].apply(lambda x: " ".join(x))
)

movies["tags"] = movies["tags"].str.lower()


# ==========================================
# 9. TF-IDF
# ==========================================

tfidf = TfidfVectorizer(
    max_features=5000,
    stop_words="english"
)

vectors = tfidf.fit_transform(
    movies["tags"]
)


# ==========================================
# 10. COSINE SIMILARITY
# ==========================================

similarity = cosine_similarity(vectors)


# ==========================================
# 11. SAVE DATA
# ==========================================

final_movies = movies[
    [
        "movie_id",
        "title",
        "genres",
        "overview",
        "vote_average",
        "vote_count",
        "popularity",
        "tags"
    ]
]


pickle.dump(
    final_movies,
    open("movies.pkl", "wb")
)

pickle.dump(
    similarity,
    open("similarity.pkl", "wb")
)


print("Model training completed!")
print("Movies:", len(final_movies))
print("Similarity matrix:", similarity.shape)
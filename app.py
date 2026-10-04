import streamlit as st
import pickle


# ==========================================
# LOAD DATA
# ==========================================

movies = pickle.load(
    open("movies.pkl", "rb")
)

similarity = pickle.load(
    open("similarity.pkl", "rb")
)


# ==========================================
# PAGE
# ==========================================

st.title("🎬 Movie Recommendation System")

st.write(
    "Search for a genre or a movie"
)


# ==========================================
# SEARCH BOX
# ==========================================

search = st.text_input(
    "🔍 Search"
)


# ==========================================
# GENRE SEARCH
# ==========================================

def genre_search(genre):

    result = movies[
        movies["genres"].apply(
            lambda x: genre.lower() in
            [g.lower() for g in x]
        )
    ]

    # Highest rated movies first
    result = result.sort_values(
        by="vote_average",
        ascending=False
    )

    return result


# ==========================================
# MOVIE RECOMMENDATION
# ==========================================

def movie_recommend(movie):

    movie_index = movies[
        movies["title"].str.lower() ==
        movie.lower()
    ].index

    if len(movie_index) == 0:
        return []

    movie_index = movie_index[0]

    distances = similarity[movie_index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    recommendations = []

    for i in movie_list:

        movie_data = movies.iloc[i[0]]

        recommendations.append(
            {
                "title": movie_data["title"],
                "rating": movie_data["vote_average"],
                "similarity": round(i[1], 3)
            }
        )

    return recommendations


# ==========================================
# GENRE LIST
# ==========================================

genres = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Music",
    "Mystery",
    "Romance",
    "Science Fiction",
    "Thriller",
    "War",
    "Western"
]


# ==========================================
# SEARCH PROCESS
# ==========================================

if search:

    # --------------------------------------
    # CHECK IF SEARCH IS A GENRE
    # --------------------------------------

    matched_genre = None

    for genre in genres:

        if search.lower() == genre.lower():

            matched_genre = genre
            break


    # ======================================
    # GENRE RESULT
    # ======================================

    if matched_genre:

        st.subheader(
            f"⭐ Top {matched_genre} Movies"
        )

        result = genre_search(
            matched_genre
        )

        for _, movie in result.head(20).iterrows():

            st.write(
                f"### {movie['title']}"
            )

            st.write(
                f"⭐ Rating: {movie['vote_average']}"
            )

            st.write(
                f"🔥 Popularity: {movie['popularity']}"
            )

            st.write("---")


    # ======================================
    # MOVIE SEARCH
    # ======================================

    else:

        matches = movies[
            movies["title"]
            .str.lower()
            .str.contains(
                search.lower(),
                na=False
            )
        ]

        if len(matches) == 0:

            st.error(
                "Movie or genre not found."
            )

        else:

            st.subheader(
                "🎬 Movies Found"
            )

            selected_movie = st.selectbox(
                "Select a movie",
                matches["title"].tolist()
            )


            if st.button(
                "🎯 Recommend Similar Movies"
            ):

                recommendations = movie_recommend(
                    selected_movie
                )


                st.subheader(
                    "Recommended Movies"
                )


                for movie in recommendations:

                    st.write(
                        f"### {movie['title']}"
                    )

                    st.write(
                        f"⭐ Rating: {movie['rating']}"
                    )

                    st.write(
                        f"🎯 Similarity: {movie['similarity']}"
                    )

                    st.write("---")
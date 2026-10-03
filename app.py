
import streamlit as st
import pandas as pd
import pickle
import requests

st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide"
)

# =========================
# LOAD MODEL
# =========================

@st.cache_resource
def load_data():

    with open("/content/movies.pkl", "rb") as f:
        movies = pickle.load(f)

    with open("/content/similarity.pkl", "rb") as f:
        similarity = pickle.load(f)

    return movies, similarity


movies, similarity = load_data()

# =========================
# TMDB TOKEN
# =========================

TMDB_TOKEN = st.secrets.get("TMDB_TOKEN", "")

TMDB_URL = "https://api.themoviedb.org/3/search/movie"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# =========================
# MOVIE DETAILS
# =========================

@st.cache_data
def get_movie_details(title):

    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json"
    }

    params = {
        "query": title
    }

    try:

        response = requests.get(
            TMDB_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None

        results = response.json().get("results", [])

        if not results:
            return None

        movie = results[0]

        poster_path = movie.get("poster_path")

        return {
            "poster": IMAGE_URL + poster_path if poster_path else None,
            "overview": movie.get("overview", ""),
            "rating": movie.get("vote_average", 0),
            "release_date": movie.get("release_date", "")
        }

    except Exception:
        return None


# =========================
# RECOMMENDER
# =========================

def recommend(movie_title):

    query = movie_title.strip().lower()

    matches = movies[
        movies["title"].str.lower() == query
    ]

    if matches.empty:

        matches = movies[
            movies["title"]
            .str.lower()
            .str.contains(query, na=False)
        ]

    if matches.empty:
        return None, []

    index = matches.index[0]

    distances = similarity[index]

    movie_list = sorted(
        enumerate(distances),
        key=lambda x: x[1],
        reverse=True
    )[1:6]

    recommendations = []

    for movie_index, score in movie_list:

        title = movies.iloc[movie_index]["title"]

        details = get_movie_details(title)

        if details:

            recommendations.append({
                "title": title,
                "score": score,
                "poster": details["poster"],
                "overview": details["overview"],
                "rating": details["rating"],
                "release_date": details["release_date"]
            })

    return movies.iloc[index]["title"], recommendations


# =========================
# CUSTOM CSS
# =========================

st.html("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(
        circle at 50% -20%,
        #292929 0%,
        #101010 35%,
        #070707 70%
    );
    color: white;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
}

/* LOGO */

.logo {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -1px;
}

.logo span {
    color: #e50914;
}

/* HERO */

.hero {
    text-align: center;
    padding: 80px 20px 45px;
}

.hero h1 {
    font-size: 58px;
    line-height: 1.05;
    margin: 0;
    font-weight: 800;
}

.hero h1 span {
    color: #e50914;
}

.hero p {
    color: #a7a7a7;
    font-size: 18px;
    max-width: 650px;
    margin: 22px auto 0;
}

/* INPUT */

.stTextInput input {
    background: #171717 !important;
    color: white !important;
    border: 1px solid #333 !important;
    border-radius: 12px !important;
}

/* BUTTON */

.stButton button {
    width: 100%;
    border-radius: 12px;
    background: #e50914;
    color: white;
    border: none;
    font-weight: 700;
}

/* RESULT */

.result-title {
    font-size: 30px;
    font-weight: 800;
    margin: 50px 0 25px;
}

.movie-card {
    background: #151515;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #252525;
    height: 100%;
}

.movie-card img {
    width: 100%;
    height: 350px;
    object-fit: cover;
}

.movie-info {
    padding: 15px;
}

.movie-name {
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 9px;
}

.match {
    display: inline-block;
    background: rgba(229,9,20,.15);
    color: #ff5962;
    padding: 5px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
}

.rating {
    color: #aaa;
    font-size: 13px;
    margin-top: 9px;
}

.overview {
    color: #888;
    font-size: 12px;
    line-height: 1.5;
    margin-top: 10px;
}

.footer {
    text-align: center;
    color: #666;
    margin-top: 70px;
    padding: 30px;
    border-top: 1px solid #222;
}

</style>
""")

# =========================
# HEADER
# =========================

st.html("""
<div class="logo">
    Cine<span>Match</span> 🎬
</div>
""")

# =========================
# HERO
# =========================

st.html("""
<div class="hero">

<h1>
Don't know what to watch?<br>
<span>We'll find it.</span>
</h1>

<p>
Tell CineMatch one movie you love.
We'll analyze its genres, keywords, cast and director
to discover movies with a similar feel.
</p>

</div>
""")

# =========================
# SEARCH
# =========================

movie_input = st.text_input(
    "Movie",
    placeholder="Try: Interstellar, Inception, Avatar..."
)

if st.button("🔍 Find My Movies"):

    if not movie_input.strip():

        st.warning("Enter a movie title first.")

    else:

        selected_movie, recommendations = recommend(movie_input)

        if selected_movie is None:

            st.error("Movie not found. Try another title.")

        else:

            st.html(
                f"""
                <div class="result-title">
                    Because you liked {selected_movie}
                </div>
                """
            )

            cols = st.columns(5)

            for col, movie in zip(cols, recommendations):

                with col:

                    poster = movie["poster"]

                    if poster:

                        overview = movie["overview"][:150]

                        st.html(
                            f"""
                            <div class="movie-card">

                                <img src="{poster}">

                                <div class="movie-info">

                                    <div class="movie-name">
                                        {movie["title"]}
                                    </div>

                                    <span class="match">
                                        {movie["score"]:.0%} MATCH
                                    </span>

                                    <div class="rating">
                                        ⭐ {movie["rating"]:.1f}/10
                                    </div>

                                    <div class="overview">
                                        {overview}
                                        {"..." if len(movie["overview"]) > 150 else ""}
                                    </div>

                                </div>

                            </div>
                            """
                        )

# =========================
# FOOTER
# =========================

st.html("""
<div class="footer">

CineMatch · Content-Based Movie Recommendation System<br>
Built with Python · Machine Learning · TMDB

</div>
""")

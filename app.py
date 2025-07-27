# Import Required Libraries
import pickle
import streamlit as st
import requests
from fuzzywuzzy import process

# --- Load Models ---
movies = pickle.load(open('model/movie_list.pkl', 'rb'))
similarity = pickle.load(open('model/similarity.pkl', 'rb'))

# --- Extract Genres and Years ---
all_genres = set()
release_years = set()
for g_list in movies['tags']:
    for word in g_list.split():
        if word.lower() in ['action', 'comedy', 'drama', 'thriller', 'romance', 'animation', 'horror', 'sci-fi']:
            all_genres.add(word.capitalize())

movies['release_year'] = movies['title'].str.extract(r'\((\d{4})\)').fillna('Unknown')
release_years = sorted(set(movies['release_year'].values))

# --- Fetch Movie Details from TMDB API ---
def fetch_movie_data(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    data = requests.get(url).json()
    movie_info = {
        "poster": f"https://image.tmdb.org/t/p/w500/{data.get('poster_path')}",
        "overview": data.get("overview", "No overview available."),
        "release_date": data.get("release_date", "N/A"),
        "rating": data.get("vote_average", "N/A"),
        "genres": ", ".join([genre['name'] for genre in data.get("genres", [])]),
        "tmdb_link": f"https://www.themoviedb.org/movie/{movie_id}"
    }
    return movie_info

# --- Recommendation Logic ---
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommendations = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        info = fetch_movie_data(movie_id)
        recommendations.append({
            "title": movies.iloc[i[0]].title,
            "poster": info['poster'],
            "overview": info['overview'],
            "release_date": info['release_date'],
            "rating": info['rating'],
            "genres": info['genres'],
            "link": info['tmdb_link']
        })

    return recommendations

# --- Streamlit UI ---
st.title('🎬 Movie Recommender System')

# --- Sidebar Filters ---
st.sidebar.header("🎯 Filters")
selected_genre = st.sidebar.selectbox("Select Genre (Optional):", ["All"] + sorted(all_genres))
selected_year = st.sidebar.selectbox("Select Release Year (Optional):", ["All"] + release_years)

# --- Search Input with Fuzzy Match ---
user_input = st.text_input("🔍 Search for a movie:")
movie_list = movies['title'].values
selected_movie = None
if user_input:
    best_match = process.extractOne(user_input, movie_list)
    if best_match:
        selected_movie = best_match[0]
        st.success(f"Best match: {selected_movie}")
else:
    selected_movie = st.selectbox("Or select from dropdown:", movie_list)

# --- Show Recommendations ---
if st.button("🎁 Show Recommendations") and selected_movie:
    filtered_movies = movies.copy()
    if selected_genre != "All":
        filtered_movies = filtered_movies[filtered_movies['tags'].str.contains(selected_genre.lower())]
    if selected_year != "All":
        filtered_movies = filtered_movies[filtered_movies['release_year'] == selected_year]

    if selected_movie not in filtered_movies['title'].values:
        st.warning("Selected movie is excluded by current filters. Showing all matches.")
        filtered_movies = movies

    recommendations = recommend(selected_movie)
    cols = st.columns(5)
    for i, col in enumerate(cols):
        with col:
            st.image(recommendations[i]['poster'])
            st.markdown(f"**{recommendations[i]['title']}**")
            st.markdown(f"🎬 *{recommendations[i]['genres']}*")
            st.markdown(f"📅 {recommendations[i]['release_date']}")
            st.markdown(f"⭐ {recommendations[i]['rating']}/10")
            st.markdown(f"[🔗 TMDB]({recommendations[i]['link']})", unsafe_allow_html=True)
            st.markdown(f"📝 {recommendations[i]['overview'][:150]}...")

    # --- Rating and Feedback ---
    st.subheader("📢 Your Feedback")
    user_rating = st.slider("Rate this recommendation", 0, 10, 5)
    user_comments = st.text_area("Any suggestions or feedback?")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! 🙏")

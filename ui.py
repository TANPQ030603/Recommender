import streamlit as st
import pandas as pd
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Spotify API Credentials
CLIENT_ID = "bf27f12ccb924a79a5d582294807e452"
CLIENT_SECRET = "6420a78e25ae49268b95a2b2b3fafcd3"

# Initialize Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Load the dataset
@st.cache_data
def load_data():
    return pd.read_csv(r"C:\Users\Tan\Downloads\Music_Recommender_System\Music_Recommender_System\spotifymusicdataset.csv")

df = load_data()
df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

music = pickle.load(open('df.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Functions for Recommendations
def get_song_album_cover_url(song_name, artist_name):
    search_query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=search_query, type="track")

    if results and results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        album_cover_url = track["album"]["images"][0]["url"]
        return album_cover_url
    else:
        return "https://i.postimg.cc/0QNxYz4V/social.png"

def recommend(song):
    index = music[music['song'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_music_names = []
    recommended_music_posters = []
    for i in distances[1:6]:
        artist = music.iloc[i[0]].artist
        recommended_music_posters.append(get_song_album_cover_url(music.iloc[i[0]].song, artist))
        recommended_music_names.append(music.iloc[i[0]].song)
    return recommended_music_names, recommended_music_posters

def recommend_random_songs():
    top_songs = df[df['rating'] > 3.0].sample(n=3) if len(df[df['rating'] > 3.0]) >= 3 else df[df['rating'] > 3.0]
    if not top_songs.empty:
        return top_songs[['song', 'artist', 'rating']]

def recommend_artist_songs(selected_artist):
    artist_songs = df[(df['artist'] == selected_artist) & (df['rating'] > 3.0)].sort_values(by='rating', ascending=False).head(5)
    return artist_songs[['song', 'rating']]

artists_list = sorted(df['artist'].unique())

# --- Streamlit App ---

# Custom CSS for Sidebar
st.markdown("""
    <style>
    .sidebar .sidebar-content {
        background: #f0f0f5;
        color: #333;
        padding: 1rem;
        border-radius: 8px;
    }
    .sidebar .sidebar-content .stButton button {
        background-color: #007bff;
        color: #fff;
    }
    .sidebar .sidebar-content .stButton button:hover {
        background-color: #0056b3;
    }
    .sidebar .sidebar-content img {
        max-width: 80%;
        height: auto;
    }
    .sidebar .sidebar-content .stSelectbox {
        font-size: 18px;
    }
    .sidebar .sidebar-content .stButton {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation with Custom Header Image and Text
st.sidebar.image(r"C:\Users\Tan\Downloads\Music_Recommender_System\Music_Recommender_System\spotify-logo.jpg", width=300)

nav_option = st.sidebar.selectbox("Choose an option", 
    ["📅 Most People Like", 
     "🎵 Music Recommender", 
     "⭐ Recommend Artist's Top Rated Song", 
     "📝 Rate Us"]
)

if nav_option == "📅 Most People Like":
    st.header("Most People Like")
    
    if 'random_songs' not in st.session_state:
        st.session_state.random_songs = recommend_random_songs()

    # Add a button to refresh the songs
    if st.button("Refresh Top 3 Songs"):
        st.session_state.random_songs = recommend_random_songs()

    random_songs = st.session_state.random_songs
    if random_songs is not None:
        col1, col2, col3 = st.columns(3)
        for idx, (song, artist) in enumerate(zip(random_songs['song'], random_songs['artist'])):
            album_cover_url = get_song_album_cover_url(song, artist)
            with [col1, col2, col3][idx % 3]:
                st.text(song)
                st.image(album_cover_url)

elif nav_option == "🎵 Music Recommender":
    st.header('Music Recommender')
    selected_song = st.selectbox("Select a song from the dropdown", music['song'].values)

    if st.button('Show Recommendation'):
        recommended_music_names, recommended_music_posters = recommend(selected_song)
        col1, col2, col3, col4, col5 = st.columns(5)
        for idx, col in enumerate([col1, col2, col3, col4, col5]):
            with col:
                st.text(recommended_music_names[idx])
                st.image(recommended_music_posters[idx])

elif nav_option == "⭐ Recommend Artist's Top Rated Song":
    st.header("Select an artist")

    selected_artist = st.selectbox("Select an artist", artists_list)

    if st.button("Recommend Artist's Top Rated Song"):
        if selected_artist:
            recommended_songs = recommend_artist_songs(selected_artist)
            if not recommended_songs.empty:
                col1, col2, col3, col4, col5 = st.columns(5)
                for idx, (song, _) in enumerate(zip(recommended_songs['song'], recommended_songs['rating'])):
                    album_cover_url = get_song_album_cover_url(song, selected_artist)
                    with [col1, col2, col3, col4, col5][idx % 5]:
                        st.text(song)
                        st.image(album_cover_url)
            else:
                st.write("No songs found for this artist.")
        else:
            st.warning("Please select an artist.")

elif nav_option == "📝 Rate Us":
    st.header("Rate a Song")

    selected_artist = st.selectbox("Select an artist to rate", artists_list)
    if selected_artist:
        artist_songs = df[df['artist'] == selected_artist]['song'].unique()
        selected_song = st.selectbox("Select a song", artist_songs)

        rating = st.slider("Rate the song (0 to 5)", min_value=0.0, max_value=5.0, step=0.1, format="%.1f")

        # Adding a comment box
        comment = st.text_area("Leave a comment about the song", placeholder="What did you think about this song?")

        if st.button("Submit rating"):
            st.success(f"Rating for '{selected_song}' by '{selected_artist}': {rating} stars")
            if comment:
                st.write(f"Your comment: {comment}")
            else:
                st.write("No comment provided.")

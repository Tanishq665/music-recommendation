from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)

# Replace with your Spotify Client ID and Client Secret
CLIENT_ID = 'dd391fd7f79b46eb86d5b876c794a1a0'
CLIENT_SECRET = '8e5f649973d74ab4898426d3d10d8aa1'

# Initialize Spotipy
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Function to fetch music data from Spotify playlist
def get_trending_playlist_data(playlist_id):
    playlist_tracks = sp.playlist_tracks(playlist_id, fields='items(track(id, name, artists, album(id, name)))')
    music_data = []

    for track_info in playlist_tracks['items']:
        track = track_info['track']
        track_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album_name = track['album']['name']
        album_id = track['album']['id']
        track_id = track['id']

        # Get audio features for the track
        audio_features = sp.audio_features(track_id)[0] if track_id else None

        # Get release date of the album
        try:
            album_info = sp.album(album_id) if album_id else None
            release_date = album_info['release_date'] if album_info else None
        except:
            release_date = None

        # Get popularity of the track
        try:
            track_info = sp.track(track_id) if track_id else None
            popularity = track_info['popularity'] if track_info else None
        except:
            popularity = None

        # Add track information to the music data
        track_data = {
            'Track Name': track_name,
            'Artists': artists,
            'Album Name': album_name,
            'Release Date': release_date,
            'Popularity': popularity,
            'Duration (ms)': audio_features['duration_ms'] if audio_features else None,
            'Danceability': audio_features['danceability'] if audio_features else None,
            'Energy': audio_features['energy'] if audio_features else None,
            'Key': audio_features['key'] if audio_features else None,
            'Loudness': audio_features['loudness'] if audio_features else None,
            'Mode': audio_features['mode'] if audio_features else None,
            'Speechiness': audio_features['speechiness'] if audio_features else None,
            'Acousticness': audio_features['acousticness'] if audio_features else None,
            'Instrumentalness': audio_features['instrumentalness'] if audio_features else None,
            'Liveness': audio_features['liveness'] if audio_features else None,
            'Valence': audio_features['valence'] if audio_features else None,
            'Tempo': audio_features['tempo'] if audio_features else None,
        }
        music_data.append(track_data)

    return pd.DataFrame(music_data)

# Normalize music features using Min-Max scaling
music_df = get_trending_playlist_data('37i9dQZF1DX76Wlfdnj7AP')
scaler = MinMaxScaler()
music_features = music_df[['Danceability', 'Energy', 'Key',
                           'Loudness', 'Mode', 'Speechiness', 'Acousticness',
                           'Instrumentalness', 'Liveness', 'Valence', 'Tempo']].values
music_features_scaled = scaler.fit_transform(music_features)

# Function to calculate weighted popularity scores based on release date
def calculate_weighted_popularity(release_date):
    release_date = datetime.strptime(release_date, '%Y-%m-%d')
    time_span = datetime.now() - release_date
    weight = 1 / (time_span.days + 1)
    return weight

# Content-based recommendations based on music features
def content_based_recommendations(input_song_name, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        return []

    input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]
    similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]
    return music_df.iloc[similar_song_indices].to_dict(orient='records')

# Hybrid recommendations based on weighted popularity
def hybrid_recommendations(input_song_name, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        return []

    content_based_rec = content_based_recommendations(input_song_name, num_recommendations)
    popularity_score = music_df.loc[music_df['Track Name'] == input_song_name, 'Popularity'].values[0]
    weighted_popularity_score = popularity_score * calculate_weighted_popularity(music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0])
    
    hybrid_recommendations = content_based_rec
    hybrid_recommendations.append({
        'Track Name': input_song_name,
        'Artists': music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0],
        'Album Name': music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0],
        'Release Date': music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0],
        'Popularity': weighted_popularity_score
    })
    return sorted(hybrid_recommendations, key=lambda x: x['Popularity'], reverse=True)[:num_recommendations]

# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for getting recommendations
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    song_name = data['song_name']
    recommendations = hybrid_recommendations(song_name)
    return jsonify(recommendations)

if __name__ == '__main__':
    app.run(debug=True)

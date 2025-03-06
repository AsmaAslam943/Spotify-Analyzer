from flask import Flask, request, redirect, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

# Set up Spotify OAuth settings
SCOPE = "user-read-private user-read-email playlist-read-private playlist-read-collaborative user-library-read"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
CLIENT_ID = '70c7286c415e4480b59e1c61772624b0'  # Replace with your Spotify client ID
CLIENT_SECRET = '151c4150586c46b289a958cec4a84e54'  # Replace with your Spotify client secret


# Set up Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Route to start the authentication flow
@app.route('/')
def index():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback route to handle the response from Spotify after authentication
@app.route('/callback')
def callback():
    try:
        token_info = sp_oauth.get_access_token(request.args['code'])
        sp = spotipy.Spotify(auth=token_info['access_token'])

        # Example playlist URL
        playlist_url = "spotify:playlist:6MfBWckYX1WRr6Hnf4FZV8"
        tracks = get_playlist_tracks(sp, playlist_url)
        analysis = analyze_playlist(sp, playlist_url)
        
        return jsonify(analysis)
    except Exception as e:
        print(f"Error in callback: {e}")
        return jsonify({"error": str(e)})

# Function to fetch playlist tracks
def get_playlist_tracks(sp, playlist_url):
    try:
        # Extract playlist ID from URL or URI
        if "playlist" in playlist_url:
            playlist_id = playlist_url.split(":")[-1]
        else:
            playlist_id = playlist_url
        
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        return [track['track'] for track in tracks]  # Extract track information
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

# Function to fetch audio features for the tracks
def get_audio_features(sp, track_ids):
    # Limit the number of tracks to avoid issues with too many requests
    track_ids = track_ids[:50]  # Spotify allows fetching up to 50 tracks at once

    try:
        features = sp.audio_features(track_ids)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error fetching audio features: {e}")
        return []

    if features is None:
        print("No features returned.")
        return []

    return [{"id": f["id"], "tempo": f["tempo"], "energy": f["energy"], "danceability": f["danceability"]} for f in features]

    
# Function to analyze the playlist based on its tracks' audio features
def analyze_playlist(sp, playlist_url):
    try:
        tracks = get_playlist_tracks(sp, playlist_url)
        track_ids = [track["id"] for track in tracks if track and "id" in track]  # Ensure track IDs are valid

        if not track_ids:
            print("No tracks found in the playlist.")
            return {"error": "No tracks found in the playlist."}

        features = get_audio_features(sp, track_ids)
        
        # Handle case where no features are returned
        if not features:
            print("No audio features found.")
            return {"error": "No audio features found."}

        df = pd.DataFrame(features)

        avg_tempo = df["tempo"].mean() if not df["tempo"].isnull().all() else 0
        avg_energy = df["energy"].mean() if not df["energy"].isnull().all() else 0
        avg_danceability = df["danceability"].mean() if not df["danceability"].isnull().all() else 0

        analysis = {
            "avg_tempo": avg_tempo,
            "avg_energy": avg_energy,
            "avg_danceability": avg_danceability
        }

        print(f"📊 Playlist Analysis:")
        print(f"🎵 Average Tempo: {avg_tempo:.2f} BPM")
        print(f"⚡ Average Energy: {avg_energy:.2f}")
        print(f"💃 Average Danceability: {avg_danceability:.2f}")
        
        return analysis
    except Exception as e:
        print(f"Error analyzing playlist: {e}")
        return {"error": str(e)}

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=8888)

import spotipy
import spotipy.oauth2
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import configs


class SpotifyScraper:
    def __init__(self):
        self._auth_manager = SpotifyClientCredentials(client_id=configs.spotify_id, client_secret=configs.spotify_secret)
        self._spot = spotipy.Spotify(auth_manager=self._auth_manager)

    def playlist_songs(self, url):
        songs = []
        try:
            playlist = self._spot.playlist_items(url)["items"]
            for song in playlist:
                song = song["track"]
                songs.append(f"{song['artists'][0]['name']} - {song['name']}")
        except:
            print("In Exception")
            playlist = self._spot.album_tracks(url)["items"]
            for song in playlist:
                songs.append(f"{song['artists'][0]['name']} - {song['name']}")
        return songs




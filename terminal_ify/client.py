import os

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

load_dotenv()

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-library-read",
    "user-library-modify",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-read-recently-played",
    "user-top-read",
])


class SpotifyClient:
    def __init__(self):
        auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback"),
            scope=SCOPES,
            cache_path=".spotify_cache",
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_current_playback(self) -> dict | None:
        try:
            return self.sp.current_playback()
        except SpotifyException:
            return None

    def play(
        self,
        context_uri: str | None = None,
        uris: list[str] | None = None,
        device_id: str | None = None,
        offset: dict | None = None,
    ) -> None:
        try:
            self.sp.start_playback(
                device_id=device_id,
                context_uri=context_uri,
                uris=uris,
                offset=offset,
            )
        except SpotifyException:
            pass

    def pause(self, device_id: str | None = None) -> None:
        try:
            self.sp.pause_playback(device_id=device_id)
        except SpotifyException:
            pass

    def next_track(self, device_id: str | None = None) -> None:
        try:
            self.sp.next_track(device_id=device_id)
        except SpotifyException:
            pass

    def previous_track(self, device_id: str | None = None) -> None:
        try:
            self.sp.previous_track(device_id=device_id)
        except SpotifyException:
            pass

    def seek(self, position_ms: int) -> None:
        try:
            self.sp.seek_track(position_ms)
        except SpotifyException:
            pass

    def set_volume(self, volume_percent: int) -> None:
        try:
            self.sp.volume(volume_percent)
        except SpotifyException:
            pass

    def toggle_shuffle(self, state: bool) -> None:
        try:
            self.sp.shuffle(state)
        except SpotifyException:
            pass

    def set_repeat(self, state: str) -> None:
        try:
            self.sp.repeat(state)
        except SpotifyException:
            pass

    def get_devices(self) -> list:
        try:
            result = self.sp.devices()
            return result.get("devices", [])
        except SpotifyException:
            return []

    def transfer_playback(self, device_id: str) -> None:
        try:
            self.sp.transfer_playback(device_id)
        except SpotifyException:
            pass

    def search(self, query: str, types: list[str], limit: int = 20) -> dict:
        try:
            return self.sp.search(q=query, type=",".join(types), limit=limit)
        except SpotifyException:
            return {}

    def get_playlists(self, limit: int = 50) -> list:
        try:
            result = self.sp.current_user_playlists(limit=limit)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_playlist_tracks(self, playlist_id: str) -> list:
        try:
            result = self.sp.playlist_tracks(playlist_id)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_saved_tracks(self, limit: int = 50, offset: int = 0) -> list:
        try:
            result = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_saved_albums(self, limit: int = 50) -> list:
        try:
            result = self.sp.current_user_saved_albums(limit=limit)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_album_tracks(self, album_id: str) -> list:
        try:
            result = self.sp.album_tracks(album_id)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_queue(self) -> dict:
        try:
            return self.sp.queue()
        except SpotifyException:
            return {}

    def add_to_queue(self, uri: str) -> None:
        try:
            self.sp.add_to_queue(uri)
        except SpotifyException:
            pass

    def get_recently_played(self, limit: int = 20) -> list:
        try:
            result = self.sp.current_user_recently_played(limit=limit)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_artist(self, artist_id: str) -> dict:
        try:
            return self.sp.artist(artist_id)
        except SpotifyException:
            return {}

    def get_artist_top_tracks(self, artist_id: str) -> list:
        try:
            result = self.sp.artist_top_tracks(artist_id)
            return result.get("tracks", [])
        except SpotifyException:
            return []

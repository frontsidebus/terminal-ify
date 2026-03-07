import json
import os
import sys
import time
import uuid
import webbrowser
from urllib.request import urlopen
from urllib.error import URLError

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

load_dotenv()

REMOTE_CALLBACK_URL = "https://terminalify.343-guilty-spark.io/callback"
REMOTE_TOKEN_URL = "https://terminalify.343-guilty-spark.io/token"

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


def remote_auth() -> bool:
    """Authenticate via the remote AWS Lambda OAuth callback flow.

    Opens the Spotify authorization page in the user's browser, then polls
    the remote token endpoint until tokens are returned or the timeout is
    reached.

    Returns True on success, False on timeout.
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    session_id = str(uuid.uuid4())

    authorize_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={client_id}"
        "&response_type=code"
        f"&redirect_uri={REMOTE_CALLBACK_URL}"
        f"&scope={SCOPES}"
        f"&state={session_id}"
    )

    print("Opening Spotify authorization in your browser...")
    webbrowser.open(authorize_url)

    print("Waiting for authorization", end="", flush=True)
    poll_interval = 2
    max_wait = 120
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        print(".", end="", flush=True)

        try:
            response = urlopen(f"{REMOTE_TOKEN_URL}/{session_id}")
            if response.status == 200:
                token_data = json.loads(response.read().decode())
                # Ensure the token data has the fields spotipy expects
                if "access_token" not in token_data:
                    continue
                if "expires_at" not in token_data:
                    token_data["expires_at"] = int(time.time()) + token_data.get("expires_in", 3600)
                if "token_type" not in token_data:
                    token_data["token_type"] = "Bearer"
                if "scope" not in token_data:
                    token_data["scope"] = SCOPES

                with open(".spotify_cache", "w") as f:
                    json.dump(token_data, f)

                print("\nAuthorization successful!")
                return True
        except (URLError, json.JSONDecodeError):
            continue

    print("\nAuthorization timed out. Please try again.")
    return False


class SpotifyClient:
    def __init__(self):
        cache_path = ".spotify_cache"
        cache_valid = False

        # Check if we already have a valid cached token
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached = json.load(f)
                if cached.get("access_token") and cached.get("expires_at", 0) > time.time():
                    cache_valid = True
            except (json.JSONDecodeError, OSError):
                pass

        # If no valid cache and we're in a terminal, try remote auth
        if not cache_valid and sys.stdout.isatty():
            remote_auth()

        auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=REMOTE_CALLBACK_URL,
            scope=SCOPES,
            cache_path=cache_path,
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

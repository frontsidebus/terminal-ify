import json
import sys
import time
import uuid
import webbrowser
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError

import spotipy
from spotipy.exceptions import SpotifyException

API_BASE = "https://terminalify.343-guilty-spark.io"
CACHE_PATH = ".spotify_cache"


def fetch_config() -> dict:
    """Fetch client_id, redirect_uri, and scope from the server."""
    resp = urlopen(f"{API_BASE}/config")
    return json.loads(resp.read().decode())


def refresh_token_remote(refresh_token: str) -> dict | None:
    """Exchange a refresh token for new access token via the server."""
    data = json.dumps({"refresh_token": refresh_token}).encode()
    req = Request(
        f"{API_BASE}/refresh",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except URLError:
        return None


def load_cached_token() -> dict | None:
    """Load token from cache file if it exists."""
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save_token(token_data: dict) -> None:
    """Save token data to cache file."""
    with open(CACHE_PATH, "w") as f:
        json.dump(token_data, f)


def ensure_valid_token() -> dict | None:
    """Return a valid access token, refreshing or re-authing as needed."""
    token = load_cached_token()

    if token and token.get("access_token"):
        # Still valid
        if token.get("expires_at", 0) > time.time() + 60:
            return token

        # Try refresh
        if token.get("refresh_token"):
            new_token = refresh_token_remote(token["refresh_token"])
            if new_token and "access_token" in new_token:
                # Preserve refresh_token if not returned
                if "refresh_token" not in new_token:
                    new_token["refresh_token"] = token["refresh_token"]
                new_token["expires_at"] = int(time.time()) + new_token.get("expires_in", 3600)
                save_token(new_token)
                return new_token

    # Need fresh auth
    if sys.stdout.isatty():
        if remote_auth():
            return load_cached_token()

    return None


def remote_auth() -> bool:
    """Authenticate via the remote OAuth callback flow."""
    try:
        config = fetch_config()
    except URLError:
        print("\n[terminal-ify] Could not reach auth server. Check your connection.")
        return False

    client_id = config["client_id"]
    redirect_uri = config["redirect_uri"]
    scope = config["scope"]
    session_id = str(uuid.uuid4())

    authorize_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={client_id}"
        "&response_type=code"
        f"&redirect_uri={quote(redirect_uri, safe='')}"
        f"&scope={quote(scope, safe='')}"
        f"&state={session_id}"
    )

    opened = webbrowser.open(authorize_url)
    if not opened:
        print("Could not open browser automatically. Open this URL manually:\n")
        print(f"  {authorize_url}\n")
    else:
        print("Opening Spotify authorization in your browser...")

    print("Waiting for authorization", end="", flush=True)

    for _ in range(60):
        time.sleep(2)
        print(".", end="", flush=True)

        try:
            resp = urlopen(f"{API_BASE}/token/{session_id}")
            if resp.status == 200:
                token_data = json.loads(resp.read().decode())
                if "access_token" not in token_data:
                    continue
                token_data.setdefault("expires_at", int(time.time()) + token_data.get("expires_in", 3600))
                token_data.setdefault("token_type", "Bearer")
                token_data.setdefault("scope", scope)
                save_token(token_data)
                print("\nAuthorization successful!")
                return True
        except (URLError, json.JSONDecodeError):
            continue

    print("\nAuthorization timed out. Please try again.")
    return False


class SpotifyClient:
    def __init__(self):
        token = ensure_valid_token()
        if not token:
            raise RuntimeError("Could not obtain Spotify access token")

        self.sp = spotipy.Spotify(auth=token["access_token"])
        self._token = token

    def _refresh_if_needed(self) -> None:
        if self._token.get("expires_at", 0) < time.time() + 60:
            new_token = refresh_token_remote(self._token.get("refresh_token", ""))
            if new_token and "access_token" in new_token:
                if "refresh_token" not in new_token:
                    new_token["refresh_token"] = self._token.get("refresh_token", "")
                new_token["expires_at"] = int(time.time()) + new_token.get("expires_in", 3600)
                save_token(new_token)
                self._token = new_token
                self.sp = spotipy.Spotify(auth=new_token["access_token"])

    def get_current_playback(self) -> dict | None:
        try:
            self._refresh_if_needed()
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
            self._refresh_if_needed()
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
            self._refresh_if_needed()
            self.sp.pause_playback(device_id=device_id)
        except SpotifyException:
            pass

    def next_track(self, device_id: str | None = None) -> None:
        try:
            self._refresh_if_needed()
            self.sp.next_track(device_id=device_id)
        except SpotifyException:
            pass

    def previous_track(self, device_id: str | None = None) -> None:
        try:
            self._refresh_if_needed()
            self.sp.previous_track(device_id=device_id)
        except SpotifyException:
            pass

    def seek(self, position_ms: int) -> None:
        try:
            self._refresh_if_needed()
            self.sp.seek_track(position_ms)
        except SpotifyException:
            pass

    def set_volume(self, volume_percent: int) -> None:
        try:
            self._refresh_if_needed()
            self.sp.volume(volume_percent)
        except SpotifyException:
            pass

    def toggle_shuffle(self, state: bool) -> None:
        try:
            self._refresh_if_needed()
            self.sp.shuffle(state)
        except SpotifyException:
            pass

    def set_repeat(self, state: str) -> None:
        try:
            self._refresh_if_needed()
            self.sp.repeat(state)
        except SpotifyException:
            pass

    def get_devices(self) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.devices()
            return result.get("devices", [])
        except SpotifyException:
            return []

    def transfer_playback(self, device_id: str) -> None:
        try:
            self._refresh_if_needed()
            self.sp.transfer_playback(device_id)
        except SpotifyException:
            pass

    def search(self, query: str, types: list[str], limit: int = 20) -> dict:
        try:
            self._refresh_if_needed()
            return self.sp.search(q=query, type=",".join(types), limit=limit)
        except SpotifyException:
            return {}

    def get_playlists(self, limit: int = 50) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.current_user_playlists(limit=limit)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_playlist_tracks(self, playlist_id: str) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.playlist_tracks(playlist_id)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_saved_tracks(self, limit: int = 50, offset: int = 0) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_saved_albums(self, limit: int = 50) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.current_user_saved_albums(limit=limit)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_album_tracks(self, album_id: str) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.album_tracks(album_id)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_queue(self) -> dict:
        try:
            self._refresh_if_needed()
            return self.sp.queue()
        except SpotifyException:
            return {}

    def add_to_queue(self, uri: str) -> None:
        try:
            self._refresh_if_needed()
            self.sp.add_to_queue(uri)
        except SpotifyException:
            pass

    def get_recently_played(self, limit: int = 20) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.current_user_recently_played(limit=limit)
            return result.get("items", [])
        except SpotifyException:
            return []

    def get_artist(self, artist_id: str) -> dict:
        try:
            self._refresh_if_needed()
            return self.sp.artist(artist_id)
        except SpotifyException:
            return {}

    def get_artist_top_tracks(self, artist_id: str) -> list:
        try:
            self._refresh_if_needed()
            result = self.sp.artist_top_tracks(artist_id)
            return result.get("tracks", [])
        except SpotifyException:
            return []

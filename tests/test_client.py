"""Tests for terminal_ify.client — SpotifyClient and auth helpers."""

import json
import time
from unittest.mock import MagicMock, mock_open, patch, PropertyMock
from urllib.error import URLError

import pytest

from spotipy.exceptions import SpotifyException

# We import the module-level functions and the class separately.
import terminal_ify.client as client_mod
from terminal_ify.client import (
    API_BASE,
    CACHE_PATH,
    SpotifyClient,
    ensure_valid_token,
    fetch_config,
    load_cached_token,
    refresh_token_remote,
    save_token,
)


# ---------------------------------------------------------------------------
# fetch_config
# ---------------------------------------------------------------------------


class TestFetchConfig:
    @patch("terminal_ify.client.urlopen")
    def test_returns_parsed_json(self, mock_urlopen):
        payload = {"client_id": "cid", "redirect_uri": "https://example.com/cb", "scope": "user-read-playback-state"}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_urlopen.return_value = mock_resp

        result = fetch_config()
        assert result == payload
        mock_urlopen.assert_called_once_with(f"{API_BASE}/config", timeout=10)

    @patch("terminal_ify.client.urlopen", side_effect=URLError("no network"))
    def test_raises_on_network_error(self, mock_urlopen):
        with pytest.raises(URLError):
            fetch_config()


# ---------------------------------------------------------------------------
# refresh_token_remote
# ---------------------------------------------------------------------------


class TestRefreshTokenRemote:
    @patch("terminal_ify.client.urlopen")
    def test_returns_new_token(self, mock_urlopen):
        new_token = {"access_token": "new-at", "expires_in": 3600}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(new_token).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = refresh_token_remote("old-refresh")
        assert result == new_token

    @patch("terminal_ify.client.urlopen", side_effect=URLError("fail"))
    def test_returns_none_on_error(self, mock_urlopen):
        result = refresh_token_remote("old-refresh")
        assert result is None


# ---------------------------------------------------------------------------
# load_cached_token / save_token
# ---------------------------------------------------------------------------


class TestTokenCache:
    @patch("builtins.open", mock_open(read_data='{"access_token": "at"}'))
    def test_load_cached_token_success(self):
        result = load_cached_token()
        assert result == {"access_token": "at"}

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_cached_token_missing_file(self, _):
        assert load_cached_token() is None

    @patch("builtins.open", mock_open(read_data="not json"))
    def test_load_cached_token_bad_json(self):
        assert load_cached_token() is None

    @patch("terminal_ify.client.os.fdopen", new_callable=mock_open)
    @patch("terminal_ify.client.os.open", return_value=99)
    def test_save_token_writes_json_with_restricted_perms(self, m_os_open, m_fdopen):
        token = {"access_token": "at", "refresh_token": "rt"}
        save_token(token)
        import os as _os
        m_os_open.assert_called_once_with(
            CACHE_PATH, _os.O_WRONLY | _os.O_CREAT | _os.O_TRUNC, 0o600
        )
        handle = m_fdopen()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        assert json.loads(written) == token


# ---------------------------------------------------------------------------
# ensure_valid_token
# ---------------------------------------------------------------------------


class TestEnsureValidToken:
    @patch("terminal_ify.client.load_cached_token")
    def test_returns_valid_token(self, mock_load, mock_token):
        mock_load.return_value = mock_token
        result = ensure_valid_token()
        assert result == mock_token

    @patch("terminal_ify.client.save_token")
    @patch("terminal_ify.client.refresh_token_remote")
    @patch("terminal_ify.client.load_cached_token")
    def test_refreshes_expired_token(self, mock_load, mock_refresh, mock_save, expired_token):
        mock_load.return_value = expired_token
        new_token = {"access_token": "refreshed", "expires_in": 3600}
        mock_refresh.return_value = new_token

        result = ensure_valid_token()
        assert result is not None
        assert result["access_token"] == "refreshed"
        mock_refresh.assert_called_once_with(expired_token["refresh_token"])
        mock_save.assert_called_once()

    @patch("terminal_ify.client.save_token")
    @patch("terminal_ify.client.refresh_token_remote")
    @patch("terminal_ify.client.load_cached_token")
    def test_preserves_refresh_token_on_refresh(self, mock_load, mock_refresh, mock_save, expired_token):
        mock_load.return_value = expired_token
        # Server response without refresh_token
        new_token = {"access_token": "refreshed", "expires_in": 3600}
        mock_refresh.return_value = new_token

        result = ensure_valid_token()
        assert result["refresh_token"] == expired_token["refresh_token"]

    @patch("terminal_ify.client.remote_auth", return_value=False)
    @patch("terminal_ify.client.load_cached_token", return_value=None)
    @patch("sys.stdout")
    def test_returns_none_when_no_token_and_auth_fails(self, mock_stdout, mock_load, mock_auth):
        mock_stdout.isatty.return_value = True
        result = ensure_valid_token()
        assert result is None

    @patch("terminal_ify.client.load_cached_token", return_value=None)
    @patch("sys.stdout")
    def test_returns_none_when_not_tty(self, mock_stdout, mock_load):
        mock_stdout.isatty.return_value = False
        result = ensure_valid_token()
        assert result is None


# ---------------------------------------------------------------------------
# SpotifyClient.__init__
# ---------------------------------------------------------------------------


class TestSpotifyClientInit:
    @patch("terminal_ify.client.spotipy.Spotify")
    @patch("terminal_ify.client.ensure_valid_token")
    def test_creates_client_with_valid_token(self, mock_ensure, mock_sp_cls, mock_token):
        mock_ensure.return_value = mock_token
        c = SpotifyClient()
        mock_sp_cls.assert_called_once_with(auth=mock_token["access_token"])
        assert c._token == mock_token

    @patch("terminal_ify.client.ensure_valid_token", return_value=None)
    def test_raises_when_no_token(self, _):
        with pytest.raises(RuntimeError, match="Could not obtain"):
            SpotifyClient()


# ---------------------------------------------------------------------------
# SpotifyClient methods
# ---------------------------------------------------------------------------


class TestSpotifyClientMethods:
    @pytest.fixture(autouse=True)
    def setup_client(self, mock_token, mock_spotify):
        with patch("terminal_ify.client.ensure_valid_token", return_value=mock_token), \
             patch("terminal_ify.client.spotipy.Spotify", return_value=mock_spotify):
            self.client = SpotifyClient()
            self.sp = mock_spotify
            self.token = mock_token

    # -- get_current_playback --

    def test_get_current_playback_returns_data(self, sample_playback):
        self.sp.current_playback.return_value = sample_playback
        result = self.client.get_current_playback()
        assert result == sample_playback
        self.sp.current_playback.assert_called_once()

    def test_get_current_playback_returns_none_on_error(self):
        self.sp.current_playback.side_effect = SpotifyException(401, -1, "Unauthorized")
        result = self.client.get_current_playback()
        assert result is None

    # -- play --

    def test_play_with_uris(self):
        self.client.play(uris=["spotify:track:abc"])
        self.sp.start_playback.assert_called_once_with(
            device_id=None, context_uri=None, uris=["spotify:track:abc"], offset=None
        )

    def test_play_with_context_uri(self):
        self.client.play(context_uri="spotify:album:xyz")
        self.sp.start_playback.assert_called_once_with(
            device_id=None, context_uri="spotify:album:xyz", uris=None, offset=None
        )

    def test_play_swallows_exception(self):
        self.sp.start_playback.side_effect = SpotifyException(403, -1, "Forbidden")
        self.client.play(uris=["spotify:track:abc"])  # should not raise

    # -- pause --

    def test_pause(self):
        self.client.pause()
        self.sp.pause_playback.assert_called_once_with(device_id=None)

    def test_pause_swallows_exception(self):
        self.sp.pause_playback.side_effect = SpotifyException(403, -1, "Forbidden")
        self.client.pause()  # no raise

    # -- next / previous --

    def test_next_track(self):
        self.client.next_track()
        self.sp.next_track.assert_called_once()

    def test_previous_track(self):
        self.client.previous_track()
        self.sp.previous_track.assert_called_once()

    # -- seek --

    def test_seek(self):
        self.client.seek(30000)
        self.sp.seek_track.assert_called_once_with(30000)

    # -- volume --

    def test_set_volume(self):
        self.client.set_volume(80)
        self.sp.volume.assert_called_once_with(80)

    # -- shuffle --

    def test_toggle_shuffle(self):
        self.client.toggle_shuffle(True)
        self.sp.shuffle.assert_called_once_with(True)

    # -- repeat --

    def test_set_repeat(self):
        self.client.set_repeat("track")
        self.sp.repeat.assert_called_once_with("track")

    # -- devices --

    def test_get_devices(self):
        devices = [{"id": "d1", "name": "Speaker"}]
        self.sp.devices.return_value = {"devices": devices}
        result = self.client.get_devices()
        assert result == devices

    def test_get_devices_returns_empty_on_error(self):
        self.sp.devices.side_effect = SpotifyException(500, -1, "Server Error")
        assert self.client.get_devices() == []

    # -- transfer_playback --

    def test_transfer_playback(self):
        self.client.transfer_playback("device-abc")
        self.sp.transfer_playback.assert_called_once_with("device-abc")

    # -- search --

    def test_search(self, sample_search_results):
        self.sp.search.return_value = sample_search_results
        result = self.client.search("test query", types=["track", "album"], limit=10)
        self.sp.search.assert_called_once_with(q="test query", type="track,album", limit=10)
        assert result == sample_search_results

    def test_search_returns_empty_on_error(self):
        self.sp.search.side_effect = SpotifyException(500, -1, "Error")
        assert self.client.search("q", types=["track"]) == {}

    # -- playlists --

    def test_get_playlists(self, sample_playlists):
        self.sp.current_user_playlists.return_value = {"items": sample_playlists}
        result = self.client.get_playlists()
        assert result == sample_playlists

    def test_get_playlists_returns_empty_on_error(self):
        self.sp.current_user_playlists.side_effect = SpotifyException(500, -1, "Error")
        assert self.client.get_playlists() == []

    def test_get_playlist_tracks(self, sample_playlist_tracks):
        self.sp.playlist_tracks.return_value = {"items": sample_playlist_tracks}
        result = self.client.get_playlist_tracks("pl-123")
        assert result == sample_playlist_tracks

    # -- saved tracks / albums --

    def test_get_saved_tracks(self):
        items = [{"track": {"name": "Saved"}}]
        self.sp.current_user_saved_tracks.return_value = {"items": items}
        result = self.client.get_saved_tracks(limit=20)
        assert result == items

    def test_get_saved_albums(self):
        items = [{"album": {"name": "Saved Album"}}]
        self.sp.current_user_saved_albums.return_value = {"items": items}
        result = self.client.get_saved_albums()
        assert result == items

    def test_get_album_tracks(self):
        items = [{"name": "Track 1"}]
        self.sp.album_tracks.return_value = {"items": items}
        result = self.client.get_album_tracks("alb-1")
        assert result == items

    # -- queue --

    def test_get_queue(self):
        queue_data = {"currently_playing": None, "queue": []}
        self.sp.queue.return_value = queue_data
        assert self.client.get_queue() == queue_data

    def test_get_queue_returns_empty_on_error(self):
        self.sp.queue.side_effect = SpotifyException(500, -1, "Error")
        assert self.client.get_queue() == {}

    def test_add_to_queue(self):
        self.client.add_to_queue("spotify:track:q1")
        self.sp.add_to_queue.assert_called_once_with("spotify:track:q1")

    # -- recently played --

    def test_get_recently_played(self):
        items = [{"track": {"name": "Recent"}}]
        self.sp.current_user_recently_played.return_value = {"items": items}
        assert self.client.get_recently_played(limit=5) == items

    # -- artist --

    def test_get_artist(self):
        artist = {"name": "Test Artist", "id": "a1"}
        self.sp.artist.return_value = artist
        assert self.client.get_artist("a1") == artist

    def test_get_artist_returns_empty_on_error(self):
        self.sp.artist.side_effect = SpotifyException(404, -1, "Not found")
        assert self.client.get_artist("bad") == {}

    def test_get_artist_top_tracks(self):
        tracks = [{"name": "Top Hit"}]
        self.sp.artist_top_tracks.return_value = {"tracks": tracks}
        assert self.client.get_artist_top_tracks("a1") == tracks


# ---------------------------------------------------------------------------
# Token refresh inside client methods
# ---------------------------------------------------------------------------


class TestClientTokenRefresh:
    @patch("terminal_ify.client.save_token")
    @patch("terminal_ify.client.refresh_token_remote")
    @patch("terminal_ify.client.spotipy.Spotify")
    @patch("terminal_ify.client.ensure_valid_token")
    def test_refresh_if_needed_refreshes_expired(self, mock_ensure, mock_sp_cls, mock_refresh, mock_save, expired_token):
        mock_ensure.return_value = expired_token
        mock_sp_instance = MagicMock()
        mock_sp_cls.return_value = mock_sp_instance

        c = SpotifyClient()

        new_token = {"access_token": "new-at", "expires_in": 3600}
        mock_refresh.return_value = new_token

        mock_sp_instance.current_playback.return_value = None
        c.get_current_playback()

        mock_refresh.assert_called_once_with(expired_token["refresh_token"])
        mock_save.assert_called_once()
        # Should have created a new Spotify instance with the new token
        assert mock_sp_cls.call_count == 2  # once in __init__, once after refresh

    @patch("terminal_ify.client.refresh_token_remote")
    @patch("terminal_ify.client.spotipy.Spotify")
    @patch("terminal_ify.client.ensure_valid_token")
    def test_no_refresh_when_token_valid(self, mock_ensure, mock_sp_cls, mock_refresh, mock_token):
        mock_ensure.return_value = mock_token
        mock_sp_cls.return_value = MagicMock()

        c = SpotifyClient()
        c.get_current_playback()

        mock_refresh.assert_not_called()

    @patch("terminal_ify.client.refresh_token_remote", return_value=None)
    @patch("terminal_ify.client.spotipy.Spotify")
    @patch("terminal_ify.client.ensure_valid_token")
    def test_refresh_failure_keeps_old_token(self, mock_ensure, mock_sp_cls, mock_refresh, expired_token):
        mock_ensure.return_value = expired_token
        mock_sp_instance = MagicMock()
        mock_sp_cls.return_value = mock_sp_instance

        c = SpotifyClient()
        mock_sp_instance.current_playback.return_value = None
        c.get_current_playback()

        # refresh was attempted but failed; token should remain the same
        assert c._token == expired_token


# ---------------------------------------------------------------------------
# remote_auth
# ---------------------------------------------------------------------------


class TestRemoteAuth:
    @patch("terminal_ify.client.save_token")
    @patch("terminal_ify.client.urlopen")
    @patch("terminal_ify.client.webbrowser.open", return_value=True)
    @patch("terminal_ify.client.fetch_config")
    @patch("terminal_ify.client.time.sleep")
    @patch("builtins.print")
    def test_remote_auth_success(self, mock_print, mock_sleep, mock_config, mock_browser, mock_urlopen, mock_save):
        mock_config.return_value = {
            "client_id": "cid",
            "redirect_uri": "https://example.com/cb",
            "scope": "user-read-playback-state",
        }
        token_resp = MagicMock()
        token_resp.status = 200
        token_resp.read.return_value = json.dumps({
            "access_token": "at-123",
            "refresh_token": "rt-456",
            "expires_in": 3600,
        }).encode()
        mock_urlopen.return_value = token_resp

        result = client_mod.remote_auth()
        assert result is True
        mock_save.assert_called_once()

    @patch("terminal_ify.client.fetch_config", side_effect=URLError("no network"))
    @patch("builtins.print")
    def test_remote_auth_config_failure(self, mock_print, mock_config):
        result = client_mod.remote_auth()
        assert result is False

    @patch("terminal_ify.client.urlopen", side_effect=URLError("timeout"))
    @patch("terminal_ify.client.webbrowser.open", return_value=False)
    @patch("terminal_ify.client.fetch_config")
    @patch("terminal_ify.client.time.sleep")
    @patch("builtins.print")
    def test_remote_auth_browser_not_opened(self, mock_print, mock_sleep, mock_config, mock_browser, mock_urlopen):
        mock_config.return_value = {
            "client_id": "cid",
            "redirect_uri": "https://example.com/cb",
            "scope": "user-read-playback-state",
        }

        result = client_mod.remote_auth()
        assert result is False
        # Should have printed the URL for manual opening
        print_args = [str(call) for call in mock_print.call_args_list]
        assert any("Open this URL" in arg or "Could not open browser" in arg for arg in print_args)

    @patch("terminal_ify.client.urlopen")
    @patch("terminal_ify.client.webbrowser.open", return_value=True)
    @patch("terminal_ify.client.fetch_config")
    @patch("terminal_ify.client.time.sleep")
    @patch("builtins.print")
    def test_remote_auth_timeout(self, mock_print, mock_sleep, mock_config, mock_browser, mock_urlopen):
        mock_config.return_value = {
            "client_id": "cid",
            "redirect_uri": "https://example.com/cb",
            "scope": "user-read-playback-state",
        }
        # All polling attempts fail
        mock_urlopen.side_effect = URLError("not ready")

        result = client_mod.remote_auth()
        assert result is False

    @patch("terminal_ify.client.urlopen")
    @patch("terminal_ify.client.webbrowser.open", return_value=True)
    @patch("terminal_ify.client.fetch_config")
    @patch("terminal_ify.client.time.sleep")
    @patch("builtins.print")
    def test_remote_auth_skips_response_without_access_token(self, mock_print, mock_sleep, mock_config, mock_browser, mock_urlopen):
        mock_config.return_value = {
            "client_id": "cid",
            "redirect_uri": "https://example.com/cb",
            "scope": "user-read-playback-state",
        }
        # Response without access_token should be skipped
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = json.dumps({"error": "pending"}).encode()
        mock_urlopen.return_value = resp

        result = client_mod.remote_auth()
        assert result is False  # All 60 attempts return no access_token


# ---------------------------------------------------------------------------
# ensure_valid_token edge cases
# ---------------------------------------------------------------------------


class TestEnsureValidTokenEdgeCases:
    @patch("terminal_ify.client.save_token")
    @patch("terminal_ify.client.refresh_token_remote")
    @patch("terminal_ify.client.load_cached_token")
    def test_refresh_failure_triggers_reauth_if_tty(self, mock_load, mock_refresh, mock_save, expired_token):
        mock_load.return_value = expired_token
        mock_refresh.return_value = None  # refresh fails

        with patch("sys.stdout") as mock_stdout, \
             patch("terminal_ify.client.remote_auth", return_value=False) as mock_auth:
            mock_stdout.isatty.return_value = True
            result = ensure_valid_token()
            mock_auth.assert_called_once()

    @patch("terminal_ify.client.load_cached_token")
    def test_token_without_access_token_triggers_auth(self, mock_load):
        mock_load.return_value = {"refresh_token": "rt", "expires_at": 0}

        with patch("sys.stdout") as mock_stdout, \
             patch("terminal_ify.client.remote_auth", return_value=False):
            mock_stdout.isatty.return_value = True
            result = ensure_valid_token()
            assert result is None

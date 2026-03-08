"""Shared fixtures for terminal-ify tests."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_token():
    """Return a valid-looking token dict."""
    return {
        "access_token": "fake-access-token-123",
        "refresh_token": "fake-refresh-token-456",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "scope": "user-read-playback-state user-modify-playback-state",
    }


@pytest.fixture
def expired_token(mock_token):
    """Return a token that is expired."""
    return {**mock_token, "expires_at": int(time.time()) - 100}


@pytest.fixture
def mock_spotify():
    """Return a MagicMock standing in for spotipy.Spotify."""
    sp = MagicMock()
    sp.current_playback.return_value = None
    sp.devices.return_value = {"devices": []}
    sp.current_user_playlists.return_value = {"items": []}
    sp.current_user_saved_tracks.return_value = {"items": []}
    sp.search.return_value = {}
    return sp


@pytest.fixture
def sample_playback():
    """Return a realistic playback response dict."""
    return {
        "is_playing": True,
        "progress_ms": 60000,
        "shuffle_state": False,
        "repeat_state": "off",
        "device": {
            "id": "device-123",
            "name": "My Speaker",
            "type": "Speaker",
            "volume_percent": 75,
            "is_active": True,
        },
        "item": {
            "name": "Test Song",
            "uri": "spotify:track:abc123",
            "duration_ms": 240000,
            "artists": [
                {"name": "Artist One"},
                {"name": "Artist Two"},
            ],
            "album": {
                "name": "Test Album",
            },
        },
    }


@pytest.fixture
def sample_playlists():
    """Return a list of playlist dicts."""
    return [
        {
            "id": "playlist-1",
            "name": "My Playlist",
            "tracks": {"total": 25},
        },
        {
            "id": "playlist-2",
            "name": "Chill Vibes",
            "tracks": {"total": 100},
        },
    ]


@pytest.fixture
def sample_playlist_tracks():
    """Return playlist track items."""
    return [
        {
            "track": {
                "name": "Track One",
                "uri": "spotify:track:t1",
                "duration_ms": 180000,
                "artists": [{"name": "Artist A"}],
            }
        },
        {
            "track": {
                "name": "Track Two",
                "uri": "spotify:track:t2",
                "duration_ms": 210000,
                "artists": [{"name": "Artist B"}, {"name": "Artist C"}],
            }
        },
    ]


@pytest.fixture
def sample_search_results():
    """Return a search response dict."""
    return {
        "tracks": {
            "items": [
                {
                    "name": "Found Track",
                    "uri": "spotify:track:ft1",
                    "duration_ms": 195000,
                    "artists": [{"name": "Search Artist"}],
                }
            ]
        },
        "albums": {
            "items": [
                {
                    "name": "Found Album",
                    "uri": "spotify:album:fa1",
                    "release_date": "2023-06-15",
                    "artists": [{"name": "Album Artist"}],
                }
            ]
        },
        "artists": {
            "items": [
                {
                    "name": "Found Artist",
                    "uri": "spotify:artist:far1",
                    "followers": {"total": 1234567},
                }
            ]
        },
    }

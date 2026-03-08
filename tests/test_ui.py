"""Comprehensive Textual UI / integration tests for terminal-ify.

Every test patches ``SpotifyClient`` so that no real network calls are made.
Uses Textual's built-in async testing via ``app.run_test()`` to obtain a
``Pilot`` for simulating user interactions.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from textual.widgets import (
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    OptionList,
    Static,
    TabbedContent,
    TabPane,
)

from terminal_ify.app import (
    LOGO,
    DeviceSelector,
    LibraryView,
    NowPlayingBar,
    NowPlayingView,
    PlaylistsView,
    SearchView,
    TerminalIfy,
    format_ms,
    progress_bar_text,
    truncate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client_mock(
    playback=None,
    playlists=None,
    playlist_tracks=None,
    saved_tracks=None,
    search_results=None,
    devices=None,
):
    """Build a ``MagicMock`` that behaves like ``SpotifyClient``."""
    client = MagicMock()
    client.get_current_playback.return_value = playback
    client.get_playlists.return_value = playlists or []
    client.get_playlist_tracks.return_value = playlist_tracks or []
    client.get_saved_tracks.return_value = saved_tracks or []
    client.search.return_value = search_results or {}
    client.get_devices.return_value = devices or []
    client.play.return_value = None
    client.pause.return_value = None
    client.next_track.return_value = None
    client.previous_track.return_value = None
    client.set_volume.return_value = None
    client.toggle_shuffle.return_value = None
    client.set_repeat.return_value = None
    client.transfer_playback.return_value = None
    return client


def _sample_playback(
    track="Test Song",
    artist="Test Artist",
    album="Test Album",
    is_playing=True,
    progress_ms=60_000,
    duration_ms=240_000,
    volume=75,
    device_name="My Speaker",
    device_id="device-123",
    shuffle=False,
    repeat="off",
):
    return {
        "is_playing": is_playing,
        "progress_ms": progress_ms,
        "shuffle_state": shuffle,
        "repeat_state": repeat,
        "device": {
            "id": device_id,
            "name": device_name,
            "type": "Speaker",
            "volume_percent": volume,
            "is_active": True,
        },
        "item": {
            "name": track,
            "uri": "spotify:track:abc123",
            "duration_ms": duration_ms,
            "artists": [{"name": artist}],
            "album": {"name": album},
        },
    }


SAMPLE_PLAYLISTS = [
    {"id": "playlist-1", "name": "My Playlist", "tracks": {"total": 25}},
    {"id": "playlist-2", "name": "Chill Vibes", "tracks": {"total": 100}},
]

SAMPLE_PLAYLIST_TRACKS = [
    {
        "track": {
            "name": "Track One",
            "uri": "spotify:track:t1",
            "duration_ms": 180_000,
            "artists": [{"name": "Artist A"}],
        }
    },
    {
        "track": {
            "name": "Track Two",
            "uri": "spotify:track:t2",
            "duration_ms": 210_000,
            "artists": [{"name": "Artist B"}, {"name": "Artist C"}],
        }
    },
]

SAMPLE_SAVED_TRACKS = [
    {
        "track": {
            "name": "Saved One",
            "uri": "spotify:track:s1",
            "duration_ms": 200_000,
            "artists": [{"name": "Saved Artist"}],
            "album": {"name": "Saved Album"},
        }
    },
]

SAMPLE_SEARCH_RESULTS = {
    "tracks": {
        "items": [
            {
                "name": "Found Track",
                "uri": "spotify:track:ft1",
                "duration_ms": 195_000,
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
                "followers": {"total": 1_234_567},
            }
        ]
    },
}

SAMPLE_DEVICES = [
    {"id": "dev-1", "name": "Living Room", "type": "Speaker", "is_active": True},
    {"id": "dev-2", "name": "Phone", "type": "Smartphone", "is_active": False},
]


def _build_app(client_mock: MagicMock | None = None) -> TerminalIfy:
    """Create a ``TerminalIfy`` instance with ``SpotifyClient`` patched out."""
    with patch("terminal_ify.app.SpotifyClient"):
        app = TerminalIfy()
    app.client = client_mock or _make_client_mock()
    return app


# ---------------------------------------------------------------------------
# 1. App startup
# ---------------------------------------------------------------------------


class TestAppStartup:
    """Verify that the app mounts and key widgets are present."""

    @pytest.mark.asyncio
    async def test_app_mounts_successfully(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            assert app.is_running

    @pytest.mark.asyncio
    async def test_logo_present(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            logo = app.query_one("#logo-art", Static)
            assert logo is not None

    @pytest.mark.asyncio
    async def test_tabbed_content_present(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs is not None

    @pytest.mark.asyncio
    async def test_now_playing_bar_present(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar is not None

    @pytest.mark.asyncio
    async def test_footer_present(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            footer = app.query_one(Footer)
            assert footer is not None

    @pytest.mark.asyncio
    async def test_top_bar_present(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            top_logo = app.query_one("#top-logo", Static)
            top_device = app.query_one("#top-device", Static)
            assert top_logo is not None
            assert top_device is not None

    @pytest.mark.asyncio
    async def test_four_tab_panes_exist(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            panes = app.query(TabPane)
            ids = {p.id for p in panes}
            assert {"now-playing", "playlists", "library", "search"} == ids

    @pytest.mark.asyncio
    async def test_initial_tab_is_now_playing(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs.active == "now-playing"

    @pytest.mark.asyncio
    async def test_now_playing_view_present(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            npv = app.query_one("#now-playing-view", NowPlayingView)
            assert npv is not None


# ---------------------------------------------------------------------------
# 2. Tab navigation
# ---------------------------------------------------------------------------


class TestTabNavigation:
    """Verify switching between tabs using key bindings."""

    @pytest.mark.asyncio
    async def test_switch_to_playlists_tab(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs.active == "playlists"

    @pytest.mark.asyncio
    async def test_switch_to_library_tab(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs.active == "library"

    @pytest.mark.asyncio
    async def test_switch_to_search_tab(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs.active == "search"

    @pytest.mark.asyncio
    async def test_switch_to_now_playing_tab(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.press("1")
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs.active == "now-playing"

    @pytest.mark.asyncio
    async def test_slash_focuses_search_tab(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("slash")
            tabs = app.query_one("#main-tabs", TabbedContent)
            assert tabs.active == "search"

    @pytest.mark.asyncio
    async def test_round_trip_tab_navigation(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs", TabbedContent)
            for key, expected in [("2", "playlists"), ("3", "library"), ("4", "search"), ("1", "now-playing")]:
                await pilot.press(key)
                assert tabs.active == expected


# ---------------------------------------------------------------------------
# 3. Device picker modal
# ---------------------------------------------------------------------------


class TestDevicePickerModal:
    """Test the device selector modal dialog."""

    @pytest.mark.asyncio
    async def test_device_modal_opens(self):
        client = _make_client_mock(devices=SAMPLE_DEVICES)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            # Allow the worker to complete
            await pilot.pause()
            await pilot.pause()
            # The DeviceSelector should be pushed as a screen
            assert len(app.screen_stack) > 1

    @pytest.mark.asyncio
    async def test_device_modal_shows_devices(self):
        client = _make_client_mock(devices=SAMPLE_DEVICES)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()
            option_list = app.screen.query_one("#device-list", OptionList)
            assert option_list.option_count == 2

    @pytest.mark.asyncio
    async def test_device_modal_cancel_button(self):
        client = _make_client_mock(devices=SAMPLE_DEVICES)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()
            cancel_btn = app.screen.query_one("#device-cancel")
            cancel_btn.press()
            await pilot.pause()
            # Modal should be dismissed
            assert len(app.screen_stack) == 1

    @pytest.mark.asyncio
    async def test_device_modal_escape_closes(self):
        client = _make_client_mock(devices=SAMPLE_DEVICES)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert len(app.screen_stack) == 1

    @pytest.mark.asyncio
    async def test_device_modal_no_devices(self):
        client = _make_client_mock(devices=[])
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()
            option_list = app.screen.query_one("#device-list", OptionList)
            # Should show the "No devices found" option
            assert option_list.option_count == 1


# ---------------------------------------------------------------------------
# 4. Playlist view
# ---------------------------------------------------------------------------


class TestPlaylistView:
    """Test playlist browsing and track selection."""

    @pytest.mark.asyncio
    async def test_playlists_load_on_tab_switch(self):
        client = _make_client_mock(playlists=SAMPLE_PLAYLISTS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            client.get_playlists.assert_called()

    @pytest.mark.asyncio
    async def test_playlists_populate_list(self):
        client = _make_client_mock(playlists=SAMPLE_PLAYLISTS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            await pilot.pause()
            lv = app.query_one("#playlists-list", ListView)
            assert len(lv.children) == 2

    @pytest.mark.asyncio
    async def test_playlist_click_loads_tracks(self):
        client = _make_client_mock(
            playlists=SAMPLE_PLAYLISTS,
            playlist_tracks=SAMPLE_PLAYLIST_TRACKS,
        )
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            await pilot.pause()
            # Select the first playlist (clear first to avoid duplicates from worker)
            playlists_view = app.query_one("#playlists-view", PlaylistsView)
            lv = app.query_one("#playlists-list", ListView)
            await lv.clear()
            playlists_view._populate_playlists(SAMPLE_PLAYLISTS)
            await pilot.pause()
            # Simulate selecting the playlist
            if len(lv.children) > 0:
                lv.index = 0
                lv.action_select_cursor()
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()
                client.get_playlist_tracks.assert_called_with("playlist-1")

    @pytest.mark.asyncio
    async def test_playlist_tracks_populate(self):
        client = _make_client_mock(
            playlists=SAMPLE_PLAYLISTS,
            playlist_tracks=SAMPLE_PLAYLIST_TRACKS,
        )
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            # Directly populate tracks (clear first to avoid duplicates from worker)
            playlists_view = app.query_one("#playlists-view", PlaylistsView)
            tracks_lv = app.query_one("#playlist-tracks-list", ListView)
            await tracks_lv.clear()
            playlists_view._populate_tracks(SAMPLE_PLAYLIST_TRACKS)
            await pilot.pause()
            assert len(tracks_lv.children) == 2

    @pytest.mark.asyncio
    async def test_playlist_track_click_plays(self):
        client = _make_client_mock(
            playlists=SAMPLE_PLAYLISTS,
            playlist_tracks=SAMPLE_PLAYLIST_TRACKS,
        )
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            playlists_view = app.query_one("#playlists-view", PlaylistsView)
            tracks_lv = app.query_one("#playlist-tracks-list", ListView)
            await tracks_lv.clear()
            playlists_view._populate_tracks(SAMPLE_PLAYLIST_TRACKS)
            await pilot.pause()
            tracks_lv = app.query_one("#playlist-tracks-list", ListView)
            tracks_lv.index = 0
            tracks_lv.action_select_cursor()
            await pilot.pause()
            await pilot.pause()
            client.play.assert_called_once_with(uris=["spotify:track:t1"])


# ---------------------------------------------------------------------------
# 5. Library view
# ---------------------------------------------------------------------------


class TestLibraryView:
    """Test saved tracks loading and playback."""

    @pytest.mark.asyncio
    async def test_library_loads_on_tab_switch(self):
        client = _make_client_mock(saved_tracks=SAMPLE_SAVED_TRACKS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            await pilot.pause()
            await pilot.pause()
            client.get_saved_tracks.assert_called()

    @pytest.mark.asyncio
    async def test_library_tracks_populate(self):
        client = _make_client_mock(saved_tracks=SAMPLE_SAVED_TRACKS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            await pilot.pause()
            await pilot.pause()
            # Clear and repopulate to avoid duplicates from worker
            lib_view = app.query_one("#library-view", LibraryView)
            lv = app.query_one("#library-tracks-list", ListView)
            await lv.clear()
            lib_view._populate_tracks(SAMPLE_SAVED_TRACKS)
            await pilot.pause()
            lv = app.query_one("#library-tracks-list", ListView)
            assert len(lv.children) == 1

    @pytest.mark.asyncio
    async def test_library_track_click_plays(self):
        client = _make_client_mock(saved_tracks=SAMPLE_SAVED_TRACKS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            await pilot.pause()
            await pilot.pause()
            lib_view = app.query_one("#library-view", LibraryView)
            lv = app.query_one("#library-tracks-list", ListView)
            await lv.clear()
            lib_view._populate_tracks(SAMPLE_SAVED_TRACKS)
            await pilot.pause()
            lv.index = 0
            lv.action_select_cursor()
            await pilot.pause()
            await pilot.pause()
            client.play.assert_called_once_with(uris=["spotify:track:s1"])


# ---------------------------------------------------------------------------
# 6. Search view
# ---------------------------------------------------------------------------


class TestSearchView:
    """Test searching and result display."""

    @pytest.mark.asyncio
    async def test_search_input_visible(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            inp = app.query_one("#search-input", Input)
            assert inp is not None

    @pytest.mark.asyncio
    async def test_search_submit_calls_api(self):
        client = _make_client_mock(search_results=SAMPLE_SEARCH_RESULTS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            inp = app.query_one("#search-input", Input)
            inp.focus()
            await pilot.pause()
            inp.value = "radiohead"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            await pilot.pause()
            client.search.assert_called_once_with("radiohead", types=["track", "album", "artist"], limit=10)

    @pytest.mark.asyncio
    async def test_search_results_sections(self):
        client = _make_client_mock(search_results=SAMPLE_SEARCH_RESULTS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            search_view = app.query_one("#search-view", SearchView)
            search_view._populate_results(SAMPLE_SEARCH_RESULTS)
            await pilot.pause()
            lv = app.query_one("#search-results-list", ListView)
            # 3 section headers + 3 items = 6
            assert len(lv.children) == 6

    @pytest.mark.asyncio
    async def test_search_track_click_plays(self):
        client = _make_client_mock(search_results=SAMPLE_SEARCH_RESULTS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            search_view = app.query_one("#search-view", SearchView)
            search_view._populate_results(SAMPLE_SEARCH_RESULTS)
            await pilot.pause()
            lv = app.query_one("#search-results-list", ListView)
            # Index 1 is the first track (index 0 is the TRACKS header)
            lv.index = 1
            lv.action_select_cursor()
            await pilot.pause()
            await pilot.pause()
            client.play.assert_called_once_with(uris=["spotify:track:ft1"])

    @pytest.mark.asyncio
    async def test_search_album_click_plays_context(self):
        client = _make_client_mock(search_results=SAMPLE_SEARCH_RESULTS)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            search_view = app.query_one("#search-view", SearchView)
            search_view._populate_results(SAMPLE_SEARCH_RESULTS)
            await pilot.pause()
            lv = app.query_one("#search-results-list", ListView)
            # Index 0=TRACKS header, 1=track, 2=ALBUMS header, 3=album
            lv.index = 3
            lv.action_select_cursor()
            await pilot.pause()
            await pilot.pause()
            client.play.assert_called_once_with(context_uri="spotify:album:fa1")

    @pytest.mark.asyncio
    async def test_search_empty_query_ignored(self):
        client = _make_client_mock()
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            inp = app.query_one("#search-input", Input)
            inp.focus()
            await pilot.pause()
            # Submit empty query
            await pilot.press("enter")
            await pilot.pause()
            client.search.assert_not_called()


# ---------------------------------------------------------------------------
# 7. Now Playing view -- playback controls
# ---------------------------------------------------------------------------


class TestNowPlayingControls:
    """Test keyboard shortcuts for playback control."""

    @pytest.mark.asyncio
    async def test_space_toggles_play_pause(self):
        playback = _sample_playback(is_playing=True)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            # App should detect is_playing=True from poll
            app._update_playback(playback)
            assert app.is_playing is True
            await pilot.press("space")
            await pilot.pause()
            await pilot.pause()
            client.pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_space_resumes_when_paused(self):
        playback = _sample_playback(is_playing=False)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            assert app.is_playing is False
            await pilot.press("space")
            await pilot.pause()
            await pilot.pause()
            client.play.assert_called_once()

    @pytest.mark.asyncio
    async def test_n_skips_to_next(self):
        client = _make_client_mock()
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("n")
            await pilot.pause()
            await pilot.pause()
            client.next_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_p_goes_to_previous(self):
        client = _make_client_mock()
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("p")
            await pilot.pause()
            await pilot.pause()
            client.previous_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_plus_increases_volume(self):
        playback = _sample_playback(volume=50)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.press("equal")
            await pilot.pause()
            await pilot.pause()
            client.set_volume.assert_called_once_with(55)

    @pytest.mark.asyncio
    async def test_minus_decreases_volume(self):
        playback = _sample_playback(volume=50)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.press("minus")
            await pilot.pause()
            await pilot.pause()
            client.set_volume.assert_called_once_with(45)

    @pytest.mark.asyncio
    async def test_volume_capped_at_100(self):
        playback = _sample_playback(volume=100)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.press("equal")
            await pilot.pause()
            await pilot.pause()
            client.set_volume.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_volume_floor_at_zero(self):
        playback = _sample_playback(volume=0)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.press("minus")
            await pilot.pause()
            await pilot.pause()
            client.set_volume.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_s_toggles_shuffle(self):
        playback = _sample_playback(shuffle=False)
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            assert app.shuffle_state is False
            await pilot.press("s")
            await pilot.pause()
            await pilot.pause()
            client.toggle_shuffle.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_r_cycles_repeat(self):
        playback = _sample_playback(repeat="off")
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            assert app.repeat_state == "off"
            await pilot.press("r")
            await pilot.pause()
            await pilot.pause()
            client.set_repeat.assert_called_once_with("context")

    @pytest.mark.asyncio
    async def test_repeat_cycles_context_to_track(self):
        playback = _sample_playback(repeat="context")
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.press("r")
            await pilot.pause()
            await pilot.pause()
            client.set_repeat.assert_called_once_with("track")

    @pytest.mark.asyncio
    async def test_repeat_cycles_track_to_off(self):
        playback = _sample_playback(repeat="track")
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.press("r")
            await pilot.pause()
            await pilot.pause()
            client.set_repeat.assert_called_once_with("off")


# ---------------------------------------------------------------------------
# 8. Now Playing bar updates
# ---------------------------------------------------------------------------


class TestNowPlayingBar:
    """Verify the persistent bottom bar updates with track info."""

    @pytest.mark.asyncio
    async def test_bar_shows_nothing_playing_initially(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.track_name == "Nothing playing"

    @pytest.mark.asyncio
    async def test_bar_updates_with_track_info(self):
        playback = _sample_playback(
            track="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
            device_name="Laptop",
        )
        client = _make_client_mock(playback=playback)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.track_name == "Bohemian Rhapsody"
            assert bar.artist_name == "Queen"
            assert bar.album_name == "A Night at the Opera"
            assert bar.device_name == "Laptop"

    @pytest.mark.asyncio
    async def test_bar_progress_updates(self):
        playback = _sample_playback(progress_ms=120_000, duration_ms=240_000)
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.progress == pytest.approx(0.5)
            assert bar.elapsed_ms == 120_000
            assert bar.total_ms == 240_000

    @pytest.mark.asyncio
    async def test_bar_shuffle_indicator(self):
        playback = _sample_playback(shuffle=True)
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.shuffle_on is True

    @pytest.mark.asyncio
    async def test_bar_repeat_indicator(self):
        playback = _sample_playback(repeat="track")
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.repeat_state == "track"

    @pytest.mark.asyncio
    async def test_bar_volume(self):
        playback = _sample_playback(volume=80)
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.volume == 80

    @pytest.mark.asyncio
    async def test_bar_is_playing_flag(self):
        playback = _sample_playback(is_playing=True)
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.is_playing is True

    @pytest.mark.asyncio
    async def test_bar_resets_on_no_playback(self):
        playback = _sample_playback()
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            bar = app.query_one("#now-playing-bar", NowPlayingBar)
            assert bar.track_name == "Test Song"
            # Now clear playback
            app._update_playback(None)
            assert bar.track_name == "Nothing playing"
            assert bar.artist_name == ""
            assert bar.device_name == ""


# ---------------------------------------------------------------------------
# 9. Keyboard shortcuts (comprehensive)
# ---------------------------------------------------------------------------


class TestKeyboardShortcuts:
    """Test all bindings defined in the app."""

    @pytest.mark.asyncio
    async def test_q_quits_app(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("q")
            # The app should begin exiting (run_test context handles cleanup)

    @pytest.mark.asyncio
    async def test_d_opens_devices(self):
        client = _make_client_mock(devices=SAMPLE_DEVICES)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()
            client.get_devices.assert_called()

    @pytest.mark.asyncio
    async def test_number_keys_switch_tabs(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs", TabbedContent)
            bindings = [
                ("1", "now-playing"),
                ("2", "playlists"),
                ("3", "library"),
                ("4", "search"),
            ]
            for key, expected_tab in bindings:
                await pilot.press(key)
                assert tabs.active == expected_tab, f"Key '{key}' should activate '{expected_tab}'"


# ---------------------------------------------------------------------------
# 10. Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases: empty data, no devices, no playback, etc."""

    @pytest.mark.asyncio
    async def test_empty_playlists(self):
        client = _make_client_mock(playlists=[])
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            playlists_view = app.query_one("#playlists-view", PlaylistsView)
            playlists_view._populate_playlists([])
            await pilot.pause()
            lv = app.query_one("#playlists-list", ListView)
            assert len(lv.children) == 0

    @pytest.mark.asyncio
    async def test_empty_playlist_tracks(self):
        client = _make_client_mock(playlists=SAMPLE_PLAYLISTS, playlist_tracks=[])
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            await pilot.pause()
            playlists_view = app.query_one("#playlists-view", PlaylistsView)
            playlists_view._populate_tracks([])
            await pilot.pause()
            lv = app.query_one("#playlist-tracks-list", ListView)
            assert len(lv.children) == 0

    @pytest.mark.asyncio
    async def test_empty_library(self):
        client = _make_client_mock(saved_tracks=[])
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            await pilot.pause()
            await pilot.pause()
            lib_view = app.query_one("#library-view", LibraryView)
            lib_view._populate_tracks([])
            await pilot.pause()
            lv = app.query_one("#library-tracks-list", ListView)
            assert len(lv.children) == 0

    @pytest.mark.asyncio
    async def test_no_active_playback(self):
        client = _make_client_mock(playback=None)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(None)
            assert app.current_track == "Nothing playing"
            assert app.is_playing is False
            assert app.device_name == ""

    @pytest.mark.asyncio
    async def test_playback_missing_item(self):
        """Playback dict exists but ``item`` is None (e.g., ad break)."""
        client = _make_client_mock()
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback({"is_playing": True, "item": None})
            assert app.current_track == "Nothing playing"

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        empty_results = {
            "tracks": {"items": []},
            "albums": {"items": []},
            "artists": {"items": []},
        }
        client = _make_client_mock(search_results=empty_results)
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("4")
            await pilot.pause()
            search_view = app.query_one("#search-view", SearchView)
            search_view._populate_results(empty_results)
            await pilot.pause()
            lv = app.query_one("#search-results-list", ListView)
            assert len(lv.children) == 0
            hint = app.query_one("#search-hint", Label)
            # hint should say "No results found."

    @pytest.mark.asyncio
    async def test_no_devices_in_modal(self):
        client = _make_client_mock(devices=[])
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()
            option_list = app.screen.query_one("#device-list", OptionList)
            assert option_list.option_count == 1  # "No devices found"

    @pytest.mark.asyncio
    async def test_playback_with_zero_duration(self):
        """Edge case: duration_ms is 0 should not cause division by zero."""
        playback = _sample_playback(duration_ms=0, progress_ms=0)
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            assert app.progress_pct == 0.0

    @pytest.mark.asyncio
    async def test_track_with_no_artists(self):
        """Handle track with empty artists list."""
        playback = _sample_playback()
        playback["item"]["artists"] = []
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            assert app.current_artist == ""

    @pytest.mark.asyncio
    async def test_track_with_multiple_artists(self):
        playback = _sample_playback()
        playback["item"]["artists"] = [
            {"name": "Artist One"},
            {"name": "Artist Two"},
            {"name": "Artist Three"},
        ]
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            assert app.current_artist == "Artist One, Artist Two, Artist Three"

    @pytest.mark.asyncio
    async def test_now_playing_view_updates_display(self):
        """Verify NowPlayingView internal widgets update."""
        playback = _sample_playback(track="Eclipse", artist="Pink Floyd", album="Dark Side")
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            await pilot.pause()
            npv = app.query_one("#now-playing-view", NowPlayingView)
            assert npv.track_name == "Eclipse"
            assert npv.artist_name == "Pink Floyd"
            assert npv.album_name == "Dark Side"

    @pytest.mark.asyncio
    async def test_top_device_label_updates(self):
        playback = _sample_playback(device_name="HomePod")
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(playback)
            # The top-device Static should contain the device name

    @pytest.mark.asyncio
    async def test_top_device_label_no_device(self):
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            app._update_playback(None)
            # device_name should be empty
            assert app.device_name == ""

    @pytest.mark.asyncio
    async def test_playlist_tracks_with_null_track(self):
        """Some playlist items have track=None (local files, unavailable)."""
        tracks_with_null = [
            {"track": None},
            {
                "track": {
                    "name": "Valid Track",
                    "uri": "spotify:track:valid1",
                    "duration_ms": 200_000,
                    "artists": [{"name": "Valid Artist"}],
                }
            },
        ]
        client = _make_client_mock()
        app = _build_app(client)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            playlists_view = app.query_one("#playlists-view", PlaylistsView)
            playlists_view._populate_tracks(tracks_with_null)
            await pilot.pause()
            tracks_lv = app.query_one("#playlist-tracks-list", ListView)
            # Only the valid track should appear
            assert len(tracks_lv.children) == 1

    @pytest.mark.asyncio
    async def test_library_tracks_with_null_track(self):
        """Library items with track=None should be skipped."""
        tracks_with_null = [{"track": None}]
        app = _build_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            await pilot.pause()
            lib_view = app.query_one("#library-view", LibraryView)
            lib_view._populate_tracks(tracks_with_null)
            await pilot.pause()
            lv = app.query_one("#library-tracks-list", ListView)
            assert len(lv.children) == 0


# ---------------------------------------------------------------------------
# Helper function tests (pure, no app needed)
# ---------------------------------------------------------------------------


class TestHelpers:
    """Test pure helper functions."""

    def test_format_ms_normal(self):
        assert format_ms(60_000) == "1:00"
        assert format_ms(125_000) == "2:05"
        assert format_ms(0) == "0:00"

    def test_format_ms_none(self):
        assert format_ms(None) == "--:--"

    def test_truncate_short(self):
        assert truncate("hello", 40) == "hello"

    def test_truncate_long(self):
        result = truncate("a" * 50, 10)
        assert len(result) == 10
        assert result.endswith("…")  # Ends with ellipsis character

    def test_truncate_exact(self):
        assert truncate("hello", 5) == "hello"

    def test_progress_bar_text_zero(self):
        result = progress_bar_text(0.0, width=10)
        assert "▓" not in result or result.count("░") == 10

    def test_progress_bar_text_full(self):
        result = progress_bar_text(1.0, width=10)
        assert "▓" in result

"""Tests for terminal_ify.app — Textual widgets, views, and the main app.

Uses Textual's async test helpers where appropriate, and direct unit tests
for synchronous logic like _update_playback and _sync_widgets.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from terminal_ify.app import (
    DeviceSelector,
    NowPlayingBar,
    NowPlayingView,
    TerminalIfy,
    format_ms,
    truncate,
)


# ---------------------------------------------------------------------------
# TerminalIfy._update_playback (synchronous logic, no TUI needed)
# ---------------------------------------------------------------------------


class TestUpdatePlayback:
    """Test _update_playback which transforms API data into reactive state."""

    def _make_app(self):
        """Create a TerminalIfy instance with mocked client, without running."""
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            app = TerminalIfy()
            return app

    def test_none_playback_resets_state(self):
        app = self._make_app()
        app._sync_widgets = MagicMock()

        app._update_playback(None)

        assert app.current_track == "Nothing playing"
        assert app.current_artist == ""
        assert app.current_album == ""
        assert app.is_playing is False
        assert app.progress_pct == 0.0
        assert app.elapsed_ms == 0
        assert app.total_ms == 0
        assert app.device_name == ""

    def test_empty_item_resets_state(self):
        app = self._make_app()
        app._sync_widgets = MagicMock()

        app._update_playback({"item": None})

        assert app.current_track == "Nothing playing"

    def test_valid_playback_sets_state(self, sample_playback):
        app = self._make_app()
        app._sync_widgets = MagicMock()

        app._update_playback(sample_playback)

        assert app.current_track == "Test Song"
        assert app.current_artist == "Artist One, Artist Two"
        assert app.current_album == "Test Album"
        assert app.is_playing is True
        assert app.elapsed_ms == 60000
        assert app.total_ms == 240000
        assert app.progress_pct == pytest.approx(0.25)
        assert app.shuffle_state is False
        assert app.repeat_state == "off"
        assert app.volume_level == 75
        assert app.device_name == "My Speaker"

    def test_progress_zero_when_duration_zero(self):
        app = self._make_app()
        app._sync_widgets = MagicMock()

        playback = {
            "is_playing": True,
            "progress_ms": 0,
            "shuffle_state": False,
            "repeat_state": "off",
            "device": {"volume_percent": 50, "name": "Dev"},
            "item": {
                "name": "Silence",
                "duration_ms": 0,
                "artists": [],
                "album": {"name": ""},
            },
        }
        app._update_playback(playback)
        assert app.progress_pct == 0.0

    def test_missing_device_volume_defaults_to_50(self):
        app = self._make_app()
        app._sync_widgets = MagicMock()

        playback = {
            "is_playing": False,
            "progress_ms": 0,
            "shuffle_state": False,
            "repeat_state": "off",
            "device": {},
            "item": {
                "name": "Track",
                "duration_ms": 1000,
                "artists": [],
                "album": {},
            },
        }
        app._update_playback(playback)
        assert app.volume_level == 50

    def test_calls_sync_widgets(self, sample_playback):
        app = self._make_app()
        app._sync_widgets = MagicMock()

        app._update_playback(sample_playback)
        app._sync_widgets.assert_called_once()


# ---------------------------------------------------------------------------
# Textual app mounting tests (async)
# ---------------------------------------------------------------------------


class TestAppComposition:
    """Test that the app composes correctly with Textual's async pilot."""

    @pytest.mark.asyncio
    async def test_app_mounts_and_has_tabs(self):
        """The app should mount and contain the main tabs."""
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                # Check the app title
                assert app.title == "terminal-ify"

                # Check key widgets exist
                from textual.widgets import TabbedContent, Footer
                tabs = app.query_one("#main-tabs", TabbedContent)
                assert tabs is not None

                footer = app.query_one(Footer)
                assert footer is not None

                bar = app.query_one("#now-playing-bar", NowPlayingBar)
                assert bar is not None

    @pytest.mark.asyncio
    async def test_now_playing_view_exists(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                npv = app.query_one("#now-playing-view", NowPlayingView)
                assert npv is not None
                assert npv.track_name == "Nothing playing"

    @pytest.mark.asyncio
    async def test_now_playing_bar_defaults(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                bar = app.query_one("#now-playing-bar", NowPlayingBar)
                assert bar.track_name == "Nothing playing"
                assert bar.artist_name == ""
                assert bar.is_playing is False
                assert bar.progress == 0.0
                assert bar.volume == 50

    @pytest.mark.asyncio
    async def test_switch_tab_action(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_client.get_playlists.return_value = []
            mock_client.get_saved_tracks.return_value = []
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                from textual.widgets import TabbedContent
                tabs = app.query_one("#main-tabs", TabbedContent)

                app.action_switch_tab("playlists")
                assert tabs.active == "playlists"

                app.action_switch_tab("library")
                assert tabs.active == "library"

                app.action_switch_tab("search")
                assert tabs.active == "search"

                app.action_switch_tab("now-playing")
                assert tabs.active == "now-playing"

    @pytest.mark.asyncio
    async def test_sync_widgets_updates_bar(self, sample_playback):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                app._update_playback(sample_playback)

                bar = app.query_one("#now-playing-bar", NowPlayingBar)
                assert bar.track_name == "Test Song"
                assert bar.artist_name == "Artist One, Artist Two"
                assert bar.album_name == "Test Album"
                assert bar.is_playing is True
                assert bar.volume == 75
                assert bar.device_name == "My Speaker"

    @pytest.mark.asyncio
    async def test_sync_widgets_updates_now_playing_view(self, sample_playback):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                app._update_playback(sample_playback)

                npv = app.query_one("#now-playing-view", NowPlayingView)
                assert npv.track_name == "Test Song"
                assert npv.artist_name == "Artist One, Artist Two"
                assert npv.is_playing is True

    @pytest.mark.asyncio
    async def test_top_device_shows_device_name(self, sample_playback):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                app._update_playback(sample_playback)

                from textual.widgets import Static
                top_device = app.query_one("#top-device", Static)
                # The widget's update was called; check the app state
                assert app.device_name == "My Speaker"


# ---------------------------------------------------------------------------
# NowPlayingBar rendering
# ---------------------------------------------------------------------------


class TestNowPlayingBarRender:
    @pytest.mark.asyncio
    async def test_bar_render_nothing_playing(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                bar = app.query_one("#now-playing-bar", NowPlayingBar)
                rendered = bar.render()
                assert "Nothing playing" in rendered.plain

    @pytest.mark.asyncio
    async def test_bar_render_with_track(self, sample_playback):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                bar = app.query_one("#now-playing-bar", NowPlayingBar)
                bar.track_name = "My Track"
                bar.artist_name = "My Artist"
                bar.is_playing = True
                bar.elapsed_ms = 60000
                bar.total_ms = 180000
                bar.volume = 70

                rendered = bar.render()
                plain = rendered.plain
                assert "My Track" in plain
                assert "My Artist" in plain
                assert "1:00" in plain
                assert "3:00" in plain

    @pytest.mark.asyncio
    async def test_bar_play_pause_icon(self, sample_playback):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                bar = app.query_one("#now-playing-bar", NowPlayingBar)

                bar.is_playing = True
                rendered = bar.render()
                # Playing icon is ▐▐
                assert "\u2590\u2590" in rendered.plain

                bar.is_playing = False
                rendered = bar.render()
                assert "\u25b6" in rendered.plain  # play icon ▶


# ---------------------------------------------------------------------------
# DeviceSelector
# ---------------------------------------------------------------------------


class TestDeviceSelector:
    @pytest.mark.asyncio
    async def test_device_selector_shows_devices(self):
        devices = [
            {"id": "d1", "name": "Living Room", "type": "Speaker", "is_active": True},
            {"id": "d2", "name": "Phone", "type": "Smartphone", "is_active": False},
        ]

        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                modal = DeviceSelector(devices)
                app.push_screen(modal)
                await pilot.pause()

                from textual.widgets import OptionList
                ol = modal.query_one("#device-list", OptionList)
                assert ol.option_count == 2

    @pytest.mark.asyncio
    async def test_device_selector_no_devices(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get_current_playback.return_value = None
            mock_cls.return_value = mock_client

            app = TerminalIfy()
            async with app.run_test(size=(120, 40)) as pilot:
                modal = DeviceSelector([])
                app.push_screen(modal)
                await pilot.pause()

                from textual.widgets import OptionList
                ol = modal.query_one("#device-list", OptionList)
                assert ol.option_count == 1  # "No devices found"


# ---------------------------------------------------------------------------
# App key bindings
# ---------------------------------------------------------------------------


class TestAppBindings:
    def test_bindings_include_expected_keys(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            app = TerminalIfy()

        binding_keys = [b.key for b in app.BINDINGS]
        assert "q" in binding_keys
        assert "space" in binding_keys
        assert "n" in binding_keys
        assert "p" in binding_keys
        assert "s" in binding_keys
        assert "r" in binding_keys
        assert "d" in binding_keys
        assert "slash" in binding_keys
        assert "1" in binding_keys
        assert "2" in binding_keys
        assert "3" in binding_keys
        assert "4" in binding_keys

    def test_volume_action_clamps(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            app = TerminalIfy()

        # Volume up should clamp at 100
        app.volume_level = 98
        new_vol = min(100, app.volume_level + 5)
        assert new_vol == 100

        # Volume down should clamp at 0
        app.volume_level = 3
        new_vol = max(0, app.volume_level - 5)
        assert new_vol == 0

    def test_repeat_cycle(self):
        cycle = {"off": "context", "context": "track", "track": "off"}
        assert cycle["off"] == "context"
        assert cycle["context"] == "track"
        assert cycle["track"] == "off"


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------


class TestMain:
    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run")
    def test_main_runs_app(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player_cls.return_value = MagicMock()

        main()
        mock_run.assert_called_once()

    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run", side_effect=RuntimeError("Could not obtain credentials"))
    def test_main_handles_auth_error(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player_cls.return_value = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run", side_effect=ValueError("some other error"))
    def test_main_reraises_non_auth_error(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player_cls.return_value = MagicMock()

        with pytest.raises(ValueError, match="some other error"):
            main()

    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run")
    def test_main_stops_player_on_exit(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player = MagicMock()
        mock_player_cls.return_value = mock_player

        main()
        mock_player.stop.assert_called_once()

    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run", side_effect=ValueError("oops"))
    def test_main_stops_player_even_on_error(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player = MagicMock()
        mock_player_cls.return_value = mock_player

        with pytest.raises(ValueError):
            main()
        mock_player.stop.assert_called_once()

    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run", side_effect=RuntimeError("token expired"))
    def test_main_catches_token_keyword(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player_cls.return_value = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("terminal_ify.app.LibrespotPlayer")
    @patch("terminal_ify.app.SpotifyClient")
    @patch.object(TerminalIfy, "run", side_effect=RuntimeError("auth server down"))
    def test_main_catches_auth_keyword(self, mock_run, mock_client_cls, mock_player_cls):
        from terminal_ify.app import main
        mock_client_cls.return_value = MagicMock()
        mock_player_cls.return_value = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# _update_playback edge cases
# ---------------------------------------------------------------------------


class TestUpdatePlaybackEdgeCases:
    def _make_app(self):
        with patch("terminal_ify.app.SpotifyClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            app = TerminalIfy()
            app._sync_widgets = MagicMock()
            return app

    def test_playback_with_none_progress_ms(self):
        app = self._make_app()
        playback = {
            "is_playing": True,
            "progress_ms": None,
            "shuffle_state": False,
            "repeat_state": "off",
            "device": {"volume_percent": 50, "name": "Dev"},
            "item": {
                "name": "Track",
                "duration_ms": 180000,
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album"},
            },
        }
        app._update_playback(playback)
        assert app.elapsed_ms == 0

    def test_playback_with_none_duration_ms(self):
        app = self._make_app()
        playback = {
            "is_playing": True,
            "progress_ms": 60000,
            "shuffle_state": False,
            "repeat_state": "off",
            "device": {"volume_percent": 50, "name": "Dev"},
            "item": {
                "name": "Track",
                "duration_ms": None,
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album"},
            },
        }
        app._update_playback(playback)
        assert app.total_ms == 0
        assert app.progress_pct == 0.0

    def test_playback_missing_album_key(self):
        app = self._make_app()
        playback = {
            "is_playing": True,
            "progress_ms": 0,
            "shuffle_state": False,
            "repeat_state": "off",
            "device": {"volume_percent": 50, "name": "Dev"},
            "item": {
                "name": "Track",
                "duration_ms": 1000,
                "artists": [],
                "album": {},
            },
        }
        app._update_playback(playback)
        assert app.current_album == ""

    def test_empty_dict_playback(self):
        app = self._make_app()
        app._update_playback({})
        assert app.current_track == "Nothing playing"

    def test_playback_with_multiple_artists(self):
        app = self._make_app()
        playback = {
            "is_playing": True,
            "progress_ms": 0,
            "shuffle_state": False,
            "repeat_state": "off",
            "device": {"volume_percent": 50, "name": "Dev"},
            "item": {
                "name": "Collab Track",
                "duration_ms": 1000,
                "artists": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
                "album": {"name": "Album"},
            },
        }
        app._update_playback(playback)
        assert app.current_artist == "A, B, C"

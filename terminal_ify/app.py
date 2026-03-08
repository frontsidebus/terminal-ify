"""terminal-ify: TUI application built with Textual."""

from __future__ import annotations

import sys
import time
from typing import ClassVar

from rich.markup import escape as esc
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
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
from textual.widgets.option_list import Option

from terminal_ify.client import SpotifyClient
from terminal_ify.player import LibrespotPlayer
from terminal_ify.themes import TERMINAL_IFY_CSS

# ---------------------------------------------------------------------------
# ASCII logo
# ---------------------------------------------------------------------------

LOGO = r"""
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗       ██╗███████╗██╗   ██╗
  ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║       ██║██╔════╝╚██╗ ██╔╝
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║  ███  ██║█████╗   ╚████╔╝
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║ ██╔██╗██║██╔══╝    ╚██╔╝
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╔╝████║██║        ██║
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═══╝╚═╝        ╚═╝
""".strip(
    "\n"
)

MINI_LOGO = "  [bold #1DB954]terminal[/][dim]-[/][bold white]ify[/]"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def format_ms(ms: int | None) -> str:
    """Convert milliseconds to mm:ss."""
    if ms is None:
        return "--:--"
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def progress_bar_text(progress: float, width: int = 30) -> str:
    """Return a text-based progress bar using block characters."""
    filled = int(progress * width)
    empty = width - filled
    return f"[#1DB954]{'▓' * filled}[/][dim]{'░' * empty}[/]"


def truncate(text: str, length: int = 40) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"


def uri_to_id(uri: str) -> str:
    return uri.replace(":", "-")


def id_to_uri(widget_id: str, prefix: str) -> str:
    rest = widget_id[len(prefix):]
    return rest.replace("-", ":", 2)


# ---------------------------------------------------------------------------
# Device selector modal
# ---------------------------------------------------------------------------


class DeviceSelector(ModalScreen[str | None]):
    """Modal screen to pick a playback device."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close"),
    ]

    def __init__(self, devices: list[dict]) -> None:
        super().__init__()
        self.devices = devices

    def compose(self) -> ComposeResult:
        with Vertical(id="device-modal"):
            yield Label("[bold #1DB954]Select a device[/]", id="device-title")
            option_items: list[Option] = []
            for dev in self.devices:
                icon = "🔊 " if dev.get("is_active") else "   "
                name = dev.get("name", "Unknown")
                dtype = dev.get("type", "")
                option_items.append(Option(f"{icon}{esc(name)}  [dim]({esc(dtype)})[/]", id=dev.get("id", "")))
            if not option_items:
                option_items.append(Option("[dim]No devices found[/]", id="__none__"))
            yield OptionList(*option_items, id="device-list")
            yield Button("Cancel", variant="default", id="device-cancel")

    @on(OptionList.OptionSelected, "#device-list")
    def on_device_selected(self, event: OptionList.OptionSelected) -> None:
        device_id = str(event.option.id)
        if device_id != "__none__":
            self.dismiss(device_id)
        else:
            self.dismiss(None)

    @on(Button.Pressed, "#device-cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Now-playing bar (always visible at the bottom)
# ---------------------------------------------------------------------------


class NowPlayingBar(Static):
    """Persistent playback bar that sits at the bottom of the screen."""

    track_name: reactive[str] = reactive("Nothing playing")
    artist_name: reactive[str] = reactive("")
    album_name: reactive[str] = reactive("")
    progress: reactive[float] = reactive(0.0)
    elapsed_ms: reactive[int] = reactive(0)
    total_ms: reactive[int] = reactive(0)
    is_playing: reactive[bool] = reactive(False)
    shuffle_on: reactive[bool] = reactive(False)
    repeat_state: reactive[str] = reactive("off")
    volume: reactive[int] = reactive(50)
    device_name: reactive[str] = reactive("")

    def render(self) -> Text:
        play_icon = "▐▐ " if self.is_playing else " ▶ "
        shuffle_indicator = "[#1DB954]⇄[/]" if self.shuffle_on else "[dim]⇄[/]"

        repeat_map = {"off": "[dim]⟳[/]", "context": "[#1DB954]⟳[/]", "track": "[#1DB954]⟳¹[/]"}
        repeat_indicator = repeat_map.get(self.repeat_state, "[dim]⟳[/]")

        vol_bars = self.volume // 10
        vol_display = f"[#1DB954]{'█' * vol_bars}[/][dim]{'░' * (10 - vol_bars)}[/]"

        elapsed_str = format_ms(self.elapsed_ms)
        total_str = format_ms(self.total_ms)
        bar = progress_bar_text(self.progress, width=30)

        track_display = f"[bold #1DB954]{esc(truncate(self.track_name, 35))}[/]" if self.track_name != "Nothing playing" else "[dim]Nothing playing[/]"
        artist_display = f"  [italic]{esc(truncate(self.artist_name, 25))}[/]" if self.artist_name else ""
        album_display = f"  [dim]{esc(truncate(self.album_name, 25))}[/]" if self.album_name else ""

        device_display = f"  [dim]on[/] [bold]{esc(self.device_name)}[/]" if self.device_name else ""

        line1 = f"  {play_icon} {track_display}{artist_display}{album_display}"
        line2 = f"    {elapsed_str} {bar} {total_str}   {shuffle_indicator}  {repeat_indicator}   🔊 {vol_display}  ({self.volume}%){device_display}"

        markup = f"{line1}\n{line2}"
        return Text.from_markup(markup)


# ---------------------------------------------------------------------------
# View: Now Playing (large)
# ---------------------------------------------------------------------------


class NowPlayingView(Static):
    """Full-screen now-playing display with large track info."""

    track_name: reactive[str] = reactive("Nothing playing")
    artist_name: reactive[str] = reactive("")
    album_name: reactive[str] = reactive("")
    is_playing: reactive[bool] = reactive(False)
    progress: reactive[float] = reactive(0.0)
    elapsed_ms: reactive[int] = reactive(0)
    total_ms: reactive[int] = reactive(0)
    shuffle_on: reactive[bool] = reactive(False)
    repeat_state: reactive[str] = reactive("off")

    def compose(self) -> ComposeResult:
        yield Static(LOGO, id="logo-art")
        yield Static("", id="np-track-info")
        yield Static("", id="np-progress-area")
        yield Static("", id="np-controls-area")

    def _update_display(self) -> None:
        try:
            track_info = self.query_one("#np-track-info", Static)
            progress_area = self.query_one("#np-progress-area", Static)
            controls_area = self.query_one("#np-controls-area", Static)
        except NoMatches:
            return

        if self.track_name == "Nothing playing":
            track_info.update(
                "\n\n[dim]No active playback detected.[/]\n"
                "[dim]Start playing something on Spotify and it will appear here.[/]\n"
                "[dim]Press [bold]/[/bold] to search, or [bold]2[/bold] to browse playlists.[/]"
            )
            progress_area.update("")
            controls_area.update("")
            return

        play_icon = " ▐▐  PLAYING" if self.is_playing else "  ▶  PAUSED"
        track_info.update(
            f"\n\n[bold #1DB954 on default]  ♫  {esc(self.track_name)}[/]\n"
            f"[italic]     {esc(self.artist_name)}[/]\n"
            f"[dim]     {esc(self.album_name)}[/]\n"
        )

        elapsed = format_ms(self.elapsed_ms)
        total = format_ms(self.total_ms)
        bar = progress_bar_text(self.progress, width=50)
        progress_area.update(f"\n     {elapsed}  {bar}  {total}\n")

        shuffle_indicator = "[#1DB954]SHUFFLE ON[/]" if self.shuffle_on else "[dim]SHUFFLE OFF[/]"
        repeat_labels = {"off": "[dim]REPEAT OFF[/]", "context": "[#1DB954]REPEAT ALL[/]", "track": "[#1DB954]REPEAT ONE[/]"}
        repeat_indicator = repeat_labels.get(self.repeat_state, "[dim]REPEAT OFF[/]")
        controls_area.update(
            f"     [bold]{play_icon}[/]      {shuffle_indicator}      {repeat_indicator}\n\n"
            f"     [dim]space[/] play/pause  [dim]n[/] next  [dim]p[/] prev  "
            f"[dim]+/-[/] volume  [dim]s[/] shuffle  [dim]r[/] repeat  [dim]d[/] devices"
        )

    def watch_track_name(self) -> None:
        self._update_display()

    def watch_is_playing(self) -> None:
        self._update_display()

    def watch_progress(self) -> None:
        self._update_display()

    def watch_shuffle_on(self) -> None:
        self._update_display()

    def watch_repeat_state(self) -> None:
        self._update_display()


# ---------------------------------------------------------------------------
# View: Playlists
# ---------------------------------------------------------------------------


class PlaylistsView(Static):
    """Browse user playlists and their tracks."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="playlists-layout"):
            with Vertical(id="playlists-sidebar"):
                yield Label("[bold #1DB954]Your Playlists[/]", id="playlists-header")
                yield ListView(id="playlists-list")
            with Vertical(id="playlists-detail"):
                yield Label("[dim]Select a playlist to see tracks[/]", id="playlist-detail-header")
                yield ListView(id="playlist-tracks-list")

    def on_mount(self) -> None:
        self.load_playlists()

    @work(thread=True)
    def load_playlists(self) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        playlists = app.client.get_playlists()
        self.app.call_from_thread(self._populate_playlists, playlists)

    def _populate_playlists(self, playlists: list) -> None:
        try:
            lv = self.query_one("#playlists-list", ListView)
        except NoMatches:
            return
        lv.clear()
        for pl in playlists:
            name = pl.get("name", "Unknown")
            total = pl.get("tracks", {}).get("total", 0)
            pl_id = pl.get("id", "")
            item = ListItem(
                Label(f"[bold]{esc(name)}[/]  [dim]({total} tracks)[/]"),
                id=f"pl-{pl_id}",
            )
            lv.append(item)

    @on(ListView.Selected, "#playlists-list")
    def on_playlist_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("pl-"):
            playlist_id = item_id[3:]
            self.load_playlist_tracks(playlist_id)

    @work(thread=True)
    def load_playlist_tracks(self, playlist_id: str) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        tracks = app.client.get_playlist_tracks(playlist_id)
        self.app.call_from_thread(self._populate_tracks, tracks)

    def _populate_tracks(self, tracks: list) -> None:
        try:
            lv = self.query_one("#playlist-tracks-list", ListView)
            header = self.query_one("#playlist-detail-header", Label)
        except NoMatches:
            return
        header.update(f"[bold #1DB954]Tracks[/]  [dim]({len(tracks)} total)[/]")
        lv.clear()
        for i, item in enumerate(tracks):
            track = item.get("track")
            if not track:
                continue
            name = track.get("name", "Unknown")
            artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
            duration = format_ms(track.get("duration_ms"))
            uri = track.get("uri", "")
            lv.append(
                ListItem(
                    Label(f"[bold]{i + 1:>3}.[/]  [#1DB954]{esc(truncate(name, 40))}[/]  [dim]{esc(truncate(artists, 30))}[/]  [dim]{duration}[/]"),
                    id=f"trk-{uri_to_id(uri)}",
                )
            )

    @on(ListView.Selected, "#playlist-tracks-list")
    def on_track_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("trk-"):
            uri = id_to_uri(item_id, "trk-")
            self.play_track(uri)

    @work(thread=True)
    def play_track(self, uri: str) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        app.client.play(uris=[uri])


# ---------------------------------------------------------------------------
# View: Library
# ---------------------------------------------------------------------------


class LibraryView(Static):
    """Browse saved tracks and albums."""

    def compose(self) -> ComposeResult:
        with Vertical(id="library-container"):
            yield Label("[bold #1DB954]Saved Tracks[/]", id="library-header")
            yield ListView(id="library-tracks-list")

    def on_mount(self) -> None:
        self.load_library()

    @work(thread=True)
    def load_library(self) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        tracks = app.client.get_saved_tracks(limit=50)
        self.app.call_from_thread(self._populate_tracks, tracks)

    def _populate_tracks(self, tracks: list) -> None:
        try:
            lv = self.query_one("#library-tracks-list", ListView)
        except NoMatches:
            return
        lv.clear()
        for i, item in enumerate(tracks):
            track = item.get("track")
            if not track:
                continue
            name = track.get("name", "Unknown")
            artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
            album = track.get("album", {}).get("name", "")
            duration = format_ms(track.get("duration_ms"))
            uri = track.get("uri", "")
            lv.append(
                ListItem(
                    Label(
                        f"[bold]{i + 1:>3}.[/]  [#1DB954]{esc(truncate(name, 35))}[/]  "
                        f"[italic]{esc(truncate(artists, 25))}[/]  [dim]{esc(truncate(album, 25))}[/]  [dim]{duration}[/]"
                    ),
                    id=f"lib-{uri_to_id(uri)}",
                )
            )

    @on(ListView.Selected, "#library-tracks-list")
    def on_track_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("lib-"):
            uri = id_to_uri(item_id, "lib-")
            self.play_track(uri)

    @work(thread=True)
    def play_track(self, uri: str) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        app.client.play(uris=[uri])


# ---------------------------------------------------------------------------
# View: Search
# ---------------------------------------------------------------------------


class SearchView(Static):
    """Search Spotify for tracks, albums, and artists."""

    def compose(self) -> ComposeResult:
        with Vertical(id="search-container"):
            yield Input(placeholder="Search Spotify...", id="search-input")
            yield Label("", id="search-status")
            with Vertical(id="search-results"):
                yield Label("[dim]Type a query and press Enter to search.[/]", id="search-hint")
                yield ListView(id="search-results-list")

    def focus_input(self) -> None:
        try:
            self.query_one("#search-input", Input).focus()
        except NoMatches:
            pass

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.run_search(query)

    @work(thread=True)
    def run_search(self, query: str) -> None:
        self.app.call_from_thread(self._set_status, f"[dim]Searching for \"{esc(query)}\"...[/]")
        app: TerminalIfy = self.app  # type: ignore[assignment]
        results = app.client.search(query, types=["track", "album", "artist"], limit=10)
        self.app.call_from_thread(self._populate_results, results)

    def _set_status(self, text: str) -> None:
        try:
            self.query_one("#search-status", Label).update(text)
        except NoMatches:
            pass

    def _populate_results(self, results: dict) -> None:
        try:
            lv = self.query_one("#search-results-list", ListView)
            hint = self.query_one("#search-hint", Label)
            status = self.query_one("#search-status", Label)
        except NoMatches:
            return

        lv.clear()
        total = 0

        # Tracks
        tracks = results.get("tracks", {}).get("items", [])
        if tracks:
            lv.append(ListItem(Label("[bold underline #1DB954]TRACKS[/]"), id="sep-tracks"))
            for track in tracks:
                name = track.get("name", "Unknown")
                artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
                duration = format_ms(track.get("duration_ms"))
                uri = track.get("uri", "")
                lv.append(
                    ListItem(
                        Label(f"  [#1DB954]{esc(truncate(name, 35))}[/]  [italic]{esc(truncate(artists, 25))}[/]  [dim]{duration}[/]"),
                        id=f"sr-track-{uri_to_id(uri)}",
                    )
                )
                total += 1

        # Albums
        albums = results.get("albums", {}).get("items", [])
        if albums:
            lv.append(ListItem(Label("\n[bold underline #1DB954]ALBUMS[/]"), id="sep-albums"))
            for album in albums:
                name = album.get("name", "Unknown")
                artists = ", ".join(a.get("name", "") for a in album.get("artists", []))
                year = (album.get("release_date") or "")[:4]
                uri = album.get("uri", "")
                lv.append(
                    ListItem(
                        Label(f"  [#1DB954]{esc(truncate(name, 35))}[/]  [italic]{esc(truncate(artists, 25))}[/]  [dim]{year}[/]"),
                        id=f"sr-album-{uri_to_id(uri)}",
                    )
                )
                total += 1

        # Artists
        artists_items = results.get("artists", {}).get("items", [])
        if artists_items:
            lv.append(ListItem(Label("\n[bold underline #1DB954]ARTISTS[/]"), id="sep-artists"))
            for artist in artists_items:
                name = artist.get("name", "Unknown")
                followers = artist.get("followers", {}).get("total", 0)
                uri = artist.get("uri", "")
                lv.append(
                    ListItem(
                        Label(f"  [#1DB954]{esc(name)}[/]  [dim]{followers:,} followers[/]"),
                        id=f"sr-artist-{uri_to_id(uri)}",
                    )
                )
                total += 1

        hint.update("" if total else "[dim]No results found.[/]")
        status.update(f"[dim]{total} results[/]" if total else "")

    @on(ListView.Selected, "#search-results-list")
    def on_result_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("sr-track-"):
            uri = id_to_uri(item_id, "sr-track-")
            self.play_uri(uri)
        elif item_id.startswith("sr-album-"):
            uri = id_to_uri(item_id, "sr-album-")
            self.play_context(uri)

    @work(thread=True)
    def play_uri(self, uri: str) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        app.client.play(uris=[uri])

    @work(thread=True)
    def play_context(self, uri: str) -> None:
        app: TerminalIfy = self.app  # type: ignore[assignment]
        app.client.play(context_uri=uri)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------


class TerminalIfy(App):
    """A Spotify client for your terminal."""

    CSS = TERMINAL_IFY_CSS

    TITLE = "terminal-ify"
    SUB_TITLE = "Spotify in your terminal"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("space", "toggle_play", "Play/Pause", priority=True),
        Binding("n", "next_track", "Next", priority=True),
        Binding("p", "prev_track", "Previous"),
        Binding("plus,equal", "volume_up", "Vol +", priority=True),
        Binding("minus,underscore", "volume_down", "Vol -", priority=True),
        Binding("s", "toggle_shuffle", "Shuffle"),
        Binding("r", "cycle_repeat", "Repeat"),
        Binding("slash", "focus_search", "Search", priority=True),
        Binding("1", "switch_tab('now-playing')", "Now Playing", priority=True),
        Binding("2", "switch_tab('playlists')", "Playlists", priority=True),
        Binding("3", "switch_tab('library')", "Library", priority=True),
        Binding("4", "switch_tab('search')", "Search", priority=True),
        Binding("d", "show_devices", "Devices"),
    ]

    # Reactive state for playback
    current_track: reactive[str] = reactive("Nothing playing")
    current_artist: reactive[str] = reactive("")
    current_album: reactive[str] = reactive("")
    is_playing: reactive[bool] = reactive(False)
    progress_pct: reactive[float] = reactive(0.0)
    elapsed_ms: reactive[int] = reactive(0)
    total_ms: reactive[int] = reactive(0)
    shuffle_state: reactive[bool] = reactive(False)
    repeat_state: reactive[str] = reactive("off")
    volume_level: reactive[int] = reactive(50)
    device_name: reactive[str] = reactive("")

    def __init__(self) -> None:
        super().__init__()
        self.client = SpotifyClient()
        self.player = LibrespotPlayer()
        self._player_device_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="app-root"):
            # Header
            with Horizontal(id="top-bar"):
                yield Static(MINI_LOGO, id="top-logo")
                yield Static("", id="top-device")

            # Main content with tabs
            with TabbedContent(id="main-tabs"):
                with TabPane("Now Playing", id="now-playing"):
                    yield NowPlayingView(id="now-playing-view")
                with TabPane("Playlists", id="playlists"):
                    yield PlaylistsView(id="playlists-view")
                with TabPane("Library", id="library"):
                    yield LibraryView(id="library-view")
                with TabPane("Search", id="search"):
                    yield SearchView(id="search-view")

            # Now-playing bar at bottom
            yield NowPlayingBar(id="now-playing-bar")
            yield Footer()

    def on_mount(self) -> None:
        """Start the polling timer and local player when the app mounts."""
        self._start_local_player()
        self.set_interval(2.0, self.poll_playback)
        self.poll_playback()

    @work(thread=True)
    def _start_local_player(self) -> None:
        """Start librespot if available, then auto-connect to it."""
        if not self.player.is_available():
            self.app.call_from_thread(
                self._set_top_device_status,
                "[dim]librespot not found — remote control only[/]",
            )
            return

        if not self.player.start():
            self.app.call_from_thread(
                self._set_top_device_status,
                "[dim]librespot failed to start[/]",
            )
            return

        self.app.call_from_thread(
            self._set_top_device_status,
            "[dim]Starting local player...[/]",
        )

        # Poll for the device to appear (librespot needs a moment to register)
        for _ in range(15):
            time.sleep(2)
            if not self.player.is_running:
                self.app.call_from_thread(
                    self._set_top_device_status,
                    "[dim]librespot stopped unexpectedly[/]",
                )
                return
            devices = self.client.get_devices()
            device_id = self.player.find_device_id(devices)
            if device_id:
                self._player_device_id = device_id
                # Transfer playback to our local player
                self.client.transfer_playback(device_id)
                self.poll_playback()
                return

        self.app.call_from_thread(
            self._set_top_device_status,
            "[dim]Local player ready — select 'terminal-ify' in devices (d)[/]",
        )

    def _set_top_device_status(self, markup: str) -> None:
        try:
            self.query_one("#top-device", Static).update(markup)
        except NoMatches:
            pass

    @work(thread=True)
    def poll_playback(self) -> None:
        """Fetch current playback state from Spotify."""
        playback = self.client.get_current_playback()
        self.app.call_from_thread(self._update_playback, playback)

    def _update_playback(self, playback: dict | None) -> None:
        """Update reactive state from playback data."""
        if not playback or not playback.get("item"):
            self.current_track = "Nothing playing"
            self.current_artist = ""
            self.current_album = ""
            self.is_playing = False
            self.progress_pct = 0.0
            self.elapsed_ms = 0
            self.total_ms = 0
            self.device_name = ""
        else:
            item = playback["item"]
            self.current_track = item.get("name", "Unknown")
            self.current_artist = ", ".join(
                a.get("name", "") for a in item.get("artists", [])
            )
            self.current_album = item.get("album", {}).get("name", "")
            self.is_playing = playback.get("is_playing", False)
            self.elapsed_ms = playback.get("progress_ms", 0) or 0
            self.total_ms = item.get("duration_ms", 0) or 0
            self.progress_pct = (
                self.elapsed_ms / self.total_ms if self.total_ms > 0 else 0.0
            )
            self.shuffle_state = playback.get("shuffle_state", False)
            self.repeat_state = playback.get("repeat_state", "off")

            device = playback.get("device", {})
            vol = device.get("volume_percent")
            self.volume_level = vol if vol is not None else 50
            self.device_name = device.get("name", "")

        self._sync_widgets()

    def _sync_widgets(self) -> None:
        """Push reactive state into the now-playing bar and view widgets."""
        try:
            bar = self.query_one("#now-playing-bar", NowPlayingBar)
            bar.track_name = self.current_track
            bar.artist_name = self.current_artist
            bar.album_name = self.current_album
            bar.is_playing = self.is_playing
            bar.progress = self.progress_pct
            bar.elapsed_ms = self.elapsed_ms
            bar.total_ms = self.total_ms
            bar.shuffle_on = self.shuffle_state
            bar.repeat_state = self.repeat_state
            bar.volume = self.volume_level
            bar.device_name = self.device_name
        except NoMatches:
            pass

        try:
            npv = self.query_one("#now-playing-view", NowPlayingView)
            npv.track_name = self.current_track
            npv.artist_name = self.current_artist
            npv.album_name = self.current_album
            npv.is_playing = self.is_playing
            npv.progress = self.progress_pct
            npv.elapsed_ms = self.elapsed_ms
            npv.total_ms = self.total_ms
            npv.shuffle_on = self.shuffle_state
            npv.repeat_state = self.repeat_state
        except NoMatches:
            pass

        try:
            top_device = self.query_one("#top-device", Static)
            if self.device_name:
                top_device.update(f"[dim]Playing on[/] [bold]{esc(self.device_name)}[/]")
            else:
                top_device.update("[dim]No active device[/]")
        except NoMatches:
            pass

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @work(thread=True)
    def action_toggle_play(self) -> None:
        if self.is_playing:
            self.client.pause()
        else:
            self.client.play()
        self.poll_playback()

    @work(thread=True)
    def action_next_track(self) -> None:
        self.client.next_track()
        self.poll_playback()

    @work(thread=True)
    def action_prev_track(self) -> None:
        self.client.previous_track()
        self.poll_playback()

    @work(thread=True)
    def action_volume_up(self) -> None:
        new_vol = min(100, self.volume_level + 5)
        self.client.set_volume(new_vol)
        self.volume_level = new_vol
        self.app.call_from_thread(self._sync_widgets)

    @work(thread=True)
    def action_volume_down(self) -> None:
        new_vol = max(0, self.volume_level - 5)
        self.client.set_volume(new_vol)
        self.volume_level = new_vol
        self.app.call_from_thread(self._sync_widgets)

    @work(thread=True)
    def action_toggle_shuffle(self) -> None:
        new_state = not self.shuffle_state
        self.client.toggle_shuffle(new_state)
        self.shuffle_state = new_state
        self.app.call_from_thread(self._sync_widgets)

    @work(thread=True)
    def action_cycle_repeat(self) -> None:
        cycle = {"off": "context", "context": "track", "track": "off"}
        new_state = cycle.get(self.repeat_state, "off")
        self.client.set_repeat(new_state)
        self.repeat_state = new_state
        self.app.call_from_thread(self._sync_widgets)

    def action_focus_search(self) -> None:
        try:
            tabs = self.query_one("#main-tabs", TabbedContent)
            tabs.active = "search"
            search_view = self.query_one("#search-view", SearchView)
            search_view.focus_input()
        except NoMatches:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        try:
            tabs = self.query_one("#main-tabs", TabbedContent)
            tabs.active = tab_id
        except NoMatches:
            pass

    def action_show_devices(self) -> None:
        self._fetch_and_show_devices()

    @work(thread=True)
    def _fetch_and_show_devices(self) -> None:
        devices = self.client.get_devices()
        self.app.call_from_thread(self._push_device_modal, devices)

    def _push_device_modal(self, devices: list) -> None:
        def on_device_selected(device_id: str | None) -> None:
            if device_id:
                self._transfer_to_device(device_id)

        self.push_screen(DeviceSelector(devices), on_device_selected)

    @work(thread=True)
    def _transfer_to_device(self, device_id: str) -> None:
        self.client.transfer_playback(device_id)
        self.poll_playback()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Launch the terminal-ify application."""
    app: TerminalIfy | None = None
    try:
        app = TerminalIfy()
        app.run()
    except Exception as exc:
        error_msg = str(exc).lower()
        if any(
            keyword in error_msg
            for keyword in ("client_id", "client_secret", "credentials", "token", "auth")
        ):
            print(
                "\n[terminal-ify] Could not reach the auth server or token is invalid.\n"
                "\n"
                "Make sure the auth server is reachable and try again.\n"
            )
            sys.exit(1)
        else:
            raise
    finally:
        if app is not None:
            app.player.stop()


if __name__ == "__main__":
    main()

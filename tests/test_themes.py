"""Tests for terminal_ify.themes — CSS validation."""

import pytest

from terminal_ify.themes import TERMINAL_IFY_CSS


class TestThemeCSS:
    def test_css_is_nonempty_string(self):
        assert isinstance(TERMINAL_IFY_CSS, str)
        assert len(TERMINAL_IFY_CSS) > 500

    # -- Key selectors that the app depends on --

    def test_has_screen_selector(self):
        assert "Screen {" in TERMINAL_IFY_CSS or "Screen{" in TERMINAL_IFY_CSS

    def test_has_now_playing_bar(self):
        assert "#now-playing-bar" in TERMINAL_IFY_CSS

    def test_has_footer_selector(self):
        assert "Footer" in TERMINAL_IFY_CSS

    def test_has_tabs_selector(self):
        assert "Tabs" in TERMINAL_IFY_CSS or "Tab " in TERMINAL_IFY_CSS

    def test_has_input_selector(self):
        assert "Input" in TERMINAL_IFY_CSS

    def test_has_listview_selector(self):
        assert "ListView" in TERMINAL_IFY_CSS

    def test_has_listitem_selector(self):
        assert "ListItem" in TERMINAL_IFY_CSS

    def test_has_button_selector(self):
        assert "Button" in TERMINAL_IFY_CSS

    def test_has_option_list_selector(self):
        assert "OptionList" in TERMINAL_IFY_CSS

    def test_has_progress_bar_selector(self):
        assert "ProgressBar" in TERMINAL_IFY_CSS or ".progress-bar" in TERMINAL_IFY_CSS

    # -- App layout IDs --

    def test_has_app_root(self):
        assert "#app-root" in TERMINAL_IFY_CSS

    def test_has_top_bar(self):
        assert "#top-bar" in TERMINAL_IFY_CSS

    def test_has_main_tabs(self):
        assert "#main-tabs" in TERMINAL_IFY_CSS

    def test_has_now_playing_view(self):
        assert "#now-playing-view" in TERMINAL_IFY_CSS

    def test_has_logo_art(self):
        assert "#logo-art" in TERMINAL_IFY_CSS

    def test_has_playlists_layout(self):
        assert "#playlists-layout" in TERMINAL_IFY_CSS

    def test_has_playlists_sidebar(self):
        assert "#playlists-sidebar" in TERMINAL_IFY_CSS

    def test_has_library_container(self):
        assert "#library-container" in TERMINAL_IFY_CSS

    def test_has_search_container(self):
        assert "#search-container" in TERMINAL_IFY_CSS

    def test_has_device_modal(self):
        assert "#device-modal" in TERMINAL_IFY_CSS

    def test_has_device_list(self):
        assert "#device-list" in TERMINAL_IFY_CSS

    # -- Spotify brand colors --

    def test_uses_spotify_green(self):
        assert "#1DB954" in TERMINAL_IFY_CSS or "#1db954" in TERMINAL_IFY_CSS

    def test_uses_dark_background(self):
        assert "#121212" in TERMINAL_IFY_CSS

    def test_uses_dark_surface(self):
        assert "#181818" in TERMINAL_IFY_CSS

    def test_uses_hover_surface(self):
        assert "#282828" in TERMINAL_IFY_CSS

    def test_uses_muted_text_color(self):
        assert "#B3B3B3" in TERMINAL_IFY_CSS or "#b3b3b3" in TERMINAL_IFY_CSS

    def test_uses_dimmed_text_color(self):
        assert "#727272" in TERMINAL_IFY_CSS

    # -- Structural properties --

    def test_screen_background_is_dark(self):
        # Screen should have the darkest background
        assert "background: #121212" in TERMINAL_IFY_CSS

    def test_now_playing_bar_docks_bottom(self):
        assert "dock: bottom" in TERMINAL_IFY_CSS

    def test_scrollbar_width(self):
        assert "width: 1" in TERMINAL_IFY_CSS

    # -- CSS syntax validation --

    def test_braces_are_balanced(self):
        opens = TERMINAL_IFY_CSS.count("{")
        closes = TERMINAL_IFY_CSS.count("}")
        assert opens == closes, f"Unbalanced braces: {opens} open vs {closes} close"

    def test_no_empty_rules(self):
        """Every rule block should have at least one property."""
        import re
        # Find blocks with nothing between { and }
        empty_blocks = re.findall(r"\{[\s]*\}", TERMINAL_IFY_CSS)
        assert len(empty_blocks) == 0, f"Found empty CSS rule blocks: {empty_blocks}"

    def test_css_parseable_by_textual(self):
        """Ensure Textual can parse the CSS without errors."""
        from textual.app import App
        # If the CSS is invalid, creating the class raises
        class TestApp(App):
            CSS = TERMINAL_IFY_CSS
        # Instantiation should not raise
        app = TestApp()

    # -- Layout IDs used by views --

    def test_has_np_track_info(self):
        assert "#np-track-info" in TERMINAL_IFY_CSS

    def test_has_np_progress_area(self):
        assert "#np-progress-area" in TERMINAL_IFY_CSS

    def test_has_np_controls_area(self):
        assert "#np-controls-area" in TERMINAL_IFY_CSS

    def test_has_playlists_detail(self):
        assert "#playlists-detail" in TERMINAL_IFY_CSS

    def test_has_search_results(self):
        assert "#search-results" in TERMINAL_IFY_CSS

    def test_has_device_cancel(self):
        assert "#device-cancel" in TERMINAL_IFY_CSS

    def test_has_top_logo(self):
        assert "#top-logo" in TERMINAL_IFY_CSS

    def test_has_top_device(self):
        assert "#top-device" in TERMINAL_IFY_CSS

    # -- Error/warning colors --

    def test_has_error_color(self):
        assert "#E22134" in TERMINAL_IFY_CSS or "#e22134" in TERMINAL_IFY_CSS

    def test_has_warning_color(self):
        assert "#F5A623" in TERMINAL_IFY_CSS or "#f5a623" in TERMINAL_IFY_CSS

    # -- Hover states exist for interactive elements --

    def test_has_hover_brightness_green(self):
        assert "#1ed760" in TERMINAL_IFY_CSS or "#1ED760" in TERMINAL_IFY_CSS

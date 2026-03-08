"""Tests for helper functions in terminal_ify.app."""

import pytest

from terminal_ify.app import (
    LOGO,
    MINI_LOGO,
    format_ms,
    id_to_uri,
    progress_bar_text,
    truncate,
    uri_to_id,
)


# ---------------------------------------------------------------------------
# format_ms
# ---------------------------------------------------------------------------


class TestFormatMs:
    def test_none_returns_placeholder(self):
        assert format_ms(None) == "--:--"

    def test_zero(self):
        assert format_ms(0) == "0:00"

    def test_one_second(self):
        assert format_ms(1000) == "0:01"

    def test_exact_minute(self):
        assert format_ms(60000) == "1:00"

    def test_one_minute_thirty(self):
        assert format_ms(90000) == "1:30"

    def test_typical_track_length(self):
        # 3:45
        assert format_ms(225000) == "3:45"

    def test_long_track(self):
        # 10:05
        assert format_ms(605000) == "10:05"

    def test_seconds_zero_padded(self):
        # 2:03
        assert format_ms(123000) == "2:03"

    def test_sub_second_truncated(self):
        # 1999ms should be 1s
        assert format_ms(1999) == "0:01"

    def test_large_value(self):
        # 99:59
        assert format_ms(5999000) == "99:59"


# ---------------------------------------------------------------------------
# truncate
# ---------------------------------------------------------------------------


class TestTruncate:
    def test_short_text_unchanged(self):
        assert truncate("hello", 40) == "hello"

    def test_exact_length_unchanged(self):
        text = "a" * 40
        assert truncate(text, 40) == text

    def test_long_text_truncated(self):
        text = "a" * 50
        result = truncate(text, 40)
        assert len(result) == 40
        assert result.endswith("\u2026")  # ellipsis

    def test_truncated_keeps_prefix(self):
        text = "abcdefghij"
        result = truncate(text, 5)
        assert result == "abcd\u2026"

    def test_empty_string(self):
        assert truncate("", 40) == ""

    def test_length_one(self):
        assert truncate("ab", 1) == "\u2026"

    def test_default_length(self):
        short = "short"
        assert truncate(short) == short
        long_text = "x" * 50
        assert len(truncate(long_text)) == 40


# ---------------------------------------------------------------------------
# uri_to_id / id_to_uri
# ---------------------------------------------------------------------------


class TestUriConversion:
    def test_uri_to_id_basic(self):
        assert uri_to_id("spotify:track:abc123") == "spotify-track-abc123"

    def test_uri_to_id_album(self):
        assert uri_to_id("spotify:album:xyz") == "spotify-album-xyz"

    def test_id_to_uri_track(self):
        result = id_to_uri("trk-spotify-track-abc123", "trk-")
        assert result == "spotify:track:abc123"

    def test_id_to_uri_album(self):
        result = id_to_uri("sr-album-spotify-album-xyz", "sr-album-")
        assert result == "spotify:album:xyz"

    def test_roundtrip_track(self):
        original = "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
        widget_id = f"trk-{uri_to_id(original)}"
        restored = id_to_uri(widget_id, "trk-")
        assert restored == original

    def test_roundtrip_album(self):
        original = "spotify:album:4aawyAB9vmqN3uQ7FjRGTy"
        widget_id = f"sr-album-{uri_to_id(original)}"
        restored = id_to_uri(widget_id, "sr-album-")
        assert restored == original

    def test_id_to_uri_only_replaces_first_two_dashes(self):
        # id_to_uri replaces only the first 2 dashes with colons
        widget_id = "trk-spotify-track-has-dashes-in-id"
        result = id_to_uri(widget_id, "trk-")
        assert result == "spotify:track:has-dashes-in-id"


# ---------------------------------------------------------------------------
# progress_bar_text
# ---------------------------------------------------------------------------


class TestProgressBarText:
    def test_zero_progress(self):
        result = progress_bar_text(0.0, width=10)
        assert "\u2591" * 10 in result  # all empty blocks
        assert "\u2593" not in result

    def test_full_progress(self):
        result = progress_bar_text(1.0, width=10)
        assert "\u2593" * 10 in result  # all filled blocks
        assert "\u2591" not in result

    def test_half_progress(self):
        result = progress_bar_text(0.5, width=10)
        assert "\u2593" * 5 in result
        assert "\u2591" * 5 in result

    def test_default_width(self):
        result = progress_bar_text(0.5)
        # Default is 30; 15 filled + 15 empty
        assert "\u2593" * 15 in result
        assert "\u2591" * 15 in result

    def test_contains_color_markup(self):
        result = progress_bar_text(0.5)
        assert "#1DB954" in result
        assert "[dim]" in result


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_logo_is_nonempty_string(self):
        assert isinstance(LOGO, str)
        assert len(LOGO) > 100

    def test_logo_contains_terminal(self):
        # The ASCII art spells out TERMINAL
        assert "\u2588" in LOGO or "\u2551" in LOGO or "█" in LOGO or "╗" in LOGO

    def test_mini_logo_contains_terminal_ify(self):
        assert "terminal" in MINI_LOGO
        assert "ify" in MINI_LOGO

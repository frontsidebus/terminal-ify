"""Tests for terminal_ify.player — LibrespotPlayer."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from terminal_ify.player import DEVICE_NAME, LibrespotPlayer


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestLibrespotPlayerInit:
    def test_default_device_name(self):
        player = LibrespotPlayer()
        assert player.device_name == DEVICE_NAME
        assert player.device_name == "terminal-ify"

    def test_custom_device_name(self):
        player = LibrespotPlayer(device_name="my-player")
        assert player.device_name == "my-player"

    def test_default_bitrate(self):
        player = LibrespotPlayer()
        assert player.bitrate == 320

    def test_custom_bitrate(self):
        player = LibrespotPlayer(bitrate=160)
        assert player.bitrate == 160

    def test_default_initial_volume(self):
        player = LibrespotPlayer()
        assert player.initial_volume == 50

    def test_custom_initial_volume(self):
        player = LibrespotPlayer(initial_volume=80)
        assert player.initial_volume == 80

    def test_default_cache_dir(self):
        player = LibrespotPlayer()
        assert player.cache_dir == Path.home() / ".cache" / "terminal-ify"

    def test_custom_cache_dir(self):
        custom = Path("/tmp/test-cache")
        player = LibrespotPlayer(cache_dir=custom)
        assert player.cache_dir == custom

    def test_default_backend_is_none(self):
        player = LibrespotPlayer()
        assert player.backend is None

    def test_custom_backend(self):
        player = LibrespotPlayer(backend="alsa")
        assert player.backend == "alsa"

    def test_process_initially_none(self):
        player = LibrespotPlayer()
        assert player.process is None


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_available_when_on_path(self, mock_which):
        assert LibrespotPlayer.is_available() is True
        mock_which.assert_called_once_with("librespot")

    @patch("terminal_ify.player.shutil.which", return_value=None)
    def test_not_available_when_missing(self, mock_which):
        assert LibrespotPlayer.is_available() is False


# ---------------------------------------------------------------------------
# is_running
# ---------------------------------------------------------------------------


class TestIsRunning:
    def test_not_running_when_process_is_none(self):
        player = LibrespotPlayer()
        assert player.is_running is False

    def test_running_when_process_alive(self):
        player = LibrespotPlayer()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        player.process = mock_proc
        assert player.is_running is True

    def test_not_running_when_process_exited(self):
        player = LibrespotPlayer()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0  # exited
        player.process = mock_proc
        assert player.is_running is False

    def test_not_running_when_process_crashed(self):
        player = LibrespotPlayer()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1  # crashed
        player.process = mock_proc
        assert player.is_running is False


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------


class TestStart:
    @patch("terminal_ify.player.shutil.which", return_value=None)
    def test_start_returns_false_if_not_available(self, _):
        player = LibrespotPlayer()
        assert player.start() is False
        assert player.process is None

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_launches_process(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        mock_popen.return_value = mock_proc
        player = LibrespotPlayer()

        result = player.start()

        assert result is True
        assert player.process is mock_proc
        mock_popen.assert_called_once()
        # Verify the command includes expected arguments
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == "librespot"
        assert "--name" in cmd
        assert "terminal-ify" in cmd
        assert "--bitrate" in cmd
        assert "320" in cmd

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_with_backend(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        player = LibrespotPlayer(backend="pulseaudio")

        player.start()

        cmd = mock_popen.call_args[0][0]
        assert "--backend" in cmd
        assert "pulseaudio" in cmd

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_without_backend(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        player = LibrespotPlayer()

        player.start()

        cmd = mock_popen.call_args[0][0]
        assert "--backend" not in cmd

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_returns_false_if_exits_immediately(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1  # exited immediately
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = b"error: some failure"
        mock_popen.return_value = mock_proc
        player = LibrespotPlayer()

        result = player.start()

        assert result is False
        assert player.process is None

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_returns_false_if_exits_immediately_no_stderr(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1
        mock_proc.stderr = None
        mock_popen.return_value = mock_proc
        player = LibrespotPlayer()

        result = player.start()

        assert result is False
        assert player.process is None

    @patch("terminal_ify.player.subprocess.Popen", side_effect=OSError("no such binary"))
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_returns_false_on_oserror(self, mock_which, mock_popen):
        player = LibrespotPlayer()
        result = player.start()
        assert result is False
        assert player.process is None

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_returns_true_if_already_running(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        player = LibrespotPlayer()

        # Start first time
        player.start()
        assert player.process is mock_proc

        # Start again -- should short-circuit and return True
        result = player.start()
        assert result is True
        # Popen should only have been called once
        assert mock_popen.call_count == 1

    @patch("terminal_ify.player.time.sleep")
    @patch("terminal_ify.player.subprocess.Popen")
    @patch("terminal_ify.player.shutil.which", return_value="/usr/bin/librespot")
    def test_start_creates_cache_dir(self, mock_which, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        cache_dir = MagicMock(spec=Path)
        player = LibrespotPlayer(cache_dir=cache_dir)

        player.start()

        cache_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------


class TestStop:
    def test_stop_when_no_process(self):
        player = LibrespotPlayer()
        player.stop()  # should not raise
        assert player.process is None

    def test_stop_terminates_process(self):
        player = LibrespotPlayer()
        mock_proc = MagicMock()
        player.process = mock_proc

        player.stop()

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=5)
        assert player.process is None

    def test_stop_kills_on_timeout(self):
        player = LibrespotPlayer()
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired("librespot", 5), None]
        player.process = mock_proc

        player.stop()

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert player.process is None

    def test_stop_handles_oserror(self):
        player = LibrespotPlayer()
        mock_proc = MagicMock()
        mock_proc.terminate.side_effect = OSError("process already dead")
        player.process = mock_proc

        player.stop()  # should not raise
        assert player.process is None


# ---------------------------------------------------------------------------
# find_device_id
# ---------------------------------------------------------------------------


class TestFindDeviceId:
    def test_find_device_in_list(self):
        player = LibrespotPlayer()
        devices = [
            {"id": "abc", "name": "terminal-ify"},
            {"id": "def", "name": "Other Device"},
        ]
        assert player.find_device_id(devices) == "abc"

    def test_find_device_custom_name(self):
        player = LibrespotPlayer(device_name="my-player")
        devices = [
            {"id": "abc", "name": "terminal-ify"},
            {"id": "xyz", "name": "my-player"},
        ]
        assert player.find_device_id(devices) == "xyz"

    def test_returns_none_if_not_found(self):
        player = LibrespotPlayer()
        devices = [
            {"id": "abc", "name": "Other Device"},
        ]
        assert player.find_device_id(devices) is None

    def test_returns_none_for_empty_list(self):
        player = LibrespotPlayer()
        assert player.find_device_id([]) is None

    def test_device_missing_name_key(self):
        player = LibrespotPlayer()
        devices = [{"id": "abc"}]
        assert player.find_device_id(devices) is None

    def test_device_missing_id_key(self):
        player = LibrespotPlayer()
        devices = [{"name": "terminal-ify"}]
        # Should return None because .get("id") returns None
        assert player.find_device_id(devices) is None

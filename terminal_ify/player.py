"""Librespot integration for local Spotify playback."""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path

log = logging.getLogger(__name__)

DEVICE_NAME = "terminal-ify"


class LibrespotPlayer:
    """Manages a librespot subprocess for local audio playback."""

    def __init__(
        self,
        device_name: str = DEVICE_NAME,
        bitrate: int = 320,
        initial_volume: int = 50,
        cache_dir: Path | None = None,
        backend: str | None = None,
    ) -> None:
        self.device_name = device_name
        self.bitrate = bitrate
        self.initial_volume = initial_volume
        self.cache_dir = cache_dir or Path.home() / ".cache" / "terminal-ify"
        self.backend = backend
        self.process: subprocess.Popen | None = None  # type: ignore[type-arg]

    @staticmethod
    def is_available() -> bool:
        """Check if librespot is installed and on PATH."""
        return shutil.which("librespot") is not None

    def start(self) -> bool:
        """Start librespot in Spotify Connect (zeroconf) mode.

        Returns True if the process started successfully.
        """
        if self.is_running:
            return True

        if not self.is_available():
            return False

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "librespot",
            "--name", self.device_name,
            "--cache", str(self.cache_dir),
            "--bitrate", str(self.bitrate),
            "--device-type", "computer",
            "--initial-volume", str(self.initial_volume),
            "--enable-volume-normalisation",
        ]

        if self.backend:
            cmd.extend(["--backend", self.backend])

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            # Give it a moment to start
            time.sleep(0.5)
            if self.process.poll() is not None:
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                log.warning("librespot exited immediately: %s", stderr)
                self.process = None
                return False
            return True
        except OSError as exc:
            log.warning("Failed to start librespot: %s", exc)
            self.process = None
            return False

    def stop(self) -> None:
        """Stop the librespot subprocess."""
        if self.process is None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        except OSError:
            pass
        finally:
            self.process = None

    @property
    def is_running(self) -> bool:
        """Check if the librespot process is still running."""
        return self.process is not None and self.process.poll() is None

    def find_device_id(self, devices: list[dict]) -> str | None:
        """Find our librespot device in a Spotify API devices list."""
        for dev in devices:
            if dev.get("name") == self.device_name:
                return dev.get("id")
        return None

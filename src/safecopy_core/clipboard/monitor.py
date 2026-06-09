"""Clipboard backend abstraction + polling monitor.

Production target is Windows 11 (pywin32 clipboard hooks). For development and
tests we use a pluggable :class:`ClipboardBackend` so the engine never depends
on a real OS clipboard. ``PyperclipBackend`` is used when ``pyperclip`` is
installed; ``InMemoryBackend`` is the default and is what tests drive.

The monitor itself is a simple poll loop — kept intentionally dumb so all the
interesting logic stays in the detection/policy pipeline.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol


class ClipboardBackend(Protocol):
    def get_text(self) -> str | None: ...
    def set_text(self, text: str) -> None: ...


class InMemoryBackend:
    """A fake clipboard, used by tests and the demo CLI."""

    def __init__(self, initial: str | None = None):
        self._text = initial

    def get_text(self) -> str | None:
        return self._text

    def set_text(self, text: str) -> None:
        self._text = text


class PyperclipBackend:
    """Cross-platform backend via the optional ``pyperclip`` dependency."""

    def __init__(self) -> None:
        import pyperclip  # imported lazily; part of the [clipboard] extra

        self._pyperclip = pyperclip

    def get_text(self) -> str | None:
        text: str = self._pyperclip.paste()
        return text

    def set_text(self, text: str) -> None:
        self._pyperclip.copy(text)


def default_backend() -> ClipboardBackend:
    """Return pyperclip if available, else an in-memory clipboard."""
    try:
        return PyperclipBackend()
    except Exception:
        return InMemoryBackend()


class ClipboardMonitor:
    """Poll a backend and invoke ``on_change`` whenever the text changes."""

    def __init__(
        self,
        backend: ClipboardBackend,
        on_change: Callable[[str], None],
        poll_interval: float = 0.2,
    ):
        self._backend = backend
        self._on_change = on_change
        self._poll_interval = poll_interval
        self._last: str | None = None

    def poll_once(self) -> None:
        """Check the clipboard a single time (the unit tests exercise this)."""
        text = self._backend.get_text()
        if text is not None and text != self._last:
            self._last = text
            self._on_change(text)

    def run(self) -> None:  # pragma: no cover - blocking loop
        while True:
            self.poll_once()
            time.sleep(self._poll_interval)

"""Shared test helpers."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "core"))

from nskills.adapters import load_adapters  # noqa: E402


def adapters():
    return load_adapters(REPO_ROOT)


@contextlib.contextmanager
def temp_env() -> Iterator[Path]:
    """Isolate HOME, XDG dirs, HERMES_HOME, and NSkills state."""

    keys = [
        "HOME",
        "XDG_CONFIG_HOME",
        "XDG_STATE_HOME",
        "HERMES_HOME",
        "NSKILLS_STATE_DIR",
        "NSKILLS_ROOT",
    ]
    saved = {key: os.environ.get(key) for key in keys}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home"
        home.mkdir()
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
        os.environ["XDG_STATE_HOME"] = str(home / ".local" / "state")
        os.environ["HERMES_HOME"] = str(root / "hermes")
        os.environ["NSKILLS_STATE_DIR"] = str(home / ".local" / "state" / "nskills")
        os.environ.pop("NSKILLS_ROOT", None)
        try:
            yield root
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

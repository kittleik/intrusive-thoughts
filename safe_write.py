"""Atomic file writes for state durability.

Write to a temp file in the same directory, then rename (atomic on POSIX).
This prevents corruption from crashes mid-write.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Union


def atomic_write_text(path: Union[str, Path], content: str) -> None:
    """Atomically write text content to a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: Union[str, Path], data: Any, **kwargs) -> None:
    """Atomically write JSON data to a file."""
    kwargs.setdefault("indent", 2)
    kwargs.setdefault("default", str)
    content = json.dumps(data, **kwargs)
    atomic_write_text(path, content)


def safe_append_json_array(path: Union[str, Path], entry: Any) -> None:
    """Safely append an entry to a JSON array file."""
    path = Path(path)
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if not isinstance(data, list):
                data = [data]
        except (json.JSONDecodeError, OSError):
            # Corrupted — back up and start fresh
            backup = path.with_suffix(".json.bak")
            try:
                os.rename(path, backup)
            except OSError:
                pass
            data = []
    data.append(entry)
    atomic_write_json(path, data)

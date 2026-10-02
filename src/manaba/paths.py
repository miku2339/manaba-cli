from __future__ import annotations

import os
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("MANABA_DATA_DIR")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg).expanduser() / "manaba-cli"
    return Path.home() / ".local" / "share" / "manaba-cli"


def session_path() -> Path:
    return data_dir() / "session.json"


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def ensure_private_file(path: Path) -> None:
    if path.is_symlink():
        raise OSError("session 路徑是符號連結，已拒絕寫入。")
    ensure_private_dir(path.parent)
    path.touch(exist_ok=True)
    path.chmod(0o600)

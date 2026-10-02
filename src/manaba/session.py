from __future__ import annotations

import json
from pathlib import Path

import httpx

from manaba.paths import ensure_private_file

ORIGIN_HOST = "nagasaki-gaigo.manaba.jp"


def dump_cookies(client: httpx.Client) -> list[dict]:
    cookies: list[dict] = []
    for cookie in client.cookies.jar:
        if not cookie.name or cookie.value is None:
            continue
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or "",
                "path": cookie.path or "/",
                "secure": bool(cookie.secure),
            }
        )
    return cookies


def save_session(client: httpx.Client, path: Path, *, saved_at: str) -> None:
    ensure_private_file(path)
    payload = {
        "version": 1,
        "origin": f"https://{ORIGIN_HOST}",
        "saved_at": saved_at,
        "cookies": dump_cookies(client),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def load_session(client: httpx.Client, path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    cookies = payload.get("cookies") or []
    if not isinstance(cookies, list):
        return
    for cookie in cookies:
        if not isinstance(cookie, dict) or not cookie.get("name"):
            continue
        client.cookies.set(
            cookie["name"],
            cookie.get("value") or "",
            domain=cookie.get("domain") or ORIGIN_HOST,
            path=cookie.get("path") or "/",
        )


def session_file_ready(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    cookies = payload.get("cookies")
    return isinstance(cookies, list) and any(
        isinstance(cookie, dict) and cookie.get("name") and cookie.get("value") for cookie in cookies
    )

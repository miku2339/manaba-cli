from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

from manaba.errors import LoginFailed, MissingSession, NetworkError, UnrecognizedPage, UsageError
from manaba.parse import is_logged_in, page_title, parse_login_form
from manaba.provenance import utc_now
from manaba.session import load_session, save_session

ORIGIN = "https://nagasaki-gaigo.manaba.jp"
BASE_URL = ORIGIN + "/ct/"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
MAX_DOWNLOAD_BYTES = 80 * 1024 * 1024


def resolve_target(target: str) -> str:
    raw = target.strip()
    if not raw or any(char in raw for char in "\\\r\n"):
        raise UsageError("頁面路徑不合法。")
    parts = urlsplit(raw)
    if parts.scheme or parts.netloc:
        url = raw
    else:
        if raw.startswith("//") or any(segment == ".." for segment in parts.path.split("/")):
            raise UsageError("頁面路徑不合法。")
        url = urljoin(BASE_URL, raw)
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or host != "nagasaki-gaigo.manaba.jp"
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
    ):
        raise UsageError("只會向長崎外國語大學 manaba 發送請求。")
    return url


def make_client(session_file: Path | None = None, *, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    client = httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ja,zh-TW;q=0.8,en;q=0.5"},
        follow_redirects=True,
        timeout=60.0,
        transport=transport,
    )
    if session_file is not None:
        load_session(client, session_file)
    return client


def _request(client: httpx.Client, method: str, target: str, **kwargs) -> httpx.Response:
    url = resolve_target(target)
    try:
        response = client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        raise NetworkError("網路請求失敗。") from exc
    final = urlsplit(str(response.url))
    if (final.hostname or "").lower() != "nagasaki-gaigo.manaba.jp":
        raise UsageError("manaba 把請求轉到了其他網站，已中止。")
    return response


def login(client: httpx.Client, userid: str, password: str, session_file: Path) -> str:
    page = _request(client, "GET", "login")
    if page.status_code >= 400:
        raise NetworkError(f"登入頁回應 HTTP {page.status_code}。")
    form = parse_login_form(page.text)
    payload = dict(form["fields"])
    payload[form["userid_field"]] = userid
    payload[form["password_field"]] = password
    payload.setdefault("login", "ログイン")
    action = urljoin(str(page.url), form["action"])
    # Action is still checked by resolve after joining against the login page.
    relative = action
    parsed_action = urlsplit(action)
    if parsed_action.scheme or parsed_action.netloc:
        relative = action
    submitted = _request(client, "POST", relative, data=payload)
    if submitted.status_code >= 400:
        raise LoginFailed("登入失敗。請確認ユーザID與密碼。")
    if not is_logged_in(submitted.text):
        raise LoginFailed("登入失敗。請確認ユーザID與密碼。")
    save_session(client, session_file, saved_at=utc_now())
    return page_title(submitted.text) or ""


def fetch_html(client: httpx.Client, target: str, session_file: Path) -> str:
    response = _request(client, "GET", target)
    if response.status_code >= 400:
        raise NetworkError(f"頁面回應 HTTP {response.status_code}。")
    if not is_logged_in(response.text):
        raise MissingSession("session 已失效或尚未登入。請在本機 Terminal 執行 manaba login。")
    save_session(client, session_file, saved_at=utc_now())
    return response.text


def require_recognized(recognized: bool) -> None:
    if not recognized:
        raise UnrecognizedPage("讀到了頁面，但版面無法辨識，不能當成沒有資料。")


def download_file(client: httpx.Client, target: str, output: Path, session_file: Path) -> dict:
    if output.exists():
        raise UsageError(f"檔案已存在：{output}")
    url = resolve_target(target)
    try:
        with client.stream("GET", url, follow_redirects=True) as response:
            final = urlsplit(str(response.url))
            if (final.hostname or "").lower() != "nagasaki-gaigo.manaba.jp":
                raise UsageError("manaba 把請求轉到了其他網站，已中止。")
            if response.status_code >= 400:
                raise NetworkError(f"下載回應 HTTP {response.status_code}。")
            content_type = response.headers.get("content-type", "")
            length = response.headers.get("content-length")
            if length and length.isdigit() and int(length) > MAX_DOWNLOAD_BYTES:
                raise UsageError("檔案超過 80MB，已拒絕下載。")
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise UsageError("檔案超過 80MB，已拒絕下載。")
                chunks.append(chunk)
    except httpx.HTTPError as exc:
        raise NetworkError("網路請求失敗。") from exc
    body = b"".join(chunks)
    looks_html = "html" in content_type.lower() or body.lstrip().startswith(b"<")
    if looks_html:
        text = body.decode("utf-8", errors="replace")
        if not is_logged_in(text):
            raise MissingSession("session 已失效或尚未登入。請在本機 Terminal 執行 manaba login。")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(body)
    save_session(client, session_file, saved_at=utc_now())
    return {
        "path": str(output),
        "bytes": len(body),
        "content_type": content_type.split(";", 1)[0].strip(),
        "href": target,
    }


def logout_remote(client: httpx.Client) -> None:
    try:
        _request(client, "GET", "logout")
    except (NetworkError, UsageError):
        return

from __future__ import annotations

import json
from pathlib import Path

import httpx

from manaba.api import login, make_client, resolve_target
from manaba.cli import main
from manaba.errors import UsageError
from manaba.parse import parse_courses, parse_login_form, parse_resources, parse_tasks
from manaba.secrets import MemoryStore, resolve_login

LOGIN_HTML = """
<html><head><title>長崎外国語大学 manaba - login</title></head>
<body>
<form action=login method="POST" utn>
  <input type="text" id="mainuserid" name="userid">
  <input type="password" name="password">
  <input type=submit id=login name=login value="ログイン">
  <input type="hidden" name="manaba-form" value="1">
  <input type=hidden name=SessionValue1 value="dummy
token">
  <input type=hidden name=SessionValue value="@1">
</form>
</body></html>
"""

HOME_HTML = """
<html><head><title>manaba - home</title></head>
<body><a href="logout">ログアウト</a><div class="pagebody">ホーム</div></body>
</html>
"""

COURSES_HTML = """
<html><body>
<a href="logout">ログアウト</a>
<table class="courselist">
<tr>
  <td><span class="courselist-title"><a href="course_42">日本語 I</a></span></td>
  <td>2026</td>
  <td>前期 月曜 1限</td>
  <td>山田</td>
</tr>
</table>
<a href="course_7">英語</a>
<a href="course_7_news_1">お知らせ</a>
<a href="/ct/course_8">中国語</a>
</body></html>
"""

TASKS_HTML = """
<html><body>
<table class="stdlist">
<tr><th>種別</th><th>タイトル</th><th>コース</th><th>開始</th><th>終了</th></tr>
<tr>
  <td>レポート</td>
  <td><a href="course_42_report_9">第1回</a></td>
  <td>日本語 I</td>
  <td>2026-04-01 00:00</td>
  <td>2026-04-15 23:59</td>
</tr>
<tr>
  <td>小テスト</td>
  <td><a href="/ct/course_42_query_3">確認テスト</a></td>
  <td>日本語 I</td>
  <td></td>
  <td>2026-05-01 17:00</td>
</tr>
<tr>
  <td>プロジェクト</td>
  <td><a href="course_42_project_4">発表</a></td>
  <td>日本語 I</td>
  <td></td>
  <td></td>
</tr>
</table>
</body></html>
"""

CONTENTS_HTML = """
<html><body>
<table class="stdlist">
<tr><td><a href="page_15?c42">第1回教材</a></td></tr>
</table>
<a href="page_99?c420">別の授業</a>
</body></html>
"""


def test_login_form_keeps_hidden_fields():
    form = parse_login_form(LOGIN_HTML)
    assert form["userid_field"] == "userid"
    assert form["password_field"] == "password"
    fields = dict(form["fields"])
    assert fields["manaba-form"] == "1"
    assert fields["SessionValue"] == "@1"
    assert "dummy" in fields["SessionValue1"]
    assert "token" in fields["SessionValue1"]
    assert "userid" not in fields
    assert "password" not in fields


def test_courses_skip_section_links():
    courses, recognized = parse_courses(COURSES_HTML)
    assert recognized
    assert [course["id"] for course in courses] == [7, 8, 42]
    japanese = next(course for course in courses if course["id"] == 42)
    assert japanese["name"] == "日本語 I"
    assert japanese["year"] == "2026"
    assert japanese["teacher"] == "山田"


def test_courses_unrecognized_without_markers():
    courses, recognized = parse_courses("<html><a href='logout'>ログアウト</a><p>準備中</p></html>")
    assert courses == []
    assert recognized is False


def test_tasks_kinds_and_empty_message():
    tasks, recognized = parse_tasks(TASKS_HTML)
    assert recognized
    assert [task["kind"] for task in tasks] == ["report", "quiz", "project"]
    assert tasks[0]["ends_at"] == "2026-04-15 23:59"
    empty, empty_ok = parse_tasks("<html><p>該当する課題はありません</p></html>")
    assert empty == []
    assert empty_ok


def test_contents_require_course_marker():
    items, recognized = parse_resources(CONTENTS_HTML, 42, ("page",))
    assert recognized
    assert [item["href"] for item in items] == ["page_15?c42"]


def test_resolve_target_stays_on_manaba():
    assert resolve_target("home").endswith("/ct/home")
    assert resolve_target("page_15?c42").endswith("/ct/page_15?c42")
    for blocked in (
        "https://evil.example/ct/home",
        "https://nagasaki-gaigo.manaba.jp.evil.example/ct/home",
        "//evil.example/ct/home",
        "../secret",
        "https://user:pw@nagasaki-gaigo.manaba.jp/ct/home",
    ):
        try:
            resolve_target(blocked)
        except UsageError:
            continue
        raise AssertionError(blocked)


def test_status_without_session_is_unverified(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MANABA_DATA_DIR", str(tmp_path))
    assert main(["status", "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["status"] == "unverified"
    assert payload["source"] == "unverified"
    assert "password" not in payload


def test_login_refuses_non_tty(monkeypatch):
    monkeypatch.setattr("manaba.secrets.stdin_is_tty", lambda: False)
    try:
        resolve_login(MemoryStore())
    except Exception as exc:
        assert exc.status == "secret_input_blocked"
        return
    raise AssertionError("expected secret input block")


def test_login_saves_cookie_not_password(tmp_path, monkeypatch):
    monkeypatch.setenv("MANABA_DATA_DIR", str(tmp_path))
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, text=LOGIN_HTML)
        seen["body"] = request.content.decode()
        return httpx.Response(
            200,
            text=HOME_HTML,
            headers={"set-cookie": "sessionid=rotated-session; Path=/; Secure"},
        )

    session = tmp_path / "session.json"
    client = make_client(transport=httpx.MockTransport(handler))
    login(client, "student01", "secret-password", session)
    client.close()
    raw = session.read_text(encoding="utf-8")
    assert "secret-password" not in raw
    assert "rotated-session" in raw
    assert "userid=student01" in seen["body"]
    assert "password=secret-password" in seen["body"]
    assert session.stat().st_mode & 0o777 == 0o600


def test_redact_cookie_key(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MANABA_DATA_DIR", str(tmp_path))
    assert main(["status", "--json"]) == 2
    text = capsys.readouterr().out
    assert "sessionid=" not in text


def test_real_login_page_if_cached():
    cached = Path("/tmp/manaba-login.html")
    if not cached.exists():
        return
    form = parse_login_form(cached.read_text(encoding="utf-8"))
    assert form["userid_field"] == "userid"
    assert form["password_field"] == "password"
    assert "SessionValue" in dict(form["fields"])


def test_readmes_have_six_languages():
    root = Path(__file__).resolve().parents[1]
    files = (
        "README.md",
        "README.zh-TW.md",
        "README.en.md",
        "README.ko.md",
        "README.fr.md",
        "README.de.md",
    )
    markers = ("日本語", "繁體中文", "English", "한국어", "Français", "Deutsch")
    for name in files:
        text = (root / name).read_text(encoding="utf-8")
        first = text.splitlines()[0]
        for marker in markers:
            assert marker in first
        assert "manaba status --json" in text
        assert "https://nagasaki-gaigo.manaba.jp" in text
        for other in files:
            if other != name:
                assert other in first

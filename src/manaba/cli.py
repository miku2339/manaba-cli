from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from manaba import __version__
from manaba.api import (
    download_file,
    fetch_html,
    login,
    logout_remote,
    make_client,
    require_recognized,
)
from manaba.errors import ManabaError, MissingSession, UsageError
from manaba.parse import (
    is_logged_in,
    page_title,
    parse_course_page,
    parse_courses,
    parse_grades,
    parse_resources,
    parse_table_page,
    parse_tasks,
)
from manaba.paths import session_path
from manaba.provenance import envelope
from manaba.secrets import PASSWORD_ITEM, USERID_ITEM, default_store, resolve_login
from manaba.session import session_file_ready

RESOURCES = {
    "news": ("course_{id}_news", ("news",)),
    "reports": ("course_{id}_report", ("report",)),
    "quizzes": ("course_{id}_query", ("query", "drill")),
    "surveys": ("course_{id}_survey", ("survey",)),
    "projects": ("course_{id}_project", ("project",)),
    "topics": ("course_{id}_topics", ("topics",)),
    "contents": ("course_{id}_page", ("page",)),
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code in (None, 0):
            return 0
        if code == 2:
            return 3
        return int(code) if isinstance(code, int) else 3
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 3
    try:
        payload = handler(args)
    except ManabaError as exc:
        payload = envelope(
            command=getattr(args, "command_name", args.cmd),
            source="unverified",
            ok=False,
            status=exc.status,
            error=str(exc),
        )
        _emit(payload, json_mode=_wants_json(args))
        return exc.exit_code
    except Exception:
        payload = envelope(
            command=getattr(args, "command_name", "manaba"),
            source="unverified",
            ok=False,
            status="error",
            error="指令執行失敗。",
        )
        _emit(payload, json_mode=_wants_json(args))
        return 1
    _emit(payload, json_mode=_wants_json(args))
    return 0 if payload.get("ok") else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manaba",
        description="長崎外國語大學 manaba 的只讀 CLI。登入必須在本機 Terminal 執行。",
    )
    parser.add_argument("--version", action="version", version=f"manaba {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    login_cmd = sub.add_parser("login", help="在本機 Terminal 登入，並保存 session。")
    login_cmd.add_argument("--json", action="store_true")
    login_cmd.add_argument(
        "--store-password",
        action="store_true",
        help="登入成功後把ユーザID與密碼寫進 macOS Keychain。",
    )
    login_cmd.set_defaults(handler=cmd_login, command_name="login")

    logout_cmd = sub.add_parser("logout", help="清掉本機 session。")
    logout_cmd.add_argument("--json", action="store_true")
    logout_cmd.set_defaults(handler=cmd_logout, command_name="logout")

    status = sub.add_parser("status", help="確認本機 session 是否仍可讀 manaba。")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=cmd_status, command_name="status")

    courses = sub.add_parser("courses", help="列出已登錄的課程。")
    courses.add_argument("--json", action="store_true")
    courses.set_defaults(handler=cmd_courses, command_name="courses")

    tasks = sub.add_parser("tasks", help="列出未提出課題。")
    tasks.add_argument("--json", action="store_true")
    tasks.add_argument("--course", type=_course_id)
    tasks.add_argument(
        "--kind",
        choices=("quiz", "drill", "survey", "report", "project"),
        help="quiz 含ドリル。",
    )
    tasks.set_defaults(handler=cmd_tasks, command_name="tasks")

    course = sub.add_parser("course", help="列出一門課的功能入口。")
    course.add_argument("course_id", type=_course_id)
    course.add_argument("--json", action="store_true")
    course.set_defaults(handler=cmd_course, command_name="course")

    for name, help_text in (
        ("news", "課程新聞。"),
        ("reports", "レポート。"),
        ("quizzes", "小測試與ドリル。"),
        ("surveys", "アンケート。"),
        ("projects", "專案學習。"),
        ("topics", "掲示板。"),
        ("contents", "課程內容。"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("course_id", type=_course_id)
        command.add_argument("--json", action="store_true")
        command.set_defaults(handler=cmd_resource, command_name=name, resource=name)

    grades = sub.add_parser("grades", help="一門課的成績。")
    grades.add_argument("course_id", type=_course_id)
    grades.add_argument("--json", action="store_true")
    grades.set_defaults(handler=cmd_grades, command_name="grades")

    portfolio = sub.add_parser("portfolio", help="ポートフォリオ。")
    portfolio.add_argument("--json", action="store_true")
    portfolio.set_defaults(handler=cmd_portfolio, command_name="portfolio")

    submissions = sub.add_parser("submissions", help="提出記錄。")
    submissions.add_argument("--json", action="store_true")
    submissions.set_defaults(handler=cmd_submissions, command_name="submissions")

    download = sub.add_parser("download", help="下載同一個 manaba 上的單一檔案。")
    download.add_argument("target", help="例如 course_1_report_2 或 page_3?c1")
    download.add_argument("-o", "--output", required=True, type=Path)
    download.add_argument("--json", action="store_true")
    download.set_defaults(handler=cmd_download, command_name="download")
    return parser


def _course_id(value: str) -> int:
    if not value.isdigit() or int(value) < 1:
        raise argparse.ArgumentTypeError("課程 ID 必須是正整數。")
    return int(value)


def _wants_json(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False))


def _emit(payload: dict[str, Any], *, json_mode: bool) -> None:
    clean = redact_public_payload(payload)
    if json_mode:
        json.dump(clean, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    _print_human(clean)


def redact_public_payload(payload: Any) -> Any:
    blocked = {
        "password",
        "token",
        "cookie",
        "cookies",
        "authorization",
        "secret",
        "csrf",
        "sessionvalue",
        "sessionvalue1",
        "sessionid",
    }
    if isinstance(payload, dict):
        return {
            key: redact_public_payload(value)
            for key, value in payload.items()
            if key.lower() not in blocked
        }
    if isinstance(payload, list):
        return [redact_public_payload(item) for item in payload]
    if isinstance(payload, str):
        lowered = payload.lower()
        if "sessionid=" in lowered or "password=" in lowered:
            return "[redacted]"
    return payload


def _print_human(payload: dict[str, Any]) -> None:
    print(
        f"{payload.get('command')}  site={payload.get('site')}  "
        f"source={payload.get('source')}  status={payload.get('status')}"
    )
    if payload.get("error"):
        print(payload["error"])
        return
    if payload.get("command") == "login":
        print(f"authenticated={payload.get('authenticated')} userid={payload.get('userid')}")
        return
    if payload.get("command") == "status":
        print(f"authenticated={payload.get('authenticated')} title={payload.get('title') or '-'}")
        return
    if "courses" in payload:
        courses = payload["courses"]
        print(f"courses: {len(courses)}")
        for row in courses:
            extra = "  ".join(
                part for part in (row.get("year"), row.get("schedule"), row.get("teacher")) if part
            )
            suffix = f"  {extra}" if extra else ""
            print(f"  {row.get('id')}  {row.get('name')}{suffix}")
        return
    if "tasks" in payload:
        tasks = payload["tasks"]
        print(f"tasks: {len(tasks)}")
        for row in tasks:
            due = row.get("ends_at") or "unverified"
            print(f"  {row.get('kind')}  {row.get('title')}  {row.get('course')}  due={due}  {row.get('href')}")
        return
    if "sections" in payload:
        print(payload.get("title") or f"course {payload.get('course_id')}")
        for row in payload["sections"]:
            print(f"  {row.get('kind') or '-'}  {row.get('title')}  {row.get('href')}")
        return
    if "items" in payload:
        items = payload["items"]
        print(f"items: {len(items)}")
        for row in items:
            print(f"  {row.get('title')}  {row.get('href')}")
        return
    if "rows" in payload:
        rows = payload["rows"]
        print(payload.get("title") or payload.get("command"))
        print(f"rows: {len(rows)}")
        for row in rows[:30]:
            if row.get("label"):
                print(f"  {row['label']}: {row.get('value')}")
            else:
                print(f"  {row.get('title') or '  '.join(row.get('cells') or [])}  {row.get('href') or ''}")
        if len(rows) > 30:
            print(f"  … {len(rows) - 30} more")
        return
    if payload.get("command") == "download":
        print(f"path={payload.get('path')} bytes={payload.get('bytes')}")


def _open_client():
    path = session_path()
    if not session_file_ready(path):
        raise MissingSession("尚未登入。請在本機 Terminal 執行 manaba login。讀不到不代表沒有課或沒有作業。")
    return make_client(path), path


def cmd_login(args: argparse.Namespace) -> dict[str, Any]:
    store = default_store()
    userid, password, _from_store = resolve_login(store)
    path = session_path()
    client = make_client()
    try:
        title = login(client, userid, password, path)
    finally:
        client.close()
    stored = False
    if args.store_password:
        try:
            store.set(USERID_ITEM, userid)
            store.set(PASSWORD_ITEM, password)
            stored = True
        except Exception:
            stored = False
    return envelope(
        command="login",
        source="manaba_html",
        ok=True,
        status="ok",
        authenticated=True,
        userid=userid,
        title=title,
        password_stored=stored,
        session=str(path),
    )


def cmd_logout(args: argparse.Namespace) -> dict[str, Any]:
    del args
    path = session_path()
    if session_file_ready(path):
        client = make_client(path)
        try:
            logout_remote(client)
        finally:
            client.close()
    if path.exists() or path.is_symlink():
        path.unlink()
    return envelope(command="logout", source="manaba_html", ok=True, status="ok", authenticated=False)


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    del args
    client, path = _open_client()
    try:
        html = fetch_html(client, "home", path)
    finally:
        client.close()
    if not is_logged_in(html):
        raise MissingSession("session 已失效。請在本機 Terminal 執行 manaba login。")
    return envelope(
        command="status",
        source="manaba_html",
        ok=True,
        status="ok",
        authenticated=True,
        title=page_title(html),
        session=str(path),
    )


def cmd_courses(args: argparse.Namespace) -> dict[str, Any]:
    del args
    html = _read("home_course")
    courses, recognized = parse_courses(html)
    require_recognized(recognized)
    return envelope(
        command="courses",
        source="manaba_html",
        ok=True,
        status="ok",
        courses=courses,
    )


def cmd_tasks(args: argparse.Namespace) -> dict[str, Any]:
    html = _read("home_library_query")
    tasks, recognized = parse_tasks(html)
    require_recognized(recognized)
    if args.course is not None:
        tasks = [task for task in tasks if task.get("course_id") == args.course]
    if args.kind:
        wanted = {"quiz", "drill"} if args.kind == "quiz" else {args.kind}
        tasks = [task for task in tasks if task.get("kind") in wanted]
    return envelope(command="tasks", source="manaba_html", ok=True, status="ok", tasks=tasks)


def cmd_course(args: argparse.Namespace) -> dict[str, Any]:
    html = _read(f"course_{args.course_id}")
    page, recognized = parse_course_page(html, args.course_id)
    require_recognized(recognized)
    return envelope(command="course", source="manaba_html", ok=True, status="ok", **page)


def cmd_resource(args: argparse.Namespace) -> dict[str, Any]:
    path_template, suffixes = RESOURCES[args.resource]
    html = _read(path_template.format(id=args.course_id))
    items, recognized = parse_resources(html, args.course_id, suffixes)
    require_recognized(recognized)
    return envelope(
        command=args.resource,
        source="manaba_html",
        ok=True,
        status="ok",
        course_id=args.course_id,
        items=items,
    )


def cmd_grades(args: argparse.Namespace) -> dict[str, Any]:
    html = _read(f"course_{args.course_id}_grade")
    page, recognized = parse_grades(html, args.course_id)
    require_recognized(recognized)
    return envelope(command="grades", source="manaba_html", ok=True, status="ok", **page)


def cmd_portfolio(args: argparse.Namespace) -> dict[str, Any]:
    del args
    html = _read("home_coursetable")
    page, recognized = parse_table_page(html)
    require_recognized(recognized)
    return envelope(command="portfolio", source="manaba_html", ok=True, status="ok", **page)


def cmd_submissions(args: argparse.Namespace) -> dict[str, Any]:
    del args
    html = _read("home_submitlog")
    page, recognized = parse_table_page(html)
    require_recognized(recognized)
    return envelope(command="submissions", source="manaba_html", ok=True, status="ok", **page)


def cmd_download(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.expanduser()
    if output.resolve() == session_path().resolve():
        raise UsageError("不能把下載內容寫進 session 檔。")
    client, path = _open_client()
    try:
        saved = download_file(client, args.target, output, path)
    finally:
        client.close()
    return envelope(command="download", source="manaba_html", ok=True, status="ok", **saved)


def _read(target: str) -> str:
    client, path = _open_client()
    try:
        return fetch_html(client, target, path)
    finally:
        client.close()

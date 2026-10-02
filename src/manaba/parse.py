from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from manaba.errors import LoginFailed

COURSE_HREF = re.compile(r"^course_(\d+)$")
PAGE_HREF = re.compile(r"^page_(\d+)$")
ITEM_HREF = re.compile(
    r"^course_(\d+)_(query|drill|survey|report|news|project|page|topics|grade)_(\d+)$"
)
SECTION_HREF = re.compile(
    r"^course_(\d+)_(query|drill|survey|report|news|project|page|topics|grade)$"
)

EMPTY_COURSE_MARKERS = (
    "コースはありません",
    "該当するコースがありません",
    "表示するコースがありません",
)
EMPTY_TASK_MARKERS = (
    "未提出の課題はありません",
    "課題はありません",
    "該当する課題がありません",
)

KIND_BY_SUFFIX = {
    "report": "report",
    "query": "quiz",
    "drill": "drill",
    "survey": "survey",
    "news": "news",
    "project": "project",
    "page": "contents",
    "topics": "topics",
    "grade": "grade",
}


def normalize(value: str) -> str:
    return " ".join(value.split())


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def href_tail(href: str) -> str:
    path = urlsplit(href.strip()).path
    if not path:
        return href.strip().split("?", 1)[0]
    return path.rstrip("/").split("/")[-1]


def href_key(href: str) -> str:
    parts = urlsplit(href.strip())
    tail = href_tail(href)
    if parts.query:
        return f"{tail}?{parts.query}"
    return tail


def course_marker(href: str, course_id: int) -> bool:
    return re.search(rf"(?:^|[^0-9])c{course_id}(?:[^0-9]|$)", href) is not None


def anchor_text(anchor) -> str:
    text = normalize(" ".join(anchor.stripped_strings))
    if text:
        return text
    image = anchor.find("img")
    if image is not None and image.get("alt"):
        return normalize(image["alt"])
    return ""


def is_logged_in(html: str) -> bool:
    soup = soup_of(html)
    for anchor in soup.select("a[href]"):
        if href_tail(anchor.get("href") or "") == "logout":
            return True
    return False


def page_title(html: str) -> str | None:
    soup = soup_of(html)
    if soup.title is None or not soup.title.string:
        return None
    title = normalize(soup.title.string)
    return title or None


def parse_login_form(html: str) -> dict:
    soup = soup_of(html)
    form = None
    for candidate in soup.find_all("form"):
        password = candidate.find("input", attrs={"type": "password"})
        if password is not None and password.get("name"):
            form = candidate
            break
    if form is None:
        raise LoginFailed("登入頁找不到密碼欄位。manaba 的登入畫面可能已改版。")

    fields: list[tuple[str, str]] = []
    userid_field = None
    password_field = None
    for control in form.find_all("input"):
        name = control.get("name")
        if not name:
            continue
        input_type = (control.get("type") or "text").lower()
        if input_type == "password":
            password_field = name
            continue
        if input_type in {"submit", "button", "image", "reset"}:
            if name == "login":
                fields.append((name, control.get("value") or "ログイン"))
            continue
        if name == "userid" or control.get("id") == "mainuserid":
            userid_field = name
            continue
        fields.append((name, control.get("value") or ""))

    if not userid_field or not password_field:
        raise LoginFailed("登入頁缺少ユーザID或密碼欄位。")
    return {
        "action": form.get("action") or "login",
        "fields": fields,
        "userid_field": userid_field,
        "password_field": password_field,
    }


def parse_courses(html: str) -> tuple[list[dict], bool]:
    soup = soup_of(html)
    found: dict[int, dict] = {}

    for title in soup.select("span.courselist-title"):
        anchor = title.find("a", href=True)
        if anchor is None:
            continue
        match = COURSE_HREF.match(href_tail(anchor["href"]))
        if match is None:
            continue
        course_id = int(match.group(1))
        row = title.find_parent("tr")
        cells = [normalize(cell.get_text(" ", strip=True)) for cell in row.find_all("td")] if row else []
        name = anchor_text(anchor) or (cells[0] if cells else "")
        if not name:
            continue
        found[course_id] = {
            "id": course_id,
            "name": name,
            "year": cells[1] if len(cells) > 1 else None,
            "schedule": cells[2] if len(cells) > 2 else None,
            "teacher": cells[3] if len(cells) > 3 else None,
            "href": f"course_{course_id}",
        }

    for anchor in soup.select("a[href]"):
        match = COURSE_HREF.match(href_tail(anchor["href"]))
        if match is None:
            continue
        course_id = int(match.group(1))
        if course_id in found:
            continue
        name = anchor_text(anchor)
        if not name:
            continue
        found[course_id] = {
            "id": course_id,
            "name": name,
            "year": None,
            "schedule": None,
            "teacher": None,
            "href": f"course_{course_id}",
        }

    text = normalize(soup.get_text(" ", strip=True))
    recognized = bool(found) or soup.select_one(".courselist, span.courselist-title") is not None
    recognized = recognized or any(marker in text for marker in EMPTY_COURSE_MARKERS)
    courses = [found[key] for key in sorted(found)]
    return courses, recognized


def task_kind(label: str, href: str) -> str:
    lowered = f"{label} {href}".lower()
    if "drill" in lowered or "ドリル" in label:
        return "drill"
    if "survey" in lowered or "アンケート" in label:
        return "survey"
    if "report" in lowered or "レポート" in label:
        return "report"
    if "外部教材" in label:
        return "external"
    if "project" in lowered or "プロジェクト" in label:
        return "project"
    if "query" in lowered or "小テスト" in label or "テスト" in label:
        return "quiz"
    return "unknown"


def parse_tasks(html: str) -> tuple[list[dict], bool]:
    soup = soup_of(html)
    tasks: list[dict] = []
    saw_table = soup.select_one("table.stdlist") is not None
    for row in soup.select("table.stdlist tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 3:
            continue
        anchor = cells[1].find("a", href=True)
        if anchor is None:
            continue
        href = href_tail(anchor["href"])
        match = ITEM_HREF.match(href)
        title = anchor_text(anchor)
        if not title:
            continue
        course_id = int(match.group(1)) if match else None
        item_id = int(match.group(3)) if match else None
        suffix = match.group(2) if match else ""
        label = normalize(cells[0].get_text(" ", strip=True))
        course = normalize(cells[2].get_text(" ", strip=True))
        starts_at = normalize(cells[3].get_text(" ", strip=True)) if len(cells) > 3 else ""
        ends_at = normalize(cells[4].get_text(" ", strip=True)) if len(cells) > 4 else ""
        tasks.append(
            {
                "kind": KIND_BY_SUFFIX.get(suffix) or task_kind(label, href),
                "kind_label": label,
                "id": item_id,
                "course_id": course_id,
                "title": title,
                "course": course,
                "starts_at": starts_at or None,
                "ends_at": ends_at or None,
                "href": href,
            }
        )
    text = normalize(soup.get_text(" ", strip=True))
    recognized = bool(tasks) or saw_table or any(marker in text for marker in EMPTY_TASK_MARKERS)
    return tasks, recognized


def parse_resources(html: str, course_id: int, suffixes: tuple[str, ...]) -> tuple[list[dict], bool]:
    soup = soup_of(html)
    allowed = set(suffixes)
    items: list[dict] = []
    seen: set[str] = set()
    saw_table = soup.select_one("table.stdlist") is not None

    def add(anchor, cells: list[str] | None = None) -> None:
        raw = anchor.get("href") or ""
        href = href_key(raw)
        tail = href_tail(raw)
        match = ITEM_HREF.match(tail)
        page_match = PAGE_HREF.match(tail) if "page" in allowed else None
        if match is not None and int(match.group(1)) == course_id and match.group(2) in allowed:
            item_id = int(match.group(3))
            kind = KIND_BY_SUFFIX.get(match.group(2), match.group(2))
        elif page_match is not None and course_marker(raw, course_id):
            item_id = int(page_match.group(1))
            kind = "contents"
        else:
            return
        title = anchor_text(anchor)
        if not title or href in seen:
            return
        seen.add(href)
        items.append(
            {
                "id": item_id,
                "kind": kind,
                "title": title,
                "href": href,
                "cells": cells or [],
            }
        )

    for row in soup.select("table.stdlist tr"):
        cells = [normalize(cell.get_text(" ", strip=True)) for cell in row.find_all("td")]
        anchor = row.find("a", href=True)
        if anchor is not None:
            add(anchor, cells)

    for anchor in soup.select("a[href]"):
        add(anchor)

    text = normalize(soup.get_text(" ", strip=True))
    recognized = bool(items) or saw_table or any(marker in text for marker in EMPTY_TASK_MARKERS)
    return items, recognized


def parse_course_page(html: str, course_id: int) -> tuple[dict, bool]:
    soup = soup_of(html)
    sections: list[dict] = []
    seen: set[str] = set()
    prefix = f"course_{course_id}"
    for anchor in soup.select("a[href]"):
        raw = anchor.get("href") or ""
        href = href_key(raw)
        tail = href_tail(raw)
        title = anchor_text(anchor)
        if not title or href in seen:
            continue
        kind = None
        if tail == prefix or tail.startswith(prefix + "_"):
            match = SECTION_HREF.match(tail) or ITEM_HREF.match(tail)
            if match is not None:
                kind = KIND_BY_SUFFIX.get(match.group(2))
        elif PAGE_HREF.match(tail) and course_marker(raw, course_id):
            kind = "contents"
        else:
            continue
        seen.add(href)
        sections.append({"title": title, "href": href, "kind": kind})
    title = page_title(html)
    recognized = any(section["href"] != prefix for section in sections)
    return {"course_id": course_id, "title": title, "sections": sections}, recognized


def parse_table_page(html: str) -> tuple[dict, bool]:
    soup = soup_of(html)
    rows: list[dict] = []
    for tr in soup.select("table.stdlist tr"):
        cells = [normalize(cell.get_text(" ", strip=True)) for cell in tr.find_all("td")]
        cells = [cell for cell in cells if cell]
        anchor = tr.find("a", href=True)
        if not cells and anchor is None:
            continue
        item: dict = {"cells": cells}
        if anchor is not None:
            title = anchor_text(anchor)
            if title:
                item["title"] = title
            item["href"] = href_key(anchor["href"])
        if item.get("title") or cells:
            rows.append(item)
        if len(rows) >= 200:
            break
    recognized = bool(rows) or soup.select_one("table.stdlist") is not None
    return {"title": page_title(html), "rows": rows}, recognized


def parse_grades(html: str, course_id: int) -> tuple[dict, bool]:
    soup = soup_of(html)
    rows: list[dict] = []
    tables = soup.select("table.stdlist") or [
        table for table in soup.select("table") if table.find("th")
    ]
    for table in tables:
        headers = [normalize(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
        for tr in table.find_all("tr"):
            header_cells = tr.find_all("th")
            cells = [normalize(cell.get_text(" ", strip=True)) for cell in tr.find_all("td")]
            cells = [cell for cell in cells if cell]
            if len(header_cells) == 1 and len(cells) == 1:
                rows.append({"label": normalize(header_cells[0].get_text(" ", strip=True)), "value": cells[0]})
                continue
            if not cells:
                continue
            entry = {"cells": cells}
            if headers and len(headers) == len(cells):
                entry["fields"] = dict(zip(headers, cells))
            rows.append(entry)
            if len(rows) >= 100:
                break
        if len(rows) >= 100:
            break
    recognized = bool(rows) or bool(tables)
    return {"course_id": course_id, "title": page_title(html), "rows": rows}, recognized

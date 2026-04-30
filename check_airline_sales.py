#!/usr/bin/env python3
"""Check ANA/JAL time sale pages and register active sales in Google Calendar.

Run weekly from cron:
    0 4 * * 2  cd /path/to/repo && /path/to/venv/bin/python check_airline_sales.py

Required env vars:
    GCAL_CALENDAR_ID         Calendar ID (Gmail address) to write events to.
    GCAL_OAUTH_CLIENT_FILE   Path to OAuth client_secret.json (default: ./client_secret.json).
    GCAL_TOKEN_FILE          Path to token.json (default: ./token.json).
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

JST = dt.timezone(dt.timedelta(hours=9))
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
SALE_KEYWORDS = (
    "販売期間",
    "申込期間",
    "申し込み期間",
    "受付期間",
    "セール期間",
    "予約期間",
    "ご予約期間",
    "購入期間",
)

log = logging.getLogger("airline_sale_watcher")


@dataclass(frozen=True)
class PageDef:
    key: str
    url: str
    title: str


PAGES: tuple[PageDef, ...] = (
    PageDef(
        "ana_dom",
        "https://www.ana.co.jp/ja/jp/domestic/theme/timesale/sale/",
        "✈ ANAタイムセール開催中（国内線）",
    ),
    PageDef(
        "ana_sv",
        "https://www.ana.co.jp/ja/jp/domestic/theme/timesale/sv/",
        "✈ ANA SUPER VALUE 販売中",
    ),
    PageDef(
        "ana_int",
        "https://www.ana.co.jp/ja/jp/international/theme/special_prj/",
        "✈ ANAタイムセール開催中（国際線）",
    ),
    PageDef(
        "jal_dom",
        "https://www.jal.co.jp/jp/ja/dom/special/timesale/",
        "✈ JALタイムセール開催中（国内線）",
    ),
    PageDef(
        "jal_int",
        "https://www.jal.co.jp/jp/ja/inter/special/sale/",
        "✈ JALタイムセール開催中（国際線）",
    ),
)

# 2025年4月15日 ～ 2025年4月22日 (year may be omitted on the right side)
LONG_RANGE = re.compile(
    r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    r"[^〜～~\-－ー]{0,80}?[〜～~\-－ー]\s*"
    r"(?:(\d{4})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*日"
)
# 2025/4/15 ～ 2025/4/22 (year may be omitted on the right side)
SLASH_RANGE = re.compile(
    r"(\d{4})/(\d{1,2})/(\d{1,2})"
    r"[^〜～~\-－ー]{0,80}?[〜～~\-－ー]\s*"
    r"(?:(\d{4})/)?(\d{1,2})/(\d{1,2})"
)
# 4/15 ～ 4/22 (no year on either side; year is inferred)
SHORT_RANGE = re.compile(
    r"(?<![\d/])(\d{1,2})/(\d{1,2})"
    r"[^〜～~\-－ー\d]{0,40}?[〜～~\-－ー]\s*"
    r"(\d{1,2})/(\d{1,2})(?![\d/])"
)


def _safe_date(year: int, month: int, day: int) -> dt.date | None:
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def _normalize_range(start: dt.date, end: dt.date) -> tuple[dt.date, dt.date]:
    if end < start:
        end = end.replace(year=end.year + 1)
    return start, end


def _windows_around_keywords(text: str) -> list[str]:
    windows: list[str] = []
    for kw in SALE_KEYWORDS:
        for m in re.finditer(re.escape(kw), text):
            start = m.start()
            windows.append(text[start : start + 240])
    return windows


def extract_active_periods(text: str, today: dt.date) -> list[tuple[dt.date, dt.date]]:
    """Return date ranges that include `today`, found near sale-period keywords."""
    found: list[tuple[dt.date, dt.date]] = []
    for window in _windows_around_keywords(text):
        for m in LONG_RANGE.finditer(window):
            y1, mo1, d1, y2, mo2, d2 = m.groups()
            start = _safe_date(int(y1), int(mo1), int(d1))
            end = _safe_date(int(y2) if y2 else int(y1), int(mo2), int(d2))
            if start and end:
                found.append(_normalize_range(start, end))
        for m in SLASH_RANGE.finditer(window):
            y1, mo1, d1, y2, mo2, d2 = m.groups()
            start = _safe_date(int(y1), int(mo1), int(d1))
            end = _safe_date(int(y2) if y2 else int(y1), int(mo2), int(d2))
            if start and end:
                found.append(_normalize_range(start, end))
        for m in SHORT_RANGE.finditer(window):
            mo1, d1, mo2, d2 = m.groups()
            start = _safe_date(today.year, int(mo1), int(d1))
            end = _safe_date(today.year, int(mo2), int(d2))
            if start and end:
                if end < start:
                    end = end.replace(year=end.year + 1)
                if start > today + dt.timedelta(days=180):
                    start = start.replace(year=start.year - 1)
                    if end < start:
                        end = end.replace(year=end.year)
                found.append((start, end))

    # Dedup and keep only ranges containing today.
    return sorted({(s, e) for s, e in found if s <= today <= e})


def fetch_page_text(url: str, timeout: float = 30.0) -> str:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "ja,en;q=0.5"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def build_calendar_service():
    token_file = Path(os.environ.get("GCAL_TOKEN_FILE", "token.json"))
    if not token_file.exists():
        raise SystemExit(
            f"Token file not found: {token_file}. "
            "Run `python init_oauth.py` once to create it."
        )
    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_file.write_text(creds.to_json())
        else:
            raise SystemExit(
                f"Stored credentials are invalid. Re-run `python init_oauth.py`."
            )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def event_already_exists(service, calendar_id: str, page: PageDef, period: tuple[dt.date, dt.date]) -> bool:
    start, end_excl = period[0], period[1] + dt.timedelta(days=1)
    time_min = dt.datetime.combine(start, dt.time.min, JST).isoformat()
    time_max = dt.datetime.combine(end_excl, dt.time.min, JST).isoformat()
    try:
        resp = service.events().list(
            calendarId=calendar_id,
            q=page.title,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            maxResults=20,
        ).execute()
    except HttpError as e:
        log.warning("dedup lookup failed: %s", e)
        return False
    for ev in resp.get("items", []):
        if ev.get("summary") == page.title:
            return True
    return False


def register_event(service, calendar_id: str, page: PageDef, period: tuple[dt.date, dt.date]) -> str | None:
    if event_already_exists(service, calendar_id, page, period):
        log.info("[%s] already registered, skipping", page.key)
        return None
    start, end = period
    body = {
        "summary": page.title,
        "description": f"自動登録: {page.url}\n販売期間: {start} 〜 {end}",
        "start": {"date": start.isoformat()},
        "end": {"date": (end + dt.timedelta(days=1)).isoformat()},
        "transparency": "transparent",
    }
    created = service.events().insert(calendarId=calendar_id, body=body).execute()
    log.info("[%s] created event %s", page.key, created.get("htmlLink"))
    return created.get("id")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    calendar_id = os.environ.get("GCAL_CALENDAR_ID")
    if not calendar_id:
        log.error("GCAL_CALENDAR_ID is not set")
        return 2

    today = dt.datetime.now(JST).date()
    log.info("today (JST): %s", today)
    service = build_calendar_service()

    exit_code = 0
    for page in PAGES:
        log.info("checking %s -> %s", page.key, page.url)
        try:
            text = fetch_page_text(page.url)
        except requests.RequestException as e:
            log.warning("[%s] fetch failed: %s", page.key, e)
            exit_code = 1
            continue

        periods = extract_active_periods(text, today)
        if not periods:
            log.info("[%s] no active sale", page.key)
            continue

        period = max(periods, key=lambda p: p[1])
        log.info("[%s] active sale: %s ~ %s", page.key, period[0], period[1])
        try:
            register_event(service, calendar_id, page, period)
        except HttpError as e:
            log.warning("[%s] calendar insert failed: %s", page.key, e)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

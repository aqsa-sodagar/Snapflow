import json
import re
import sqlite3
import urllib.parse
import uuid
import webbrowser
from datetime import datetime, timedelta

import pyperclip
from dateparser.search import search_dates
from plyer import notification
from pynput import keyboard

DB_FILE = "snapflow_history.db"
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign",
    "utm_term", "utm_content", "fbclid", "gclid", "ref", "si", "igsh"
}

def init_db() -> None:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                action_type TEXT,
                input_text TEXT,
                output_text TEXT
            )
        """)

def log_action(action_type: str, input_text: str, output_text: str) -> None:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO history (timestamp, action_type, input_text, output_text) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action_type, input_text[:300], output_text[:300])
        )

def notify(title: str, message: str) -> None:
    print(f"[{title}] {message}")
    try:
        notification.notify(title=title, message=message, app_name="SnapFlow", timeout=3)
    except Exception:
        pass

def extract_and_clean_url(text: str) -> tuple[str | None, bool]:
    match = re.search(r'https?://[^\s<>"]+', text)
    if not match:
        return None, False
    url = match.group(0).rstrip(".,);]")
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    cleaned_params = [(k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS]
    clean = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(cleaned_params)))
    return clean, len(cleaned_params) < len(query_params)

def format_json(text: str) -> str | None:
    stripped = text.strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return None
    try:
        return json.dumps(json.loads(stripped), indent=2)
    except json.JSONDecodeError:
        return None

def create_calendar_invite(text: str) -> str | None:
    cleaned_text = text.strip()
    if len(cleaned_text) > 250:
        return None
    found = search_dates(cleaned_text, settings={"PREFER_DATES_FROM": "future"})
    if not found:
        return None

    matched_phrase, start_dt = found[0]
    end_dt = start_dt + timedelta(hours=1)
    title = cleaned_text.replace(matched_phrase, "").strip(" -:,.") or "SnapFlow Meeting"

    # 1. Save local .ics file
    ics_content = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//SnapFlow//Action Engine//EN\n"
        "BEGIN:VEVENT\n"
        f"UID:{uuid.uuid4()}@snapflow\n"
        f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%S')}\n"
        f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}\n"
        f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}\n"
        f"SUMMARY:{title}\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    with open("snapflow_event.ics", "w", encoding="utf-8") as f:
        f.write(ics_content)

    # 2. Open pre-filled event directly in Google Calendar
    dates_param = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    gcal_url = (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={urllib.parse.quote(title)}"
        f"&dates={dates_param}"
    )
    webbrowser.open(gcal_url)

    return f"{title} ({start_dt.strftime('%d %b, %I:%M %p')})"

def process_clipboard() -> None:
    raw = pyperclip.paste()
    if not raw or not raw.strip():
        notify("SnapFlow", "Clipboard is empty!")
        return

    # 1. URL Cleaner
    cleaned_url, was_dirty = extract_and_clean_url(raw)
    if cleaned_url:
        pyperclip.copy(cleaned_url)
        log_action("URL_CLEANER", raw, cleaned_url)
        notify("Link Cleaned!", f"Clean link: {cleaned_url}" if was_dirty else "Link is already clean.")
        return

    # 2. JSON Formatter
    formatted = format_json(raw)
    if formatted:
        pyperclip.copy(formatted)
        log_action("JSON_FORMAT", raw, formatted)
        notify("JSON Formatted!", "Clean JSON copied to clipboard.")
        return

    # 3. Auto Calendar Invite
    event_info = create_calendar_invite(raw)
    if event_info:
        log_action("CALENDAR_EVENT", raw, event_info)
        notify("Calendar Event Ready!", event_info)
        return

    notify("SnapFlow", "No link, JSON, or meeting time detected.")

if __name__ == "__main__":
    init_db()
    print("SnapFlow active! Press Ctrl + Shift + Space anywhere...")
    with keyboard.GlobalHotKeys({"<ctrl>+<shift>+<space>": process_clipboard}) as listener:
        listener.join()
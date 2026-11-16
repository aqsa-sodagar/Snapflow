# SnapFlow — Context-Aware Clipboard & Action Engine

SnapFlow is a lightweight, event-driven desktop automation engine for Windows. With a single global hotkey (`Ctrl + Shift + Space`), it inspects clipboard contents, classifies the data type, executes the appropriate workflow, and logs every action to a local SQLite database.

## Key Features
* **Tracking URL Sanitizer:** Extracts links from copied text and strips tracking parameters (`utm_*`, `fbclid`, `gclid`, `ref`, `si`) in place.
* **Instant JSON Pretty-Printer:** Detects minified JSON payloads and formats them cleanly back to the clipboard.
* **Natural-Language Calendar Generator:** Parses dates and times from copied messages (e.g., *"Team meeting tomorrow at 4pm"*), generates a standard `.ics` file, and opens a pre-filled Google Calendar event in the browser.
* **SQLite Audit Trail:** Logs timestamps, action categories, and outputs locally (`snapflow_history.db`) with a CLI log viewer (`history.py`).
* **Zero-Polling Architecture:** Uses OS-level global keyboard hooks (`pynput`) so background CPU usage remains near 0% while idle.

## Architecture

```mermaid
flowchart LR
    A[Global Hotkey: Ctrl+Shift+Space] --> B[Clipboard Reader]
    B --> C{Content Classifier}
    C -->|URL with Trackers| D[Strip UTM/Tracking Params]
    C -->|Minified JSON| E[Format & Indent JSON]
    C -->|Date/Time Text| F[Generate .ics & Open Google Calendar]
    D & E & F --> G[Desktop Notification + SQLite Logger]
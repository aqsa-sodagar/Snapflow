import sqlite3

DB_FILE = "snapflow_history.db"

def show_history(limit: int = 15) -> None:
    try:
        with sqlite3.connect(DB_FILE) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, action_type, output_text FROM history ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
    except sqlite3.OperationalError:
        print("No history found yet. Run app.py and trigger Ctrl + Shift + Space first.")
        return

    if not rows:
        print("History table is empty.")
        return

    print(f"\n{'ID':<4} | {'Timestamp':<19} | {'Action':<15} | Output")
    print("-" * 75)
    for row_id, ts, action, output in rows:
        clean_out = output.replace("\n", " ")[:40]
        print(f"{row_id:<4} | {ts:<19} | {action:<15} | {clean_out}")
    print()

if __name__ == "__main__":
    show_history()
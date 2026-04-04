"""
One-time migration script to shift all existing UTC timestamps to GMT+7.
Adds 7 hours to every timestamp column in the database.

Usage (run inside the backend container):
    python migrate_timestamps.py
"""

import sqlite3
import sys

# Map of table -> list of timestamp columns to migrate
TIMESTAMP_COLUMNS = {
    "users": ["created_at"],
    "sessions": ["created_at", "expires_at"],
    "rules": ["created_at"],
    "rule_signatures": ["signed_at"],
    "questions": ["created_at"],
    "answers": ["created_at"],
    "milestones": ["created_at"],
    "milestone_approvals": ["approved_at"],
    "talks": ["created_at"],
    "talk_notes": ["created_at"],
}

DB_PATH = "./data/verse.db"


def migrate(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table, columns in TIMESTAMP_COLUMNS.items():
        for col in columns:
            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            if not cursor.fetchone():
                print(f"  SKIP  {table}.{col} (table does not exist)")
                continue

            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL")
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"  SKIP  {table}.{col} (no rows)")
                continue

            # Show a sample before
            cursor.execute(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 1")
            sample_before = cursor.fetchone()[0]

            # Add 7 hours
            cursor.execute(
                f"UPDATE {table} SET {col} = datetime({col}, '+7 hours') WHERE {col} IS NOT NULL"
            )

            # Show a sample after
            cursor.execute(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 1")
            sample_after = cursor.fetchone()[0]

            print(f"  OK    {table}.{col} — {count} row(s) updated ({sample_before} -> {sample_after})")

    conn.commit()
    conn.close()
    print("\nDone! All timestamps shifted from UTC to GMT+7.")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    print(f"Migrating timestamps in: {db_path}\n")
    migrate(db_path)

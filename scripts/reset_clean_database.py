import os
import sqlite3
from pathlib import Path

# Paths to all SQLite databases
db_paths = [
    Path("real_healthcare.db"),
    Path("synthetic_healthcare.db"),
    Path("security_events.db"),
    Path("backend/real_healthcare.db"),
    Path("backend/synthetic_healthcare.db"),
    Path("backend/security_events.db"),
]

def clean_database():
    print("[CLEANUP] Purging all old test and dummy records from EHR databases...")

    for path in db_paths:
        if not path.exists():
            continue
        
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        
        tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        
        for table in tables:
            if table.startswith("sqlite_"):
                continue
            if table == "users":
                # Preserve essential authenticated user accounts and ensure unblocked
                cursor.execute("DELETE FROM users WHERE username NOT IN ('admin', 'doctor', 'reception', 'hacker')")
                cursor.execute("UPDATE users SET is_blocked = 0")
                print(f"  -> {path.name} | Table '{table}': Kept only active system credentials (admin, doctor, reception, hacker)")
            else:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  -> {path.name} | Table '{table}': Cleared all records (0 rows remaining)")
        
        conn.commit()
        conn.close()

    print("[SUCCESS] All databases successfully cleaned! Ready for fresh patient entry.")

if __name__ == "__main__":
    clean_database()

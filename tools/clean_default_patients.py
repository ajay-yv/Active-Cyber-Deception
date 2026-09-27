"""Remove all default and test patient records from the EHR databases."""

import sqlite3
from pathlib import Path

def clean_databases() -> None:
    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    root_dir = Path(__file__).resolve().parents[1]

    # Clean real healthcare DBs
    for path in [backend_dir / "real_healthcare.db", root_dir / "real_healthcare.db"]:
        if path.exists():
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("DELETE FROM patients")
            cur.execute("DELETE FROM patient_history")
            conn.commit()
            conn.close()
            print(f"[CLEANED] Removed all patients and history from {path}")

    # Clean synthetic healthcare DBs
    for path in [backend_dir / "synthetic_healthcare.db", root_dir / "synthetic_healthcare.db"]:
        if path.exists():
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("DELETE FROM synthetic_patients")
            conn.commit()
            conn.close()
            print(f"[CLEANED] Removed all synthetic twin records from {path}")

    # Clean patient watermarks from security DB
    for path in [backend_dir / "security_events.db", root_dir / "security_events.db"]:
        if path.exists():
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("DELETE FROM watermarks WHERE source_type IN ('patient', 'synthetic')")
            conn.commit()
            conn.close()
            print(f"[CLEANED] Removed all patient watermarks from {path}")

if __name__ == "__main__":
    clean_databases()

import sqlite3
from pathlib import Path

backend_dir = Path(__file__).resolve().parent

# Clean real DB
for db_name in ["real_healthcare.db", "../real_healthcare.db"]:
    p = backend_dir / db_name
    if p.exists():
        conn = sqlite3.connect(p)
        conn.execute("DELETE FROM patients WHERE id != 'P-01'")
        conn.execute("DELETE FROM patient_history")
        conn.commit()
        conn.close()

# Clean synthetic DB
for db_name in ["synthetic_healthcare.db", "../synthetic_healthcare.db"]:
    p = backend_dir / db_name
    if p.exists():
        conn = sqlite3.connect(p)
        conn.execute("DELETE FROM synthetic_patients WHERE real_patient_id != 'P-01'")
        conn.commit()
        conn.close()

print("Sanitization complete. Only original patient P-01 remains.")

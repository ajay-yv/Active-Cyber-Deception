import sqlite3
import os

base_dirs = [
    r"c:\Users\ajayy\OneDrive\Desktop\EHR",
    r"c:\Users\ajayy\OneDrive\Desktop\EHR\backend",
]

for d in base_dirs:
    synth_db = os.path.join(d, "synthetic_healthcare.db")
    if os.path.exists(synth_db):
        try:
            conn = sqlite3.connect(synth_db)
            cur = conn.cursor()
            cur.execute("DELETE FROM synthetic_patients WHERE real_patient_id != 'P-01' AND id != 'SYN-01'")
            conn.commit()
            remaining = cur.execute("SELECT id, real_patient_id, name FROM synthetic_patients").fetchall()
            conn.close()
            print(f"Remaining in {synth_db}: {remaining}")
        except Exception as e:
            print(f"Skipping synth_db {synth_db}: {e}")

import sys
import traceback
from pathlib import Path
import sqlite3

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

from app.services.watermark import create_watermark, _generate_watermark_fingerprint, _generate_watermark_text

def backfill():
    db_path = root / "real_healthcare.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    rows = cursor.execute("SELECT id, name, age, disease, diagnosis, medicines, treatment_pattern, watermark_fingerprint FROM patients").fetchall()
    print(f"Total patient rows: {len(rows)}")
    
    for row in rows:
        p_id, name, age, disease, diagnosis, medicines_raw, treatment_pattern, wm_fp = row
        if not wm_fp:
            print(f"Fixing watermark for {name} ({p_id})...")
            import json
            try:
                medicines = json.loads(medicines_raw) if medicines_raw else []
            except Exception:
                medicines = []
            
            source_data = {
                "name": name,
                "age": age,
                "disease": disease,
                "diagnosis": diagnosis,
                "medicines": medicines,
                "treatment_pattern": treatment_pattern,
            }
            wm = create_watermark(p_id, "real", "HOSPITAL-001", "bootstrap", source_data)
            cursor.execute(
                "UPDATE patients SET watermark_id=?, watermark_text=?, watermark_fingerprint=? WHERE id=?",
                (wm.watermark_id, wm.watermark_text, wm.watermark_fingerprint, p_id)
            )
            print(f"Updated {name}: fp={wm.watermark_fingerprint}")
            
    conn.commit()
    conn.close()
    print("Backfill complete!")

if __name__ == "__main__":
    try:
        backfill()
    except Exception as e:
        traceback.print_exc()

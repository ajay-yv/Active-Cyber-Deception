import sys
from pathlib import Path
from sqlalchemy import text

root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir / "backend"))

from app.db.engines import get_real_engine, get_synthetic_engine, get_security_engine
from app.db.bootstrap import _ensure_default_users

def reset_to_zero():
    print("[1/3] Clearing all patient, twin, watermark, and audit records...")
    
    # Real DB tables
    real_engine = get_real_engine()
    with real_engine.begin() as conn:
        for table in ["patients"]:
            conn.execute(text(f"DELETE FROM {table}"))
            print(f"  - Cleared real DB table: {table}")

    # Synthetic DB tables
    syn_engine = get_synthetic_engine()
    with syn_engine.begin() as conn:
        for table in ["synthetic_patients", "honeytokens"]:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
                print(f"  - Cleared synthetic DB table: {table}")
            except Exception:
                pass

    # Security DB tables
    sec_engine = get_security_engine()
    with sec_engine.begin() as conn:
        for table in ["audit_logs", "security_events", "login_logs", "attack_logs", "ai_decisions", "watermarks"]:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
                print(f"  - Cleared security DB table: {table}")
            except Exception:
                pass

    print("[2/3] Resetting default accounts and unblocking users...")
    _ensure_default_users()
    print("[3/3] Platform reset to ZERO state successfully!")

if __name__ == "__main__":
    reset_to_zero()

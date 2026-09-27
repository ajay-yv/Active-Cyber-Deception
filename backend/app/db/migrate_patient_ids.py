import os
import sqlite3
import re

def migrate_db_file(real_db_path, synth_db_path, sec_db_path):
    if not os.path.exists(real_db_path):
        print(f"Skipping migration for {real_db_path} (file not found)")
        return

    print(f"Migrating database cluster: {real_db_path}...")

    # 1. Migrate Real Patients and Patient History
    conn_real = sqlite3.connect(real_db_path)
    cur_real = conn_real.cursor()

    id_map = {}
    next_num = 1

    # Fetch active patients sorted by created_at / rowid
    cur_real.execute("SELECT id, patient_id, created_at FROM patients ORDER BY created_at ASC, rowid ASC")
    active_rows = cur_real.fetchall()

    for old_id, pid, created_at in active_rows:
        if old_id and old_id.startswith("P-") and not (len(old_id) == 36 and "-" in old_id[5:]):
            # Already formatted like P-01
            m = re.match(r"^P-(\d+)$", old_id, re.IGNORECASE)
            if m:
                seq = int(m.group(1))
                next_num = max(next_num, seq + 1)
                id_map[old_id] = old_id
                continue

        new_p_id = f"P-{next_num:02d}" if next_num < 100 else f"P-{next_num}"
        id_map[old_id] = new_p_id
        cur_real.execute(
            "UPDATE patients SET id = ?, patient_id = ? WHERE id = ?",
            (new_p_id, next_num, old_id)
        )
        next_num += 1

    # Fetch history / archived patients
    cur_real.execute("SELECT id, patient_id FROM patient_history ORDER BY rowid ASC")
    hist_rows = cur_real.fetchall()

    for old_id, pid in hist_rows:
        if old_id in id_map:
            new_p_id = id_map[old_id]
            m = re.match(r"^P-(\d+)$", new_p_id, re.IGNORECASE)
            seq = int(m.group(1)) if m else pid
            cur_real.execute(
                "UPDATE patient_history SET id = ?, patient_id = ? WHERE id = ?",
                (new_p_id, seq, old_id)
            )
        else:
            if old_id and old_id.startswith("P-"):
                m = re.match(r"^P-(\d+)$", old_id, re.IGNORECASE)
                if m:
                    seq = int(m.group(1))
                    next_num = max(next_num, seq + 1)
                    id_map[old_id] = old_id
                    continue

            new_p_id = f"P-{next_num:02d}" if next_num < 100 else f"P-{next_num}"
            id_map[old_id] = new_p_id
            cur_real.execute(
                "UPDATE patient_history SET id = ?, patient_id = ? WHERE id = ?",
                (new_p_id, next_num, old_id)
            )
            next_num += 1

    conn_real.commit()
    conn_real.close()

    # 2. Migrate Synthetic Patients
    if os.path.exists(synth_db_path):
        conn_synth = sqlite3.connect(synth_db_path)
        cur_synth = conn_synth.cursor()

        cur_synth.execute("SELECT id, real_patient_id FROM synthetic_patients")
        synth_rows = cur_synth.fetchall()

        for old_syn_id, old_real_id in synth_rows:
            new_real_id = id_map.get(old_real_id, old_real_id)
            if new_real_id.startswith("P-"):
                num_part = new_real_id[2:]
                new_syn_id = f"SYN-{num_part}"
            else:
                new_syn_id = old_syn_id

            cur_synth.execute(
                "UPDATE synthetic_patients SET id = ?, real_patient_id = ? WHERE id = ?",
                (new_syn_id, new_real_id, old_syn_id)
            )

        conn_synth.commit()
        conn_synth.close()

    # 3. Migrate Security Events & Watermarks
    if os.path.exists(sec_db_path):
        conn_sec = sqlite3.connect(sec_db_path)
        cur_sec = conn_sec.cursor()

        cur_sec.execute("SELECT watermark_id, source_id FROM watermarks")
        wm_rows = cur_sec.fetchall()
        for wm_id, src_id in wm_rows:
            if src_id in id_map:
                new_src = id_map[src_id]
                cur_sec.execute("UPDATE watermarks SET source_id = ? WHERE watermark_id = ?", (new_src, wm_id))

        cur_sec.execute("SELECT id, target_patient_id, session_id FROM breach_logs")
        blog_rows = cur_sec.fetchall()
        for blog_id, target_pid, sess in blog_rows:
            if target_pid in id_map:
                new_target = id_map[target_pid]
                cur_sec.execute("UPDATE breach_logs SET target_patient_id = ? WHERE id = ?", (new_target, blog_id))

        conn_sec.commit()
        conn_sec.close()

    print(f"Successfully migrated {real_db_path}! ID mappings: {id_map}")

if __name__ == "__main__":
    migrate_db_file("backend/real_healthcare.db", "backend/synthetic_healthcare.db", "backend/security_events.db")
    migrate_db_file("real_healthcare.db", "synthetic_healthcare.db", "security_events.db")

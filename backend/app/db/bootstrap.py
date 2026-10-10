from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.db.engines import get_real_engine, get_security_engine, get_synthetic_engine
from app.db.base import RealBase, SecurityBase, SyntheticBase

# Import models so SQLAlchemy registers them on the correct metadata objects.
from app.models import real as real_models  # noqa: F401
from app.models import security as security_models  # noqa: F401
from app.models import synthetic as synthetic_models  # noqa: F401


def create_all_tables() -> None:
    RealBase.metadata.create_all(bind=get_real_engine())
    SyntheticBase.metadata.create_all(bind=get_synthetic_engine())
    SecurityBase.metadata.create_all(bind=get_security_engine())
    _ensure_users_block_column()
    _ensure_users_email_column()
    _ensure_users_patient_record_column()
    _ensure_default_users()
    _ensure_real_patient_watermark_columns()
    _ensure_synthetic_watermark_column()
    _ensure_synthetic_real_patient_unique_index()
    _ensure_watermark_source_columns()
    _ensure_watermark_unique_index()
    _ensure_password_reset_token_schema()
    _ensure_honeytoken_schema()
    _ensure_security_created_at_columns()
    _ensure_ai_decision_schema()
    _ensure_forensic_records_schema()


def _ensure_real_patient_watermark_columns() -> None:
    engine = get_real_engine()
    inspector = inspect(engine)
    if "patients" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("patients")}
    with engine.begin() as connection:
        if "watermark_id" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN watermark_id VARCHAR(128) NOT NULL DEFAULT ''"))
        if "watermark_text" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN watermark_text VARCHAR(255) NOT NULL DEFAULT ''"))
        if "watermark_fingerprint" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN watermark_fingerprint VARCHAR(128) NOT NULL DEFAULT ''"))
        if "gender" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN gender VARCHAR(32) NOT NULL DEFAULT ''"))
        if "date_of_birth" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN date_of_birth VARCHAR(32) NOT NULL DEFAULT ''"))
        if "blood_group" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN blood_group VARCHAR(8) NOT NULL DEFAULT ''"))
        if "phone" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN phone VARCHAR(64) NOT NULL DEFAULT ''"))
        if "email" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT ''"))
        if "address" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN address TEXT NOT NULL DEFAULT ''"))
        if "aadhaar" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN aadhaar VARCHAR(64) NOT NULL DEFAULT ''"))
        if "emergency_contact" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN emergency_contact VARCHAR(255) NOT NULL DEFAULT ''"))
        if "symptoms" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN symptoms TEXT NOT NULL DEFAULT ''"))
        if "allergies" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN allergies TEXT NOT NULL DEFAULT ''"))
        if "dosages" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN dosages TEXT NOT NULL DEFAULT ''"))
        if "doctor_assigned" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN doctor_assigned VARCHAR(255) NOT NULL DEFAULT ''"))
        if "department" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN department VARCHAR(255) NOT NULL DEFAULT ''"))
        if "admission_date" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN admission_date VARCHAR(32) NOT NULL DEFAULT ''"))
        if "discharge_date" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN discharge_date VARCHAR(32) NOT NULL DEFAULT ''"))
        if "lab_reports" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN lab_reports TEXT NOT NULL DEFAULT '[]'"))
        if "medical_images" not in columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN medical_images TEXT NOT NULL DEFAULT '[]'"))

        patient_id_present = "patient_id" in columns
        if not patient_id_present:
            try:
                connection.execute(text("ALTER TABLE patients ADD COLUMN patient_id INTEGER NOT NULL DEFAULT 0"))
                patient_id_present = True
            except OperationalError:
                # Column may already exist if a previous schema migration was applied.
                columns = {column["name"] for column in inspector.get_columns("patients")}
                patient_id_present = "patient_id" in columns

        if patient_id_present:
            connection.execute(text("UPDATE patients SET patient_id = rowid WHERE patient_id = 0"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_patients_patient_id ON patients(patient_id)"))


def _ensure_synthetic_watermark_column() -> None:
    engine = get_synthetic_engine()
    inspector = inspect(engine)
    if "synthetic_patients" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("synthetic_patients")}
    with engine.begin() as connection:
        if "name" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT ''"))
        if "address" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN address TEXT NOT NULL DEFAULT ''"))
        if "phone_number" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN phone_number VARCHAR(32) NOT NULL DEFAULT ''"))
        if "aadhaar_number" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN aadhaar_number VARCHAR(32) NOT NULL DEFAULT ''"))
        if "email" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT ''"))
        if "blood_group" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN blood_group VARCHAR(8) NOT NULL DEFAULT ''"))
        if "doctor_assigned" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN doctor_assigned VARCHAR(255) NOT NULL DEFAULT ''"))
        if "department" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN department VARCHAR(255) NOT NULL DEFAULT ''"))
        if "ward" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN ward VARCHAR(64) NOT NULL DEFAULT ''"))
        if "admission_date" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN admission_date VARCHAR(32) NOT NULL DEFAULT ''"))
        if "discharge_date" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN discharge_date VARCHAR(32) NOT NULL DEFAULT ''"))
        if "insurance_id" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN insurance_id VARCHAR(64) NOT NULL DEFAULT ''"))
        if "insurance_details" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN insurance_details VARCHAR(255) NOT NULL DEFAULT ''"))
        if "emergency_contact" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN emergency_contact VARCHAR(64) NOT NULL DEFAULT ''"))
        if "disease" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN disease VARCHAR(255) NOT NULL DEFAULT ''"))
        if "diagnosis" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN diagnosis TEXT NOT NULL DEFAULT ''"))
        if "medicines" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN medicines TEXT NOT NULL DEFAULT '[]'"))
        if "treatment_pattern" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN treatment_pattern VARCHAR(255) NOT NULL DEFAULT ''"))
        if "age_range" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN age_range VARCHAR(32) NOT NULL DEFAULT ''"))
        if "watermark_fingerprint" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN watermark_fingerprint VARCHAR(128) NOT NULL DEFAULT ''"))
        if "hospital_id" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN hospital_id VARCHAR(64) NOT NULL DEFAULT ''"))
        if "gender" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN gender VARCHAR(32) NOT NULL DEFAULT 'Male'"))
        if "date_of_birth" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN date_of_birth VARCHAR(32) NOT NULL DEFAULT ''"))
        if "symptoms" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN symptoms TEXT NOT NULL DEFAULT '[]'"))
        if "allergies" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN allergies TEXT NOT NULL DEFAULT '[]'"))
        if "dosages" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN dosages TEXT NOT NULL DEFAULT '[]'"))
        if "lab_reports" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN lab_reports TEXT NOT NULL DEFAULT '[]'"))
        if "medical_images" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN medical_images TEXT NOT NULL DEFAULT '[]'"))
        if "is_attractive_lure" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN is_attractive_lure INTEGER NOT NULL DEFAULT 0"))
        if "lure_type" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN lure_type VARCHAR(64) NOT NULL DEFAULT 'standard'"))
        if "created_at" not in columns:
            connection.execute(text("ALTER TABLE synthetic_patients ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))


def _ensure_synthetic_real_patient_unique_index() -> None:
    engine = get_synthetic_engine()
    inspector = inspect(engine)
    if "synthetic_patients" not in inspector.get_table_names():
        return
    with engine.begin() as connection:
        # Remove duplicate synthetic records for the same real patient before enforcing uniqueness.
        connection.execute(text(
            "DELETE FROM synthetic_patients WHERE rowid NOT IN ("
            "SELECT MAX(rowid) FROM synthetic_patients GROUP BY real_patient_id"
            ")"
        ))
        try:
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_synthetic_patients_real_patient_id ON synthetic_patients(real_patient_id)"))
        except OperationalError:
            # If duplicates remain due to sqlite quirks, ignore and continue.
            pass


def _ensure_watermark_source_columns() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "watermarks" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("watermarks")}

    if "twin_id" in columns:
        with engine.begin() as connection:
            connection.execute(text(
                "CREATE TABLE watermarks_new ("
                "id VARCHAR(64) PRIMARY KEY, "
                "watermark_id VARCHAR(64) NOT NULL, "
                "source_id VARCHAR(64) NOT NULL DEFAULT '', "
                "source_type VARCHAR(32) NOT NULL DEFAULT 'synthetic', "
                "hospital_id VARCHAR(64) NOT NULL, "
                "timestamp VARCHAR(64) NOT NULL, "
                "session_id VARCHAR(64) NOT NULL, "
                "watermark_text VARCHAR(255) NOT NULL DEFAULT '', "
                "watermark_fingerprint VARCHAR(128) NOT NULL DEFAULT ''"
                ")"
            ))
            connection.execute(text(
                "INSERT INTO watermarks_new (id, watermark_id, source_id, source_type, hospital_id, timestamp, session_id, watermark_text, watermark_fingerprint) "
                "SELECT id, watermark_id, twin_id, 'synthetic', hospital_id, timestamp, session_id, '', '' FROM watermarks"
            ))
            connection.execute(text("DROP TABLE watermarks"))
            connection.execute(text("ALTER TABLE watermarks_new RENAME TO watermarks"))
        columns = {column["name"] for column in inspector.get_columns("watermarks")}

    with engine.begin() as connection:
        try:
            if "source_id" not in columns:
                connection.execute(text("ALTER TABLE watermarks ADD COLUMN source_id VARCHAR(64) NOT NULL DEFAULT ''"))
            if "source_type" not in columns:
                connection.execute(text("ALTER TABLE watermarks ADD COLUMN source_type VARCHAR(32) NOT NULL DEFAULT 'synthetic'"))
            if "watermark_text" not in columns:
                connection.execute(text("ALTER TABLE watermarks ADD COLUMN watermark_text VARCHAR(255) NOT NULL DEFAULT ''"))
            if "watermark_fingerprint" not in columns:
                connection.execute(text("ALTER TABLE watermarks ADD COLUMN watermark_fingerprint VARCHAR(128) NOT NULL DEFAULT ''"))
        except OperationalError:
            # If columns already exist (race or previous migration), ignore and continue
            pass


def _ensure_watermark_unique_index() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "watermarks" not in inspector.get_table_names():
        return
    with engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM watermarks WHERE rowid NOT IN ("
            "SELECT MAX(rowid) FROM watermarks GROUP BY source_id, source_type"
            ")"
        ))
        try:
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_watermarks_source_id_source_type ON watermarks(source_id, source_type)"))
        except OperationalError:
            pass


def _ensure_password_reset_token_schema() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    table_exists = "password_reset_tokens" in inspector.get_table_names()
    with engine.begin() as connection:
        if not table_exists:
            connection.execute(
                text(
                    "CREATE TABLE password_reset_tokens ("
                    "id VARCHAR(64) PRIMARY KEY, "
                    "username VARCHAR(128) NOT NULL, "
                    "email VARCHAR(255) NOT NULL, "
                    "token_hash VARCHAR(128) NOT NULL, "
                    "expires_at DATETIME NOT NULL, "
                    "used INTEGER NOT NULL DEFAULT 0, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
        else:
            columns = {column["name"] for column in inspector.get_columns("password_reset_tokens")}
            if "username" not in columns:
                connection.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN username VARCHAR(128) NOT NULL DEFAULT ''"))
            if "email" not in columns:
                connection.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT ''"))
            if "token_hash" not in columns:
                connection.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN token_hash VARCHAR(128) NOT NULL DEFAULT ''"))
            if "expires_at" not in columns:
                connection.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN expires_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
            if "used" not in columns:
                connection.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN used INTEGER NOT NULL DEFAULT 0"))
            if "created_at" not in columns:
                connection.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)"))


def _ensure_honeytoken_schema() -> None:
    engine = get_synthetic_engine()
    inspector = inspect(engine)
    if "honeytokens" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("honeytokens")}
    with engine.begin() as connection:
        if "session_id" not in columns:
            connection.execute(text("ALTER TABLE honeytokens ADD COLUMN session_id VARCHAR(64) NOT NULL DEFAULT ''"))
        if "twin_id" not in columns:
            connection.execute(text("ALTER TABLE honeytokens ADD COLUMN twin_id VARCHAR(64) NOT NULL DEFAULT ''"))


def _ensure_security_created_at_columns() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    tables = ["audit_logs", "security_events", "login_logs", "attack_logs", "ai_decisions"]
    for table in tables:
        if table not in inspector.get_table_names():
            continue
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "created_at" not in columns:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))


def _ensure_ai_decision_schema() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "ai_decisions" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("ai_decisions")}
    with engine.begin() as connection:
        if "action" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN action VARCHAR(128) NOT NULL DEFAULT 'allow'"))
        if "reason" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN reason TEXT NOT NULL DEFAULT ''"))
        if "anomaly_score" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN anomaly_score FLOAT NOT NULL DEFAULT 0.0"))
        if "anomaly_flag" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN anomaly_flag INTEGER NOT NULL DEFAULT 0"))
        if "random_forest_label" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN random_forest_label VARCHAR(64) NOT NULL DEFAULT 'normal'"))
        if "random_forest_confidence" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN random_forest_confidence FLOAT NOT NULL DEFAULT 0.0"))
        if "attack_probability" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN attack_probability FLOAT NOT NULL DEFAULT 0.0"))
        if "xgboost_confidence" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN xgboost_confidence FLOAT NOT NULL DEFAULT 0.0"))
        if "risk_score" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN risk_score FLOAT NOT NULL DEFAULT 0.0"))
        if "attacker_ip" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN attacker_ip VARCHAR(64) NOT NULL DEFAULT ''"))
        if "user_agent" not in columns:
            connection.execute(text("ALTER TABLE ai_decisions ADD COLUMN user_agent VARCHAR(128) NOT NULL DEFAULT ''"))


def _ensure_users_block_column() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_blocked" in columns:
        return
    with engine.begin() as connection:
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0"))
        except OperationalError:
            pass


def _ensure_users_email_column() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" in columns:
        return
    with engine.begin() as connection:
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255) DEFAULT NULL"))
        except OperationalError:
            pass


def _ensure_users_patient_record_column() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "patient_record_id" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN patient_record_id VARCHAR(36) NULL"))
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_patient_record_id "
            "ON users(patient_record_id)"
        ))


def _ensure_default_users() -> None:
    # Seed default users in the security database if they don't exist
    from app.db.engines import SecuritySessionLocal
    from app.core.users import hash_password, verify_password
    from app.models.security import UserAccount

    defaults = [
        ("admin", "Admin@8431", "administrator", "System Administrator", "admin@stjude.org"),
        ("doctor", "Priya@10", "doctor", "Dr. Priya Nair (Cardiology)", "doctor@stjude.org"),
        ("doctor_priya", "Priya@10", "doctor", "Dr. Priya Nair (Cardiology)", "priya@stjude.org"),
        ("doctor_ramesh", "Ramesh@29", "doctor", "Dr. Ramesh Kumar (Neurology)", "ramesh@stjude.org"),
        ("doctor_sarah", "Sarah@38", "doctor", "Dr. Sarah Jenkins (Pediatrics)", "sarah@stjude.org"),
        ("doctor_rajesh", "Rajesh@47", "doctor", "Dr. Rajesh Patel (Orthopedics)", "rajesh@stjude.org"),
        ("doctor_anita", "Anita@56", "doctor", "Dr. Anita Sharma (General Medicine)", "anita@stjude.org"),
        ("patient", "Patient@1432", "patient", "Patient User", "patient@stjude.org"),
        ("reception", "reception123", "receptionist", "Reception Desk", "reception@stjude.org"),
        ("hacker", "hacker123", "hacker", "Simulated Attacker", "hacker@stjude.org"),
    ]

    with SecuritySessionLocal() as session:
        for username, pwd, role, full_name, email in defaults:
            existing = session.query(UserAccount).filter(UserAccount.username == username).first()
            if existing is None:
                session.add(UserAccount(username=username, password_hash=hash_password(pwd), role=role, full_name=full_name, email=email, is_blocked=False))
            else:
                if not existing.password_hash or not verify_password(pwd, existing.password_hash):
                    if username == "admin":
                        existing.password_hash = hash_password(pwd)
                    elif username in ("doctor", "doctor_priya", "doctor_ramesh", "doctor_sarah", "doctor_rajesh", "doctor_anita"):
                        existing.password_hash = hash_password(pwd)
                existing.email = existing.email or email
                existing.is_blocked = False
                session.add(existing)
        session.commit()


def _ensure_forensic_records_schema() -> None:
    engine = get_security_engine()
    inspector = inspect(engine)
    if "forensic_records" not in inspector.get_table_names():
        from app.models.security import ForensicAttackRecord
        ForensicAttackRecord.__table__.create(bind=engine, checkfirst=True)
        return
    columns = {column["name"] for column in inspector.get_columns("forensic_records")}
    with engine.begin() as connection:
        if "attack_probability" not in columns:
            connection.execute(text("ALTER TABLE forensic_records ADD COLUMN attack_probability FLOAT DEFAULT 0.0"))
        if "records_returned" not in columns:
            connection.execute(text("ALTER TABLE forensic_records ADD COLUMN records_returned INTEGER DEFAULT 0"))
        if "blocked_status" not in columns:
            connection.execute(text("ALTER TABLE forensic_records ADD COLUMN blocked_status INTEGER NOT NULL DEFAULT 0"))


def _ensure_default_patients() -> None:
    """Ensure at least one real patient exists with a corresponding synthetic twin for 1:1 parity."""
    try:
        from app.db.engines import RealSessionLocal
        from app.models.real import RealPatient
        from app.schemas import PatientCreate
        from app.services.patients import PatientService
        from app.services.twin import twin_generator_proxy

        # Default patients are not pre-seeded; created dynamically by Admin
        pass
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Bootstrap patient check error: %s", exc)




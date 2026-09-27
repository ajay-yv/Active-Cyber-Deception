import json
from hashlib import sha256
from dataclasses import dataclass, field

from app.db.engines import SyntheticSessionLocal
from app.models.synthetic import SyntheticPatient
from app.schemas import TwinRecord


@dataclass(frozen=True)
class SyntheticForensicRecord:
    synthetic_patient_id: str
    watermark_fingerprint: str
    name: str
    disease: str
    diagnosis: str
    treatment_pattern: str
    age_range: str
    aadhaar_number: str
    phone_number: str
    email: str
    address: str
    insurance_details: str
    emergency_contact: str
    real_patient_id: str = ""
    gender: str = "Male"
    date_of_birth: str = ""
    blood_group: str = "O+"
    doctor_assigned: str = ""
    department: str = ""
    ward: str = ""
    admission_date: str = ""
    discharge_date: str = ""
    symptoms: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    medicines: list[str] = field(default_factory=list)
    dosages: list[str] = field(default_factory=list)
    lab_reports: list[str] = field(default_factory=list)
    medical_images: list[str] = field(default_factory=list)
    is_attractive_lure: bool = False
    lure_type: str = "standard"


def _safe_json_loads(val: object, default: list) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.strip():
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return [val] if val else default
    return default


def _to_record(row: SyntheticPatient) -> TwinRecord:
    return TwinRecord(
        real_patient_id=row.real_patient_id,
        synthetic_patient_id=row.id,
        name=row.name,
        address=row.address,
        phone_number=row.phone_number,
        aadhaar_number=row.aadhaar_number,
        email=row.email,
        gender=getattr(row, "gender", "Male") or "Male",
        date_of_birth=getattr(row, "date_of_birth", "") or "",
        blood_group=getattr(row, "blood_group", "O+") or "O+",
        doctor_assigned=getattr(row, "doctor_assigned", "") or "",
        department=getattr(row, "department", "") or "",
        ward=getattr(row, "ward", "") or "",
        admission_date=getattr(row, "admission_date", "") or "",
        discharge_date=getattr(row, "discharge_date", "") or "",
        insurance_details=row.insurance_details,
        emergency_contact=row.emergency_contact,
        disease=row.disease,
        diagnosis=row.diagnosis,
        symptoms=_safe_json_loads(getattr(row, "symptoms", "[]"), []),
        allergies=_safe_json_loads(getattr(row, "allergies", "[]"), []),
        medicines=_safe_json_loads(row.medicines, []),
        dosages=_safe_json_loads(getattr(row, "dosages", "[]"), []),
        treatment_pattern=row.treatment_pattern,
        lab_reports=_safe_json_loads(getattr(row, "lab_reports", "[]"), []),
        medical_images=_safe_json_loads(getattr(row, "medical_images", "[]"), []),
        age_range=row.age_range,
        watermark_fingerprint=row.watermark_fingerprint,
        is_attractive_lure=getattr(row, "is_attractive_lure", False) or False,
        lure_type=getattr(row, "lure_type", "standard") or "standard",
    )


class SyntheticRepository:
    def upsert(self, twin: TwinRecord, session_id: str, hospital_id: str) -> TwinRecord:
        fingerprint = sha256(
            f"{twin.synthetic_patient_id}|{session_id}|{hospital_id}|{twin.disease}|{twin.diagnosis}|{','.join(twin.medicines)}".encode(
                "utf-8"
            )
        ).hexdigest()
        with SyntheticSessionLocal() as session:
            existing = (
                session.query(SyntheticPatient)
                .filter(SyntheticPatient.real_patient_id == twin.real_patient_id)
                .order_by(SyntheticPatient.created_at.desc())
                .first()
            )
            if existing is not None:
                twin.synthetic_patient_id = existing.id

            row = SyntheticPatient(
                id=twin.synthetic_patient_id,
                real_patient_id=twin.real_patient_id,
                name=twin.name,
                gender=getattr(twin, "gender", "Male") or "Male",
                date_of_birth=getattr(twin, "date_of_birth", "") or "",
                address=twin.address,
                phone_number=twin.phone_number,
                aadhaar_number=twin.aadhaar_number,
                email=twin.email,
                blood_group=getattr(twin, "blood_group", "") or "",
                doctor_assigned=getattr(twin, "doctor_assigned", "") or "",
                department=getattr(twin, "department", "") or "",
                ward=getattr(twin, "ward", "") or "",
                admission_date=getattr(twin, "admission_date", "") or "",
                discharge_date=getattr(twin, "discharge_date", "") or "",
                insurance_id=getattr(twin, "insurance_id", "") or "",
                insurance_details=twin.insurance_details,
                emergency_contact=twin.emergency_contact,
                disease=twin.disease,
                diagnosis=twin.diagnosis,
                symptoms=json.dumps(twin.symptoms) if isinstance(twin.symptoms, list) else str(twin.symptoms or "[]"),
                allergies=json.dumps(twin.allergies) if isinstance(twin.allergies, list) else str(twin.allergies or "[]"),
                medicines=json.dumps(twin.medicines) if isinstance(twin.medicines, list) else str(twin.medicines or "[]"),
                dosages=json.dumps(twin.dosages) if isinstance(twin.dosages, list) else str(twin.dosages or "[]"),
                treatment_pattern=twin.treatment_pattern,
                lab_reports=json.dumps(twin.lab_reports) if isinstance(twin.lab_reports, list) else str(twin.lab_reports or "[]"),
                medical_images=json.dumps(twin.medical_images) if isinstance(twin.medical_images, list) else str(twin.medical_images or "[]"),
                age_range=twin.age_range,
                watermark_fingerprint=getattr(twin, "watermark_fingerprint", fingerprint) or fingerprint,
                is_attractive_lure=getattr(twin, "is_attractive_lure", False) or False,
                lure_type=getattr(twin, "lure_type", "standard") or "standard",
                hospital_id=hospital_id,
            )
            session.merge(row)
            session.commit()
        return twin

    def list_all(self) -> list[TwinRecord]:
        with SyntheticSessionLocal() as session:
            rows = session.query(SyntheticPatient).order_by(SyntheticPatient.created_at.asc()).all()
        return [_to_record(row) for row in rows]

    def find_by_synthetic_id(self, synthetic_patient_id: str) -> SyntheticForensicRecord | None:
        with SyntheticSessionLocal() as session:
            row = session.query(SyntheticPatient).filter(SyntheticPatient.id == synthetic_patient_id).first()
        if row is None:
            return None
        return SyntheticForensicRecord(
            synthetic_patient_id=row.id,
            watermark_fingerprint=row.watermark_fingerprint,
            name=row.name,
            disease=row.disease,
            diagnosis=row.diagnosis,
            treatment_pattern=row.treatment_pattern,
            age_range=row.age_range,
            aadhaar_number=row.aadhaar_number,
            phone_number=row.phone_number,
            email=row.email,
            address=row.address,
            insurance_details=row.insurance_details,
            emergency_contact=row.emergency_contact,
            real_patient_id=getattr(row, "real_patient_id", "") or "",
            gender=getattr(row, "gender", "Male") or "Male",
            blood_group=getattr(row, "blood_group", "O+") or "O+",
            doctor_assigned=getattr(row, "doctor_assigned", "") or "",
            department=getattr(row, "department", "") or "",
            ward=getattr(row, "ward", "") or "",
            admission_date=getattr(row, "admission_date", "") or "",
            discharge_date=getattr(row, "discharge_date", "") or "",
            symptoms=_safe_json_loads(getattr(row, "symptoms", "[]"), []),
            allergies=_safe_json_loads(getattr(row, "allergies", "[]"), []),
            medicines=_safe_json_loads(row.medicines, []),
            dosages=_safe_json_loads(getattr(row, "dosages", "[]"), []),
            lab_reports=_safe_json_loads(getattr(row, "lab_reports", "[]"), []),
            medical_images=_safe_json_loads(getattr(row, "medical_images", "[]"), []),
            is_attractive_lure=getattr(row, "is_attractive_lure", False) or False,
            lure_type=getattr(row, "lure_type", "standard") or "standard",
        )

    def find_by_real_patient_id(self, real_patient_id: str) -> SyntheticForensicRecord | None:
        with SyntheticSessionLocal() as session:
            row = (
                session.query(SyntheticPatient)
                .filter(SyntheticPatient.real_patient_id == real_patient_id)
                .order_by(SyntheticPatient.created_at.desc())
                .first()
            )
        if row is None:
            return None
        return SyntheticForensicRecord(
            synthetic_patient_id=row.id,
            watermark_fingerprint=row.watermark_fingerprint,
            name=row.name,
            disease=row.disease,
            diagnosis=row.diagnosis,
            treatment_pattern=row.treatment_pattern,
            age_range=row.age_range,
            aadhaar_number=row.aadhaar_number,
            phone_number=row.phone_number,
            email=row.email,
            address=row.address,
            insurance_details=row.insurance_details,
            emergency_contact=row.emergency_contact,
            gender=getattr(row, "gender", "Male") or "Male",
            blood_group=getattr(row, "blood_group", "O+") or "O+",
            doctor_assigned=getattr(row, "doctor_assigned", "") or "",
            department=getattr(row, "department", "") or "",
            ward=getattr(row, "ward", "") or "",
            admission_date=getattr(row, "admission_date", "") or "",
            discharge_date=getattr(row, "discharge_date", "") or "",
            symptoms=_safe_json_loads(getattr(row, "symptoms", "[]"), []),
            allergies=_safe_json_loads(getattr(row, "allergies", "[]"), []),
            medicines=_safe_json_loads(row.medicines, []),
            dosages=_safe_json_loads(getattr(row, "dosages", "[]"), []),
            lab_reports=_safe_json_loads(getattr(row, "lab_reports", "[]"), []),
            medical_images=_safe_json_loads(getattr(row, "medical_images", "[]"), []),
            is_attractive_lure=getattr(row, "is_attractive_lure", False) or False,
            lure_type=getattr(row, "lure_type", "standard") or "standard",
        )

    def purge_all(self) -> int:
        with SyntheticSessionLocal() as session:
            count = session.query(SyntheticPatient).delete()
            session.commit()
            return count


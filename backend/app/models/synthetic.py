from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SyntheticBase


class SyntheticPatient(SyntheticBase):
    __tablename__ = "synthetic_patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    real_patient_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=True, default="Male")
    date_of_birth: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    address: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    aadhaar_number: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    doctor_assigned: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    department: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    ward: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    admission_date: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    discharge_date: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    insurance_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    insurance_details: Mapped[str] = mapped_column(String(255), nullable=False)
    emergency_contact: Mapped[str] = mapped_column(String(64), nullable=False)
    disease: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    allergies: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    medicines: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    dosages: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    treatment_pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    lab_reports: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    medical_images: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    age_range: Mapped[str] = mapped_column(String(32), nullable=False)
    watermark_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    is_attractive_lure: Mapped[bool] = mapped_column(nullable=False, default=False)
    lure_type: Mapped[str] = mapped_column(String(64), nullable=False, default="standard")
    hospital_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyntheticDoctor(SyntheticBase):
    __tablename__ = "synthetic_doctors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)


class SyntheticReport(SyntheticBase):
    __tablename__ = "synthetic_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    report_type: Mapped[str] = mapped_column(String(255), nullable=False)
    report_content: Mapped[str] = mapped_column(Text, nullable=False)


class Honeytoken(SyntheticBase):
    __tablename__ = "honeytokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_type: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    twin_id: Mapped[str] = mapped_column(String(64), nullable=False)


class Watermark(SyntheticBase):
    __tablename__ = "watermarks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    watermark_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="synthetic")
    hospital_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    watermark_text: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    watermark_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, default="")

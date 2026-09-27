from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import RealBase


class RealPatient(RealBase):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    disease: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    date_of_birth: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    blood_group: Mapped[str] = mapped_column(String(8), nullable=True, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=True, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    address: Mapped[str] = mapped_column(Text, nullable=True, default="")
    aadhaar: Mapped[str] = mapped_column(String(64), nullable=True, default="")
    emergency_contact: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    doctor_assigned: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    department: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    admission_date: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    discharge_date: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    lab_reports: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    medical_images: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    medicines: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    symptoms: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    allergies: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    dosages: Mapped[str] = mapped_column(Text, nullable=True, default="[]")
    treatment_pattern: Mapped[str] = mapped_column(String(255), nullable=False, default="Standard")
    watermark_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    watermark_text: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    watermark_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RealPatientHistory(RealBase):
    __tablename__ = "patient_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    disease: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    date_of_birth: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    blood_group: Mapped[str] = mapped_column(String(8), nullable=True, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=True, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    address: Mapped[str] = mapped_column(Text, nullable=True, default="")
    aadhaar: Mapped[str] = mapped_column(String(64), nullable=True, default="")
    emergency_contact: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    doctor_assigned: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    department: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    admission_date: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    discharge_date: Mapped[str] = mapped_column(String(32), nullable=True, default="")
    medicines: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="Discharged / Deleted")
    archived_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RealDoctor(RealBase):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)


class Appointment(RealBase):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctors.id"), nullable=False)
    appointment_time: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)


class Prescription(RealBase):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctors.id"), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)


class MedicalHistory(RealBase):
    __tablename__ = "medical_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


class LabReport(RealBase):
    __tablename__ = "lab_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(255), nullable=False)
    report_content: Mapped[str] = mapped_column(Text, nullable=False)

from uuid import uuid4
import json
from datetime import datetime, timezone

from sqlalchemy import func

from app.db.engines import RealSessionLocal
from app.models.real import RealPatient, RealPatientHistory
from app.schemas import PatientRecord


def _to_record(row: RealPatient) -> PatientRecord:
    medicines = row.medicines
    if isinstance(medicines, str):
        try:
            medicines = json.loads(medicines)
        except Exception:
            medicines = []
    def _load_list(value: str) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return list(value)
    return PatientRecord(
        id=row.id,
        name=row.name,
        age=row.age,
        disease=row.disease,
        diagnosis=row.diagnosis,
        medicines=medicines,
        dosages=_load_list(getattr(row, 'dosages', '')),
        treatment_pattern=row.treatment_pattern,
        gender=getattr(row, 'gender', None) or None,
        date_of_birth=getattr(row, 'date_of_birth', None) or None,
        blood_group=getattr(row, 'blood_group', None) or None,
        phone=getattr(row, 'phone', None) or None,
        email=getattr(row, 'email', None) or None,
        address=getattr(row, 'address', None) or None,
        aadhaar=getattr(row, 'aadhaar', None) or None,
        emergency_contact=getattr(row, 'emergency_contact', None) or None,
        doctor_assigned=getattr(row, 'doctor_assigned', None) or None,
        department=getattr(row, 'department', None) or None,
        admission_date=getattr(row, 'admission_date', None) or None,
        discharge_date=getattr(row, 'discharge_date', None) or None,
        lab_reports=_load_list(getattr(row, 'lab_reports', '')),
        medical_images=_load_list(getattr(row, 'medical_images', '')),
        symptoms=_load_list(getattr(row, 'symptoms', '')),
        allergies=_load_list(getattr(row, 'allergies', '')),
        patient_id=row.patient_id,
        watermark_id=row.watermark_id,
        watermark_text=row.watermark_text,
        watermark_fingerprint=row.watermark_fingerprint,
    )


class PatientRepository:
    def _get_next_sequence_and_id(self, session) -> tuple[int, str]:
        import re

        # Gather max sequence from active patients
        max_active_num = session.query(func.max(RealPatient.patient_id)).scalar() or 0
        max_hist_num = session.query(func.max(RealPatientHistory.patient_id)).scalar() or 0

        max_seq = max(int(max_active_num), int(max_hist_num))

        # Check existing string IDs in patients table for P-XX format
        for (pid,) in session.query(RealPatient.id).all():
            m = re.match(r"^P-(\d+)$", str(pid), re.IGNORECASE)
            if m:
                max_seq = max(max_seq, int(m.group(1)))

        # Check existing string IDs in patient_history table for P-XX format
        for (pid,) in session.query(RealPatientHistory.id).all():
            m = re.match(r"^P-(\d+)$", str(pid), re.IGNORECASE)
            if m:
                max_seq = max(max_seq, int(m.group(1)))

        next_seq = max_seq + 1
        formatted_id = f"P-{next_seq:02d}" if next_seq < 100 else f"P-{next_seq}"
        return next_seq, formatted_id

    def add(self, patient: PatientRecord) -> PatientRecord:
        with RealSessionLocal() as session:
            # Check if patient.id is empty, a UUID, or missing P- prefix
            is_uuid = patient.id and len(patient.id) == 36 and "-" in patient.id
            is_valid_p_id = patient.id and (patient.id.startswith("P-") or patient.id.startswith("p-"))

            if not is_valid_p_id or is_uuid or not patient.patient_id:
                next_seq, formatted_id = self._get_next_sequence_and_id(session)
                if not is_valid_p_id or is_uuid:
                    patient.id = formatted_id
                if not patient.patient_id:
                    patient.patient_id = next_seq

            row = RealPatient(
                id=patient.id,
                patient_id=patient.patient_id,
                name=patient.name,
                age=patient.age,
                disease=patient.disease,
                diagnosis=patient.diagnosis,
                gender=patient.gender or "",
                date_of_birth=patient.date_of_birth or "",
                blood_group=patient.blood_group or "",
                phone=patient.phone or "",
                email=patient.email or "",
                address=patient.address or "",
                aadhaar=patient.aadhaar or "",
                emergency_contact=patient.emergency_contact or "",
                doctor_assigned=patient.doctor_assigned or "",
                department=patient.department or "",
                admission_date=patient.admission_date or "",
                discharge_date=patient.discharge_date or "",
                lab_reports=json.dumps(getattr(patient, 'lab_reports', [])),
                medical_images=json.dumps(getattr(patient, 'medical_images', [])),
                medicines=json.dumps(patient.medicines),
                dosages=json.dumps(getattr(patient, 'dosages', [])),
                symptoms=json.dumps(getattr(patient, 'symptoms', [])),
                allergies=json.dumps(getattr(patient, 'allergies', [])),
                treatment_pattern=patient.treatment_pattern,
                watermark_id=patient.watermark_id,
                watermark_text=patient.watermark_text,
                watermark_fingerprint=patient.watermark_fingerprint,
            )
            merged = session.merge(row)
            session.commit()
            session.refresh(merged)
        return patient

    def find_by_id(self, patient_id: str) -> PatientRecord | None:
        with RealSessionLocal() as session:
            row = session.query(RealPatient).filter(RealPatient.id == patient_id).first()
            if row is None and str(patient_id).isdigit():
                num = int(patient_id)
                formatted = f"P-{num:02d}" if num < 100 else f"P-{num}"
                row = session.query(RealPatient).filter(
                    (RealPatient.patient_id == num) | (RealPatient.id == formatted)
                ).first()
            if row is None and str(patient_id).upper().startswith("P-"):
                try:
                    num = int(patient_id[2:])
                    row = session.query(RealPatient).filter(
                        (RealPatient.patient_id == num) | (RealPatient.id == patient_id)
                    ).first()
                except ValueError:
                    pass
        if row is None:
            return None
        return _to_record(row)

    def find_by_email(self, email: str) -> list[PatientRecord]:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return []
        with RealSessionLocal() as session:
            rows = session.query(RealPatient).filter(
                func.lower(func.trim(RealPatient.email)) == normalized_email
            ).all()
        return [_to_record(row) for row in rows]

    def list_all(self) -> list[PatientRecord]:
        with RealSessionLocal() as session:
            rows = session.query(RealPatient).order_by(RealPatient.created_at.asc()).all()
        return [_to_record(row) for row in rows]

    def delete(self, patient_id: str) -> PatientRecord | None:
        with RealSessionLocal() as session:
            row = session.query(RealPatient).filter(RealPatient.id == patient_id).first()
            if row is None and str(patient_id).isdigit():
                row = session.query(RealPatient).filter(RealPatient.patient_id == int(patient_id)).first()
            if row is None:
                return None
            record = _to_record(row)

            # Persist in real SQLite patient_history table
            hist_row = RealPatientHistory(
                id=record.id,
                patient_id=record.patient_id or 0,
                name=record.name,
                age=record.age,
                disease=record.disease,
                diagnosis=record.diagnosis,
                gender=record.gender or "",
                date_of_birth=record.date_of_birth or "",
                blood_group=record.blood_group or "",
                phone=record.phone or "",
                email=record.email or "",
                address=record.address or "",
                aadhaar=record.aadhaar or "",
                emergency_contact=record.emergency_contact or "",
                doctor_assigned=record.doctor_assigned or "",
                department=record.department or "",
                admission_date=record.admission_date or "",
                discharge_date=record.discharge_date or "",
                medicines=json.dumps(record.medicines),
                status="Discharged / Deleted",
            )
            session.merge(hist_row)
            session.delete(row)
            session.commit()
            return record

    def update(self, patient: PatientRecord) -> PatientRecord:
        with RealSessionLocal() as session:
            row = session.query(RealPatient).filter(RealPatient.id == patient.id).first()
            if row is None and str(patient.id).isdigit():
                row = session.query(RealPatient).filter(RealPatient.patient_id == int(patient.id)).first()
            if row is None:
                return self.add(patient)

            row.name = patient.name
            row.age = patient.age
            row.disease = patient.disease
            row.diagnosis = patient.diagnosis
            row.gender = patient.gender or ""
            row.date_of_birth = patient.date_of_birth or ""
            row.blood_group = patient.blood_group or ""
            row.phone = patient.phone or ""
            row.email = patient.email or ""
            row.address = patient.address or ""
            row.aadhaar = patient.aadhaar or ""
            row.emergency_contact = patient.emergency_contact or ""
            row.doctor_assigned = patient.doctor_assigned or ""
            row.department = patient.department or ""
            row.admission_date = patient.admission_date or ""
            row.discharge_date = patient.discharge_date or ""
            row.lab_reports = json.dumps(getattr(patient, 'lab_reports', []))
            row.medical_images = json.dumps(getattr(patient, 'medical_images', []))
            row.medicines = json.dumps(patient.medicines)
            row.dosages = json.dumps(getattr(patient, 'dosages', []))
            row.symptoms = json.dumps(getattr(patient, 'symptoms', []))
            row.allergies = json.dumps(getattr(patient, 'allergies', []))
            row.treatment_pattern = patient.treatment_pattern
            row.watermark_id = patient.watermark_id
            row.watermark_text = patient.watermark_text
            row.watermark_fingerprint = patient.watermark_fingerprint

            session.merge(row)
            session.commit()
            session.refresh(row)
        return patient

    def list_history(self) -> list[dict]:
        with RealSessionLocal() as session:
            rows = session.query(RealPatientHistory).order_by(RealPatientHistory.archived_at.desc()).all()
            history_list = []
            for r in rows:
                meds = r.medicines
                if isinstance(meds, str):
                    try:
                        meds = json.loads(meds)
                    except Exception:
                        meds = []
                history_list.append({
                    "id": r.id,
                    "patient_id": r.patient_id,
                    "name": r.name,
                    "age": r.age,
                    "disease": r.disease,
                    "diagnosis": r.diagnosis,
                    "gender": r.gender,
                    "phone": r.phone,
                    "email": r.email,
                    "aadhaar": r.aadhaar,
                    "status": r.status,
                    "medicines": meds,
                    "archived_at": r.archived_at.isoformat() if r.archived_at else "",
                })
            return history_list

    def delete_history(self, history_id: str) -> bool:
        with RealSessionLocal() as session:
            row = session.query(RealPatientHistory).filter(RealPatientHistory.id == history_id).first()
            if row is None and str(history_id).isdigit():
                row = session.query(RealPatientHistory).filter(RealPatientHistory.patient_id == int(history_id)).first()
            if row is None and str(history_id).upper().startswith("P-"):
                try:
                    num = int(history_id[2:])
                    row = session.query(RealPatientHistory).filter(
                        (RealPatientHistory.patient_id == num) | (RealPatientHistory.id == history_id)
                    ).first()
                except ValueError:
                    pass
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def clear_all_history(self) -> int:
        with RealSessionLocal() as session:
            count = session.query(RealPatientHistory).delete()
            session.commit()
            return count

    def purge_all(self) -> int:
        with RealSessionLocal() as session:
            p_count = session.query(RealPatient).delete()
            h_count = session.query(RealPatientHistory).delete()
            session.commit()
            return p_count + h_count


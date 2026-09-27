from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.patient_repository import PatientRepository
from app.repositories.synthetic_repository import SyntheticRepository
from app.schemas import PatientCreate, PatientRecord, TwinRecord
from .ai_engine_proxy import TwinGeneratorProxy
from .registries import patient_repository, synthetic_repository
from .security import block_session, record_forensic_attack
from .watermark import create_watermark, verify_patient_watermark
from app.repositories.watermark_repository import watermark_repository


def _clean_name(raw: str | None) -> str:
    if not raw:
        return "Karthik Reddy"
    cleaned = str(raw).replace("Synthetic ", "").replace("synthetic ", "").replace("Fake ", "").replace("fake ", "").replace("Decoy ", "").replace("decoy ", "")
    return cleaned.strip() or "Karthik Reddy"


def _clean_disease(raw: str | None) -> str:
    if not raw:
        return "Hypertension Management"
    cleaned = str(raw).replace("Transformed ", "").replace("transformed ", "")
    cleaned = cleaned.replace(" (Vip Executive Protocol)", "").replace(" (VIP Executive Protocol)", "")
    return cleaned.strip() or "Cardiovascular Evaluation"


class PatientService:
    def __init__(self, twin_generator: TwinGeneratorProxy) -> None:
        self._twin_generator = twin_generator
        self._generation_counter = 0

    def _generate_synthetic_twin(self, patient: PatientRecord, session_id: str, hospital_id: str, is_attractive: bool = False, lure_type: str = "standard") -> TwinRecord:
        self._generation_counter += 1
        recent_real = [record.model_dump() for record in patient_repository.list_all()[-25:]]
        recent_synthetic = [record.model_dump() for record in synthetic_repository.list_all()[-25:]]
        twin_payload = patient.model_dump()
        twin_payload.setdefault("patient_id", patient.patient_id)
        
        # Trigger dynamic AI statistical pattern evolution
        self._twin_generator.evolve_patterns([twin_payload])

        twin = self._twin_generator.generate(
            twin_payload,
            context={
                "recent_real_patients": recent_real,
                "recent_synthetic_patients": recent_synthetic,
                "session_id": session_id,
                "hospital_id": hospital_id,
                "attractive": is_attractive,
                "lure_type": lure_type,
                "revision": f"{datetime.now(timezone.utc).timestamp()}:{self._generation_counter}",
            },
        )
        real_pid_val = patient.id or str(patient.patient_id or "")
        twin["real_patient_id"] = real_pid_val

        # Deterministic 1:1 synthetic ID mapping: P-01 -> SYN-01, P-02 -> SYN-02
        if real_pid_val.upper().startswith("P-"):
            twin["synthetic_patient_id"] = f"SYN-{real_pid_val[2:]}"
        elif str(real_pid_val).isdigit():
            twin["synthetic_patient_id"] = f"SYN-{int(real_pid_val):02d}"

        # Ensure synthetic values are strictly different from the original real patient
        if twin.get("name") == patient.name or not twin.get("name"):
            twin["name"] = f"Synthetic {patient.name}"
        if twin.get("phone_number") == patient.phone or not twin.get("phone_number"):
            twin["phone_number"] = "+91-98888-12345"
        if twin.get("email") == patient.email or not twin.get("email"):
            twin["email"] = "synthetic.decoy@healthcare-twin.org"
        if twin.get("disease") == patient.disease:
            twin["disease"] = f"Transformed {patient.disease}"

        twin_record = TwinRecord(**twin)
        twin_record.real_patient_id = real_pid_val
        synthetic_repository.upsert(twin_record, session_id=session_id, hospital_id=hospital_id)
        existing_watermark = watermark_repository.find_by_source_id(twin_record.synthetic_patient_id, source_type="synthetic")
        if existing_watermark is None:
            wm = create_watermark(
                twin_record.synthetic_patient_id,
                source_type="synthetic",
                hospital_id=hospital_id,
                session_id=session_id,
                source_data=twin_record.model_dump(),
            )
            twin_record.watermark_id = wm.watermark_id
        else:
            twin_record.watermark_id = existing_watermark.watermark_id
        return twin_record

    def get_or_create_synthetic_twin(
        self,
        patient: PatientRecord,
        session_id: str = "anonymous",
        hospital_id: str = "HOSPITAL-001",
    ) -> TwinRecord:
        real_pid = patient.id or str(patient.patient_id or "")
        existing = synthetic_repository.find_by_real_patient_id(real_pid)
        if existing is not None:
            wm = watermark_repository.find_by_source_id(existing.synthetic_patient_id, source_type="synthetic")
            watermark_id = wm.watermark_id if wm else ""
            if not watermark_id:
                new_wm = create_watermark(
                    existing.synthetic_patient_id,
                    source_type="synthetic",
                    hospital_id=hospital_id,
                    session_id=session_id,
                    source_data=existing.__dict__,
                )
                watermark_id = new_wm.watermark_id
            return TwinRecord(
                real_patient_id=getattr(existing, "real_patient_id", "") or real_pid,
                synthetic_patient_id=getattr(existing, "synthetic_patient_id", "") or getattr(existing, "id", ""),
                name=getattr(existing, "name", ""),
                gender=getattr(existing, "gender", "Male"),
                date_of_birth=getattr(existing, "date_of_birth", "") or None,
                age_range=getattr(existing, "age_range", "30-45"),
                blood_group=getattr(existing, "blood_group", "O+"),
                doctor_assigned=getattr(existing, "doctor_assigned", ""),
                department=getattr(existing, "department", ""),
                ward=getattr(existing, "ward", ""),
                admission_date=getattr(existing, "admission_date", ""),
                discharge_date=getattr(existing, "discharge_date", ""),
                insurance_details=getattr(existing, "insurance_details", ""),
                emergency_contact=getattr(existing, "emergency_contact", ""),
                phone_number=getattr(existing, "phone_number", ""),
                email=getattr(existing, "email", ""),
                aadhaar_number=getattr(existing, "aadhaar_number", ""),
                address=getattr(existing, "address", ""),
                disease=getattr(existing, "disease", ""),
                diagnosis=getattr(existing, "diagnosis", ""),
                treatment_pattern=getattr(existing, "treatment_pattern", "Standard"),
                symptoms=getattr(existing, "symptoms", []),
                allergies=getattr(existing, "allergies", []),
                medicines=getattr(existing, "medicines", []),
                dosages=getattr(existing, "dosages", []),
                lab_reports=getattr(existing, "lab_reports", []),
                medical_images=getattr(existing, "medical_images", []),
                watermark_fingerprint=getattr(existing, "watermark_fingerprint", ""),
                is_attractive_lure=getattr(existing, "is_attractive_lure", False),
                lure_type=getattr(existing, "lure_type", "standard"),
                watermark_id=watermark_id,
            )
        return self._generate_synthetic_twin(patient, session_id=session_id, hospital_id=hospital_id)

    def get_patient_deceptive(
        self,
        patient_id: str,
        session_id: str = "anonymous",
        hospital_id: str = "HOSPITAL-001",
        ip_address: str = "127.0.0.1",
        user_agent: str = "",
        username: str | None = None,
    ) -> dict:
        real_patient = patient_repository.find_by_id(patient_id)
        if real_patient is None:
            digits = "".join(ch for ch in str(patient_id) if ch.isdigit())
            seq_num = int(digits) if digits else 1
            real_patient = PatientRecord(
                id=patient_id if str(patient_id).upper().startswith("P-") else f"P-{seq_num:02d}",
                patient_id=seq_num,
                name="Original Patient",
                age=45,
                disease="Essential Primary Hypertension",
                diagnosis="Hypertensive Cardiovascular Disease",
                medicines=["Amlodipine 5mg", "Telmisartan 40mg"],
                dosages=["1 OD", "1 OD"],
                treatment_pattern="Standard Cardiology Protocol",
                phone="+91-91234-56789",
                email="patient.real@hospital.org",
                address="Original Patient Residential Address",
            )

        twin = self.get_or_create_synthetic_twin(real_patient, session_id=session_id, hospital_id=hospital_id)
        wm = watermark_repository.find_by_source_id(twin.synthetic_patient_id, source_type="synthetic")
        watermark_id = wm.watermark_id if wm else twin.watermark_id

        record_forensic_attack(
            attack_type="PATIENT_ENUMERATION",
            session_id=session_id,
            risk_score=94.0,
            gateway_decision="DECEIVE",
            patient_id=real_patient.id,
            synthetic_patient_id=twin.synthetic_patient_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            watermark_id=watermark_id,
            records_returned=1,
            blocked_status=False,
        )

        target_pid = twin.synthetic_patient_id

        return {
            "id": target_pid,
            "patient_id": target_pid,
            "synthetic_patient_id": twin.synthetic_patient_id,
            "name": _clean_name(twin.name),
            "age": twin.age_range,
            "gender": twin.gender or "Male",
            "date_of_birth": twin.date_of_birth or "",
            "blood_group": twin.blood_group or "O+",
            "doctor_assigned": twin.doctor_assigned or "Dr. Priya Nair (Cardiology)",
            "department": twin.department or "Cardiology",
            "ward": twin.ward or "General Ward (W-1)",
            "admission_date": twin.admission_date or "",
            "discharge_date": twin.discharge_date or "",
            "disease": _clean_disease(twin.disease),
            "diagnosis": twin.diagnosis,
            "symptoms": twin.symptoms or [],
            "allergies": twin.allergies or ["No Known Drug Allergies (NKDA)"],
            "medicines": twin.medicines or [],
            "dosages": twin.dosages or [],
            "treatment_pattern": twin.treatment_pattern,
            "lab_reports": twin.lab_reports or [],
            "medical_images": twin.medical_images or [],
            "insurance_details": twin.insurance_details,
            "emergency_contact": twin.emergency_contact,
            "phone": twin.phone_number,
            "email": twin.email,
            "aadhaar": twin.aadhaar_number,
            "address": twin.address,
            "watermark_id": watermark_id,
            "watermark_text": wm.watermark_text if wm else None,
            "watermark_fingerprint": wm.watermark_fingerprint if wm else None,
            "is_attractive_lure": getattr(twin, "is_attractive_lure", False),
            "lure_type": getattr(twin, "lure_type", "standard"),
            "is_synthetic": True,
        }

    def create_patient(
        self,
        payload: PatientCreate,
        session_id: str = "anonymous",
        hospital_id: str = "HOSPITAL-001",
        route: str = "real",
    ) -> tuple[PatientRecord, TwinRecord]:
        patient = PatientRecord(id="", **payload.model_dump())
        if route == "real":
            patient = patient_repository.add(patient)

        real_watermark = create_watermark(
            patient.id,
            source_type="real",
            hospital_id=hospital_id,
            session_id=session_id,
            source_data=payload.model_dump(),
        )
        patient.watermark_id = real_watermark.watermark_id
        patient.watermark_text = real_watermark.watermark_text
        patient.watermark_fingerprint = real_watermark.watermark_fingerprint

        if route == "real":
            patient = patient_repository.update(patient)

        twin_record = self._generate_synthetic_twin(patient, session_id=session_id, hospital_id=hospital_id)
        return patient, twin_record

    def list_patients(self, session_id: str = "anonymous", hospital_id: str = "HOSPITAL-001", route: str = "real", limit: int | None = None) -> list[dict]:
        if route == "synthetic":
            real_patients = patient_repository.list_all()
            records: list[dict] = []
            for rp in real_patients:
                twin = self.get_or_create_synthetic_twin(rp, session_id=session_id, hospital_id=hospital_id)
                watermark = watermark_repository.find_by_source_id(twin.synthetic_patient_id, source_type="synthetic")
                syn_id = twin.synthetic_patient_id
                display_pid = rp.id if (rp.id and str(rp.id).upper().startswith("P-")) else (f"P-{syn_id[4:]}" if syn_id.upper().startswith("SYN-") else f"P-{syn_id}")
                records.append(
                    {
                        "id": display_pid,
                        "patient_id": display_pid,
                        "synthetic_patient_id": syn_id,
                        "name": _clean_name(twin.name),
                        "age": twin.age_range,
                        "gender": twin.gender or "Male",
                        "date_of_birth": twin.date_of_birth or "",
                        "blood_group": twin.blood_group or "O+",
                        "doctor_assigned": twin.doctor_assigned or "Dr. Priya Nair (Cardiology)",
                        "department": twin.department or "Cardiology",
                        "ward": twin.ward or "General Ward (W-1)",
                        "admission_date": twin.admission_date or "",
                        "discharge_date": twin.discharge_date or "",
                        "disease": _clean_disease(twin.disease),
                        "diagnosis": twin.diagnosis,
                        "symptoms": twin.symptoms or [],
                        "allergies": twin.allergies or ["No Known Drug Allergies (NKDA)"],
                        "medicines": twin.medicines or [],
                        "dosages": twin.dosages or [],
                        "treatment_pattern": twin.treatment_pattern,
                        "lab_reports": twin.lab_reports or [],
                        "medical_images": twin.medical_images or [],
                        "insurance_details": twin.insurance_details,
                        "emergency_contact": twin.emergency_contact,
                        "phone": twin.phone_number,
                        "email": twin.email,
                        "aadhaar": twin.aadhaar_number,
                        "address": twin.address,
                        "watermark_id": watermark.watermark_id if watermark else None,
                        "watermark_text": watermark.watermark_text if watermark else None,
                        "watermark_fingerprint": watermark.watermark_fingerprint if watermark else None,
                        "is_attractive_lure": getattr(twin, "is_attractive_lure", False),
                        "lure_type": getattr(twin, "lure_type", "standard"),
                        "is_synthetic": True,
                    }
                )
            return records[:limit] if limit is not None else records

        patients = patient_repository.list_all()
        for patient in patients:
            verify_patient_watermark(patient, hospital_id=hospital_id)
        result = [patient.model_dump() for patient in patients]
        return result[:limit] if limit is not None else result


    def delete_patient(
        self,
        patient_id: str,
        session_id: str = "anonymous",
        hospital_id: str = "HOSPITAL-001",
        route: str = "real",
    ) -> tuple[PatientRecord | None, TwinRecord | None]:
        existing = patient_repository.find_by_id(patient_id)
        if existing is None:
            return None, None

        twin_record = self._generate_synthetic_twin(existing, session_id=session_id, hospital_id=hospital_id)
        if route == "real":
            deleted = patient_repository.delete(patient_id)
            return deleted, twin_record

        # Suspicious delete requests are diverted to synthetic decoys and the real patient remains intact.
        return existing, twin_record

    def update_patient(
        self,
        patient_id: str,
        payload: PatientCreate,
        session_id: str = "anonymous",
        hospital_id: str = "HOSPITAL-001",
        route: str = "real",
    ) -> tuple[PatientRecord, TwinRecord]:
        existing = patient_repository.find_by_id(patient_id)
        if existing is None:
            raise ValueError("Patient not found")

        # apply updates
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)

        # refresh watermark for real record
        real_watermark = create_watermark(
            existing.id,
            source_type="real",
            hospital_id=hospital_id,
            session_id=session_id,
            source_data=existing.model_dump(),
        )
        existing.watermark_id = real_watermark.watermark_id
        existing.watermark_text = real_watermark.watermark_text
        existing.watermark_fingerprint = real_watermark.watermark_fingerprint

        if route == "real":
            # persist updated real patient
            patient_repository.update(existing)

        twin_record = self._generate_synthetic_twin(existing, session_id=session_id, hospital_id=hospital_id)
        return existing, twin_record

    def list_patient_history(self) -> list[dict]:
        return patient_repository.list_history()

    def delete_patient_history(self, history_id: str) -> bool:
        return patient_repository.delete_history(history_id)

    def clear_all_patient_history(self) -> int:
        return patient_repository.clear_all_history()

    def purge_all_patients(self) -> dict:
        real_count = patient_repository.purge_all()
        syn_count = synthetic_repository.purge_all()
        return {"purged_real_and_history": real_count, "purged_synthetic_twins": syn_count}

    def get_pattern_profile(self) -> dict:
        return self._twin_generator.get_pattern_profile()


from app.services.twin import twin_generator_proxy

patient_service = PatientService(twin_generator_proxy)




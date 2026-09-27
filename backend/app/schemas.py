from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    name: str
    age: int = Field(ge=0, le=130)
    disease: str
    diagnosis: str
    medicines: list[str] = []
    dosages: list[str] = []
    treatment_pattern: str = "Standard"
    gender: str | None = None
    date_of_birth: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    aadhaar: str | None = None
    emergency_contact: str | None = None
    symptoms: list[str] = []
    allergies: list[str] = []
    doctor_assigned: str | None = None
    department: str | None = None
    admission_date: str | None = None
    discharge_date: str | None = None
    lab_reports: list[str] = []
    medical_images: list[str] = []
    patient_id: int = 0


class PatientRecord(PatientCreate):
    id: str
    patient_id: int = 0
    watermark_id: str = ""
    watermark_text: str = ""
    watermark_fingerprint: str = ""
    is_synthetic: bool = False


class TwinRecord(BaseModel):
    real_patient_id: str
    synthetic_patient_id: str
    name: str
    address: str
    phone_number: str
    aadhaar_number: str
    email: str
    insurance_details: str
    emergency_contact: str
    disease: str
    diagnosis: str
    medicines: list[str] = []
    treatment_pattern: str = "Standard"
    age_range: str = "38-43 yrs"
    gender: str | None = None
    date_of_birth: str | None = None
    blood_group: str | None = None
    doctor_assigned: str | None = None
    department: str | None = None
    ward: str | None = None
    admission_date: str | None = None
    discharge_date: str | None = None
    symptoms: list[str] = []
    allergies: list[str] = []
    dosages: list[str] = []
    lab_reports: list[str] = []
    medical_images: list[str] = []
    watermark_fingerprint: str = ""
    watermark_id: str = ""
    is_attractive_lure: bool = False
    lure_type: str = "standard"
    is_synthetic: bool = True


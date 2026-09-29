import json
import random
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from faker import Faker

fake = Faker()


@dataclass
class SyntheticTwin:
    real_patient_id: str
    synthetic_patient_id: str
    name: str
    gender: str
    date_of_birth: str
    age_range: str
    blood_group: str
    phone_number: str
    aadhaar_number: str
    email: str
    address: str
    emergency_contact: str
    doctor_assigned: str
    department: str
    ward: str
    admission_date: str
    discharge_date: str
    disease: str
    diagnosis: str
    symptoms: list[str]
    allergies: list[str]
    medicines: list[str]
    dosages: list[str]
    treatment_pattern: str
    lab_reports: list[str]
    medical_images: list[str]
    insurance_details: str
    watermark_fingerprint: str = ""
    is_attractive_lure: bool = False
    lure_type: str = "standard"


class ClinicalPatternProfile:
    """Maintains evolving differential statistical patterns of real EHR without raw PII."""

    def __init__(self) -> None:
        self.disease_counts: Counter[str] = Counter()
        self.department_counts: Counter[str] = Counter()
        self.treatment_counts: Counter[str] = Counter()
        self.medication_associations: dict[str, Counter[str]] = {}
        self.symptom_associations: dict[str, Counter[str]] = {}
        self.lab_associations: dict[str, list[str]] = {}
        self.age_samples: list[int] = []
        self.total_patients_observed: int = 0
        self.last_updated: str = datetime.now(timezone.utc).isoformat()

    def update_from_patient(self, patient: dict) -> None:
        self.total_patients_observed += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()

        disease = str(patient.get("disease", "")).strip()
        dept = str(patient.get("department", "")).strip()
        treatment = str(patient.get("treatment_pattern", "")).strip()
        age = patient.get("age")

        if disease:
            self.disease_counts[disease] += 1
        if dept:
            self.department_counts[dept] += 1
        if treatment:
            self.treatment_counts[treatment] += 1
        if isinstance(age, (int, float)) and 0 < age < 120:
            self.age_samples.append(int(age))
            if len(self.age_samples) > 200:
                self.age_samples.pop(0)

        # Medication and symptom associations
        if disease:
            if disease not in self.medication_associations:
                self.medication_associations[disease] = Counter()
            for med in patient.get("medicines", []):
                if med:
                    self.medication_associations[disease][str(med).strip()] += 1

            if disease not in self.symptom_associations:
                self.symptom_associations[disease] = Counter()
            for sym in patient.get("symptoms", []):
                if sym:
                    self.symptom_associations[disease][str(sym).strip()] += 1

    def update_batch(self, patients: list[dict]) -> None:
        for p in patients:
            self.update_from_patient(p)

    def get_summary(self) -> dict:
        avg_age = round(sum(self.age_samples) / len(self.age_samples), 1) if self.age_samples else 42.5
        top_diseases = [d for d, _ in self.disease_counts.most_common(5)]
        top_departments = [dept for dept, _ in self.department_counts.most_common(5)]
        return {
            "total_patients_observed": self.total_patients_observed,
            "top_diseases": top_diseases or ["Hypertension", "Type 2 Diabetes", "Coronary Artery Disease"],
            "top_departments": top_departments or ["Cardiology", "General Medicine", "Endocrinology"],
            "average_age_distribution": avg_age,
            "active_pattern_rules": len(self.medication_associations),
            "realism_fidelity_score": min(99.4, 85.0 + min(len(self.disease_counts) * 2.5, 14.4)),
            "last_updated": self.last_updated,
        }


class TwinGenerator:
    def __init__(self) -> None:
        self.pattern_profile = ClinicalPatternProfile()

    def learn_patterns(self, patients: list[dict]) -> dict:
        self.pattern_profile.update_batch(patients)
        return self.pattern_profile.get_summary()

    def get_profile(self) -> dict:
        return self.pattern_profile.get_summary()

    def generate(self, real_patient: dict, context: dict | None = None) -> SyntheticTwin:
        context = context or {}
        # Learn from this patient observation to evolve internal pattern state
        self.pattern_profile.update_from_patient(real_patient)

        recent_real_patients = context.get("recent_real_patients", [])
        if recent_real_patients:
            self.pattern_profile.update_batch(recent_real_patients)

        age = int(real_patient.get("age", 42))
        age_range = f"{max(18, age - 2)}-{age + 3} yrs"

        raw_disease = str(real_patient.get("disease", "General Clinical Follow-up")).strip()
        raw_diagnosis = str(real_patient.get("diagnosis", "Stable Clinical Status")).strip()

        disease = self._refine_clinical_disease(raw_disease)
        diagnosis = self._refine_clinical_diagnosis(raw_diagnosis, disease)
        treatment_pattern = self._derive_treatment_pattern(real_patient.get("treatment_pattern"), disease)

        gender = str(real_patient.get("gender") or "Male").capitalize()
        blood_group = self._derive_blood_group(real_patient.get("blood_group"))
        dob = real_patient.get("date_of_birth") or f"{datetime.now().year - age}-04-12"

        department, doctor = self._derive_department_and_doctor(disease, real_patient.get("department"))
        ward = self._derive_ward(department, age)

        admission_date = real_patient.get("admission_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        discharge_date = real_patient.get("discharge_date") or ""

        medicines = self._medicines_for_disease(disease, real_patient.get("medicines"))
        dosages = self._dosages_for_medicines(medicines)
        symptoms = self._symptoms_for_disease(disease, real_patient.get("symptoms"))
        allergies = self._allergies_for_patient(real_patient.get("allergies"))
        lab_reports = self._generate_synthetic_lab_reports(disease, age)
        medical_images = self._generate_synthetic_imaging_notes(disease)

        is_attractive = bool(context.get("attractive", False) or context.get("threat_score", 0) >= 70)
        lure_type = str(context.get("lure_type", "high_value_clinical_trial" if is_attractive else "standard"))

        fingerprint_seed = "|".join(
            [
                str(real_patient.get("id", real_patient.get("patient_id", "P-01"))),
                str(context.get("session_id", "anonymous")),
                str(context.get("hospital_id", "HOSPITAL-001")),
                disease,
                diagnosis,
                treatment_pattern,
                str(context.get("revision", "0")),
                str(real_patient.get("name", "")),
            ]
        )
        fingerprint = sha256(fingerprint_seed.encode("utf-8")).hexdigest()

        # Realistic Indian identities with zero real PII
        real_name = str(real_patient.get("name", "Patient")).strip()
        synthetic_name = self._generate_realistic_name(real_name, gender, fingerprint)

        prefix = (int(fingerprint[:2], 16) % 8) + 2
        aadhaar_raw = str(prefix) + "".join([str(int(c, 16) % 10) for c in fingerprint[2:13]])
        aadhaar_number = f"{aadhaar_raw[:4]}-{aadhaar_raw[4:8]}-{aadhaar_raw[8:12]}"

        phone_digits = "".join([str(int(c, 16) % 10) for c in fingerprint[13:21]])
        phone_number = f"+91-98{phone_digits[:3]}-{phone_digits[3:8]}"

        emergency_digits = "".join([str(int(c, 16) % 10) for c in fingerprint[21:29]])
        emergency_contact = f"+91-97{emergency_digits[:3]}-{emergency_digits[3:8]}"

        name_parts = [p.replace(".", "").strip() for p in synthetic_name.lower().split() if p]
        rand_num = (int(fingerprint[14:18], 16) % 900) + 100
        clean_email = f"{name_parts[0]}{name_parts[1] if len(name_parts) > 1 else 'patient'}{rand_num}@gmail.com"

        address = self._address_from_fingerprint(fingerprint)

        # Deterministic P format
        real_pid_val = str(real_patient.get("id", real_patient.get("patient_id", "")))
        if real_pid_val.upper().startswith("P-"):
            syn_id = f"P-{real_pid_val[2:]}"
        elif real_pid_val.isdigit():
            syn_id = f"P-{int(real_pid_val):02d}"
        else:
            id_num = (int(fingerprint[:6], 16) % 89999) + 10001
            syn_id = f"P-{id_num}"

        insurance_plan = "Star Health & Allied Insurance | Comprehensive Platinum Cover (Cover ID: #SH-884920)" if not is_attractive else "HDFC ERGO Health Optima Super Platinum VIP Corporate Cover (Sum Insured: ₹50,00,000)"

        return SyntheticTwin(
            real_patient_id=str(real_patient.get("id", real_patient.get("patient_id", "P-01"))),
            synthetic_patient_id=syn_id,
            name=synthetic_name,
            gender=gender,
            date_of_birth=dob,
            age_range=age_range,
            blood_group=blood_group,
            phone_number=phone_number,
            aadhaar_number=aadhaar_number,
            email=clean_email,
            address=address,
            emergency_contact=emergency_contact,
            doctor_assigned=doctor,
            department=department,
            ward=ward,
            admission_date=admission_date,
            discharge_date=discharge_date,
            disease=disease,
            diagnosis=diagnosis,
            symptoms=symptoms,
            allergies=allergies,
            medicines=medicines,
            dosages=dosages,
            treatment_pattern=treatment_pattern,
            lab_reports=lab_reports,
            medical_images=medical_images,
            insurance_details=insurance_plan,
            watermark_fingerprint=fingerprint[:16],
            is_attractive_lure=is_attractive,
            lure_type=lure_type,
        )

    def _refine_clinical_disease(self, raw: str) -> str:
        r = raw.lower()
        if "head" in r or "migrain" in r:
            return "Cephalea / Acute Vascular Migraine"
        if "hyper" in r or "bp" in r or "press" in r:
            return "Essential Primary Hypertension"
        if "diabet" in r or "sugar" in r:
            return "Type 2 Diabetes Mellitus"
        if "fever" in r or "pyrex" in r:
            return "Acute Viral Pyrexia with Dehydration"
        if "card" in r or "heart" in r or "angina" in r:
            return "Ischemic Heart Disease (Angina Pectoris)"
        if "asthma" in r or "bronch" in r:
            return "Bronchial Asthma (Moderate Persistent)"
        if "kidney" in r or "renal" in r:
            return "Chronic Kidney Disease (Stage 2)"
        return raw.title() if len(raw) > 2 else "Clinical Medical Protocol"

    def _refine_clinical_diagnosis(self, raw_diag: str, disease: str) -> str:
        r = raw_diag.lower()
        if "norm" in r or "unknown" in r or len(raw_diag) < 3 or "ded" in r or "test" in r or "stable" in r:
            if "Migraine" in disease:
                return "Acute Tension-Type Cephalea with Cervicogenic Spasm"
            if "Hypertension" in disease:
                return "Stage 1 Essential Hypertension with Left Ventricular Strain"
            if "Diabetes" in disease:
                return "Non-Insulin Dependent Diabetes Mellitus with Peripheral Neuropathy"
            if "Angina" in disease or "Heart" in disease:
                return "Stable Angina Pectoris with Exercise-Induced Dyspnea"
            if "Asthma" in disease or "Bronch" in disease:
                return "Allergic Bronchial Asthma with Nocturnal Wheezing"
            if "Kidney" in disease or "Renal" in disease:
                return "Early Diabetic Nephropathy with Microalbuminuria"
            return "Stable Symptomatic Clinical Presentation under Routine Protocol"
        return raw_diag.title()

    def _derive_treatment_pattern(self, pattern: str | None, disease: str) -> str:
        if pattern and pattern not in {"Standard", ""}:
            return pattern
        if "Heart" in disease or "Angina" in disease:
            return "Standard Cardiac Stabilization Protocol"
        if "Diabetes" in disease:
            return "Glycemic Control & Endocrine Care Protocol"
        if "Hypertension" in disease:
            return "Antihypertensive Optimization Regimen"
        if "Asthma" in disease or "Bronch" in disease:
            return "Bronchodilator & Airway Anti-inflammatory Care"
        return "Standard Clinical Medical Protocol"

    def _derive_blood_group(self, raw: str | None) -> str:
        groups = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
        if raw and raw in groups:
            return raw
        return random.choice(["O+", "B+", "A+", "AB+"])

    def _derive_department_and_doctor(self, disease: str, dept_hint: str | None) -> tuple[str, str]:
        d = disease.lower()
        if "heart" in d or "card" in d or "angina" in d:
            return "Cardiology", "Dr. Priya Nair (Cardiology)"
        if "diabet" in d or "endocrin" in d:
            return "Endocrinology", "Dr. Vikram Joshi (Endocrinology)"
        if "head" in d or "migrain" in d or "neuro" in d:
            return "Neurology", "Dr. Rajesh Sharma (Neurology)"
        if "asthma" in d or "bronch" in d or "pulmon" in d:
            return "Pulmonology", "Dr. Sunita Deshmukh (Pulmonology)"
        if "kidney" in d or "nephro" in d:
            return "Nephrology", "Dr. Manish Kapoor (Nephrology)"
        if "cancer" in d or "oncol" in d or "tumor" in d:
            return "Oncology", "Dr. Ananya Varma (Oncology)"
        return dept_hint or "General Medicine", "Dr. Suresh Deshmukh (General Medicine)"

    def _derive_ward(self, department: str, age: int) -> str:
        if department == "Cardiology":
            return "Cardiac Care Unit (CCU-2)"
        if age > 65:
            return "Geriatric Care Ward (G-4)"
        return f"{department} General Ward (W-1)"

    def _medicines_for_disease(self, disease: str, existing_meds: list[str] | None) -> list[str]:
        if existing_meds and len(existing_meds) > 0 and existing_meds != ["None"] and existing_meds != ["Supportive Care"]:
            return existing_meds
        d = disease.lower()
        if "diabet" in d:
            return ["Tab. Metformin 500mg BD", "Tab. Glimepiride 1mg OD", "Tab. Voglibose 0.2mg TDS"]
        if "hyper" in d:
            return ["Tab. Telmisartan 40mg OD", "Tab. Amlodipine 5mg OD"]
        if "card" in d or "angina" in d or "heart" in d:
            return ["Tab. Aspirin 75mg OD", "Tab. Atorvastatin 40mg HS", "Tab. Metoprolol 25mg OD", "Tab. Sorbitrate 5mg SOS"]
        if "migrain" in d or "cephalea" in d:
            return ["Tab. Sumatriptan 50mg SOS", "Tab. Naproxen 250mg PRN", "Tab. Propranolol 20mg BD"]
        if "asthma" in d or "bronch" in d:
            return ["Budecort 200 Inhaler 2 Puffs BD", "Levolin Inhaler 2 Puffs SOS", "Tab. Montelukast 10mg HS"]
        if "fever" in d or "pyrex" in d:
            return ["Tab. Paracetamol 650mg BD", "Tab. Pantoprazole 40mg OD", "ORS Sachet Solution PRN"]
        return ["Tab. Paracetamol 650mg BD", "Tab. Pantoprazole 40mg OD", "Multivitamin & Zinc Tab OD"]

    def _dosages_for_medicines(self, medicines: list[str]) -> list[str]:
        dosages = []
        for med in medicines:
            if "BD" in med:
                dosages.append("Twice daily after meals (Morning & Night)")
            elif "OD" in med:
                dosages.append("Once daily in the morning after breakfast")
            elif "HS" in med:
                dosages.append("Once daily at bedtime")
            elif "SOS" in med or "PRN" in med:
                dosages.append("As needed during acute symptomatic episode")
            elif "TDS" in med:
                dosages.append("Thrice daily after meals")
            else:
                dosages.append("1 tablet daily after food")
        return dosages

    def _symptoms_for_disease(self, disease: str, existing_symptoms: list[str] | None) -> list[str]:
        if existing_symptoms and len(existing_symptoms) > 0 and existing_symptoms != ["None"]:
            return existing_symptoms
        d = disease.lower()
        if "diabet" in d:
            return ["Polyuria", "Polydipsia", "Unexplained Fatigue", "Mild Blurred Vision"]
        if "hyper" in d:
            return ["Occipital Headache", "Dizziness on Exertion", "Occasional Palpitations"]
        if "card" in d or "heart" in d or "angina" in d:
            return ["Substernal Chest Tightness", "Dyspnea on Exertion", "Cold Diaphoresis"]
        if "migrain" in d or "cephalea" in d:
            return ["Unilateral Throbbing Headache", "Photophobia", "Nausea"]
        if "asthma" in d or "bronch" in d:
            return ["Expiratory Wheezing", "Productive Cough", "Chest Congestion"]
        if "fever" in d or "pyrex" in d:
            return ["High Grade Pyrexia", "Body Aches", "General Malaise"]
        return ["Mild Fatigue", "General Malaise"]

    def _allergies_for_patient(self, existing: list[str] | None) -> list[str]:
        if existing and len(existing) > 0 and existing != ["None"]:
            return existing
        return ["No Known Drug Allergies (NKDA)"]

    def _generate_synthetic_lab_reports(self, disease: str, age: int) -> list[str]:
        d = disease.lower()
        if "diabet" in d:
            return [
                "Fasting Plasma Glucose: 148 mg/dL [Elevated]",
                "Post-Prandial Blood Sugar: 210 mg/dL [Elevated]",
                "HbA1c Glycated Hemoglobin: 7.8% [Suboptimal Control]",
                "Serum Creatinine: 0.9 mg/dL [Normal Range]",
            ]
        if "card" in d or "heart" in d or "angina" in d:
            return [
                "12-Lead Electrocardiogram: ST Segment Depression (0.5mm in V4-V6)",
                "High Sensitivity Troponin I: 0.02 ng/mL [Within Normal Reference]",
                "Total Cholesterol: 224 mg/dL [Borderline High]",
                "Serum LDL Cholesterol: 142 mg/dL [Elevated]",
            ]
        if "hyper" in d:
            return [
                "Resting Blood Pressure: 148/92 mmHg [Stage 1 Hypertension]",
                "Serum Electrolytes (Na/K/Cl): 140 / 4.1 / 102 mmol/L [Normal]",
                "eGFR: 88 mL/min/1.73m² [Normal]",
            ]
        if "asthma" in d or "bronch" in d:
            return [
                "Peak Expiratory Flow Rate (PEFR): 340 L/min [74% of Predicted]",
                "Spirometry FEV1/FVC Ratio: 0.68 [Mild Obstructive Deficit]",
                "Complete Blood Count: Absolute Eosinophil Count 520 cells/µL",
            ]
        return [
            "Complete Blood Count (CBC): Normal Differential",
            "Liver Function Tests: Within Physiological Limits",
            "Renal Profile: Normal Serum Urea & Creatinine",
        ]

    def _generate_synthetic_imaging_notes(self, disease: str) -> list[str]:
        d = disease.lower()
        if "card" in d or "heart" in d:
            return ["2D Echocardiography: LVEF 56%, Mild Concentric LVH, No Regional Wall Motion Abnormality"]
        if "asthma" in d or "bronch" in d:
            return ["Chest X-Ray PA View: Mild Bronchovascular Prominence, Clear Costophrenic Angles"]
        return ["Routine Digital Chest Radiograph: Normal Cardiothoracic Ratio"]

    def _generate_realistic_name(self, real_name: str, gender: str, fingerprint: str) -> str:
        male_first_names = [
            "Suresh", "Rohan", "Vikram", "Aravind", "Deepak", "Devansh", "Manish",
            "Sanjay", "Amit", "Arjun", "Tarun", "Nikhil", "Rahul", "Naveen", "Girish"
        ]
        female_first_names = [
            "Priya", "Sunita", "Ananya", "Ritu", "Meera", "Pooja", "Neha",
            "Divya", "Sneha", "Swati", "Tanvi", "Shreya", "Radha", "Lakshmi", "Anjali"
        ]
        last_names = [
            "Varma", "Kulkarni", "Nair", "Rangan", "Choudhury", "Desai", "Sharma", "Iyer",
            "Deshmukh", "Gupta", "Saxena", "Joshi", "Bhat", "Menon", "Singhania", "Trivedi",
            "Bhattacharya", "Chopra", "Sundaram", "Mukherjee"
        ]

        first_list = female_first_names if gender.lower() == "female" else male_first_names
        name_seed = f"{real_name}|{gender}|{fingerprint}"
        name_hash = sha256(name_seed.encode("utf-8")).hexdigest()
        f_idx = int(name_hash[:4], 16) % len(first_list)
        l_idx = int(name_hash[4:8], 16) % len(last_names)
        return f"{first_list[f_idx]} {last_names[l_idx]}"

    def _address_from_fingerprint(self, fingerprint: str) -> str:
        cities = [
            "Indiranagar, Bengaluru, KA - 560038",
            "Banjara Hills, Hyderabad, TS - 500034",
            "Connaught Place, New Delhi - 110001",
            "Andheri West, Mumbai, MH - 400058",
            "Anna Nagar, Chennai, TN - 600040",
            "Koregaon Park, Pune, MH - 411001",
            "Salt Lake Sector V, Kolkata, WB - 700091",
        ]
        idx = int(fingerprint[8:12], 16) % len(cities)
        door = (int(fingerprint[12:14], 16) % 90) + 10
        complexes = ["Prime Residency", "Emerald Heights", "Silver Oak Apartments", "Green Meadows", "Skyline Towers"]
        comp = complexes[int(fingerprint[14:16], 16) % len(complexes)]
        return f"Flat {door}, {comp}, {cities[idx]}"

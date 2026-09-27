import urllib.request
import json

def test_create():
    login_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/auth/login',
        data=json.dumps({"username": "doctor", "password": "doctor123"}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    token = json.loads(urllib.request.urlopen(login_req).read().decode())['access_token']

    patient_payload = {
        "name": "Rohan Verma",
        "age": 28,
        "date_of_birth": "1998-05-15",
        "gender": "Male",
        "blood_group": "B+",
        "disease": "Acute Bronchitis",
        "diagnosis": "Bacterial Respiratory Infection",
        "medicines": ["Azithromycin 500mg", "Paracetamol 650mg"],
        "dosages": ["1 daily after food"],
        "doctor_assigned": "Dr. Priya Nair (Cardiology)",
        "department": "Cardiology",
        "admission_date": "2026-08-02",
        "phone": "+91 9988776655",
        "email": "rohan@example.com",
        "aadhaar": "9988-7766-5544",
        "emergency_contact": "Father: +91 9988770000",
        "symptoms": ["Cough", "Fever"],
        "allergies": ["None"]
    }

    patient_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/patients',
        data=json.dumps(patient_payload).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'X-Session-Id': 'test-doc-session-001',
            'X-Device': 'trusted',
            'X-Browser': 'chrome'
        }
    )

    res = json.loads(urllib.request.urlopen(patient_req).read().decode())
    print("SUCCESS: Patient created -> Name:", res['patient']['name'], "| Gender:", res['patient'].get('gender'), "| Blood Group:", res['patient'].get('blood_group'), "| Doctor:", res['patient'].get('doctor_assigned'))

if __name__ == '__main__':
    test_create()

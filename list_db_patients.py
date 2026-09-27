import urllib.request
import json

def list_db():
    login_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/auth/login',
        data=json.dumps({"username": "doctor", "password": "doctor123"}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    token = json.loads(urllib.request.urlopen(login_req).read().decode())['access_token']

    p_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/patients',
        headers={
            'Authorization': f'Bearer {token}',
            'X-Session-Id': 'doc-user-session',
            'X-Device': 'trusted'
        }
    )
    patients = json.loads(urllib.request.urlopen(p_req).read().decode())['patients']
    print(f"Total Active Patients Count: {len(patients)}")
    for p in patients:
        print(f"ID: {p.get('id')} | Patient_ID: P-{p.get('patient_id')} | Name: {p.get('name')} | AdmDate: {p.get('admission_date')}")

if __name__ == '__main__':
    list_db()

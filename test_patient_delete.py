import urllib.request
import json

def test_delete():
    login_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/auth/login',
        data=json.dumps({"username": "doctor", "password": "doctor123"}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    token = json.loads(urllib.request.urlopen(login_req).read().decode())['access_token']

    # 1. Create a dummy patient
    create_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/patients',
        data=json.dumps({
            "name": "Test Delete Patient",
            "age": 45,
            "disease": "Hypertension",
            "diagnosis": "Stage 1",
            "medicines": ["Amlodipine"]
        }).encode(),

        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'X-Session-Id': 'delete-test-session',
            'X-Device': 'trusted'
        }
    )
    patient = json.loads(urllib.request.urlopen(create_req).read().decode())['patient']
    patient_id = patient['id']
    print("Created test patient:", patient['name'], "id:", patient_id)

    # 2. Delete the patient
    del_req = urllib.request.Request(
        f'http://127.0.0.1:8001/api/patients/{patient_id}',
        method='DELETE',
        headers={
            'Authorization': f'Bearer {token}',
            'X-Session-Id': 'delete-test-session',
            'X-Device': 'trusted'
        }
    )
    del_res = json.loads(urllib.request.urlopen(del_req).read().decode())
    print("Delete API Result:", del_res['message'])

    # 3. Fetch history
    hist_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/patients/history',
        headers={
            'Authorization': f'Bearer {token}',
            'X-Session-Id': 'delete-test-session',
            'X-Device': 'trusted'
        }
    )
    hist_res = json.loads(urllib.request.urlopen(hist_req).read().decode())
    print("History Records Count:", len(hist_res['history']))
    if len(hist_res['history']) > 0:
        print("Latest Archived Patient in History:", hist_res['history'][0]['name'], "| Status:", hist_res['history'][0].get('status'))

if __name__ == '__main__':
    test_delete()

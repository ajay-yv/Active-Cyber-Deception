import urllib.request
import json

def test_lab():
    login_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/auth/login',
        data=json.dumps({"username": "doctor", "password": "doctor123"}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    token = json.loads(urllib.request.urlopen(login_req).read().decode())['access_token']

    lab_req = urllib.request.Request(
        'http://127.0.0.1:8001/api/integration/lab-results/P-1001',
        headers={
            'Authorization': f'Bearer {token}',
            'X-Session-Id': 'doc-user-session',
            'X-Device': 'trusted',
            'X-Browser': 'chrome'
        }
    )
    res = json.loads(urllib.request.urlopen(lab_req).read().decode())
    print("SUCCESS: Lab result fetched ->", res)

if __name__ == '__main__':
    test_lab()

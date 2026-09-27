import urllib.request
import json

def test_dashboards():
    roles = ['doctor', 'reception', 'admin']
    for username in roles:
        password = username + '123'
        try:
            login_req = urllib.request.Request(
                'http://127.0.0.1:8001/api/auth/login',
                data=json.dumps({"username": username, "password": password}).encode(),
                headers={'Content-Type': 'application/json'}
            )
            token = json.loads(urllib.request.urlopen(login_req).read().decode())['access_token']

            for kind in ['admin', 'hospital']:
                dash_req = urllib.request.Request(
                    f'http://127.0.0.1:8001/api/dashboard/{kind}',
                    headers={
                        'Authorization': f'Bearer {token}',
                        'X-Session-Id': f'{username}-session-1',
                        'X-Device': 'trusted'
                    }
                )
                res = json.loads(urllib.request.urlopen(dash_req).read().decode())
                print(f"SUCCESS: [{username}] -> /api/dashboard/{kind}: total_patients={res['metrics']['total_patients']}")
        except Exception as e:
            print(f"FAILED: [{username}] -> error: {e}")

if __name__ == '__main__':
    test_dashboards()

"""Frontend smoke checks: fetch dev server pages and verify key UI markers,
then perform API-driven login and workflow checks to emulate end-to-end flows.
"""
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEV_BASES = ["http://localhost:3000", "http://127.0.0.1:3000"]
API_BASE = "http://127.0.0.1:8000"


def req_url(url, method="GET", headers=None, data=None):
    h = {"User-Agent": "smoke-test/1.0"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=h, method=method)
    try:
        with urlopen(req, timeout=10) as resp:
            content = resp.read()
            return resp.getcode(), content
    except HTTPError as e:
        try:
            body = e.read().decode('utf-8')
            return e.code, body
        except Exception:
            return e.code, str(e)
    except URLError as e:
        return None, str(e)


def ensure(cond, msg):
    if not cond:
        print('ERROR:', msg)
        sys.exit(2)

print('Checking dev server home and pages...')
for host in DEV_BASES:
    try:
        code, body = req_url(host + '/')
        if code == 200:
            DEV_BASE = host
            break
    except Exception:
        continue
else:
    ensure(False, 'Dev server not reachable on localhost or 127.0.0.1:3000')

for p in ['/', '/index.html', '/index.user.html', '/index.hacker.html', '/admin', '/hacker']:
    url = DEV_BASE + p
    code, body = req_url(url)
    ensure(code == 200, f"Dev page {p} not reachable: {code}")
    text = body.decode('utf-8') if isinstance(body, bytes) else str(body)
    print(f"OK {p} — {len(text)} bytes")

print('\nVerifying main UI markers in home page')
code, body = req_url(DEV_BASE + '/')
text = body.decode('utf-8')
ensure('Healthcare Cyber Deception' in text, 'Home page title missing')
ensure('Admin/User Dashboard' in text and 'Hacker Dashboard' in text, 'Landing links missing')
print('Home page markers OK')

# Backend-driven workflow checks similar to backend smoke test
print('\nRunning API-driven workflow checks (login, dashboards, patient create)')

def api_req(path, method='GET', token=None, data=None, headers=None):
    url = API_BASE + path
    h = headers.copy() if headers else {}
    if token:
        h['Authorization'] = f'Bearer {token}'
    return req_url(url, method=method, headers=h, data=data)

# login admin
code, body = api_req('/api/auth/login', method='POST', data={'username': 'admin','password': 'admin123'})
ensure(code == 200, 'Admin login failed')
admin = json.loads(body.decode('utf-8'))
admin_token = admin.get('access_token')
ensure(admin_token, 'No admin token')
print('Admin login OK')

# login hacker
code, body = api_req('/api/auth/login', method='POST', data={'username': 'hacker','password': 'hacker123'})
ensure(code == 200, 'Hacker login failed')
hacker = json.loads(body.decode('utf-8'))
hacker_token = hacker.get('access_token')
ensure(hacker_token, 'No hacker token')
print('Hacker login OK')

# fetch dashboards
code, body = api_req('/api/dashboard/admin', token=admin_token)
ensure(code == 200, 'Admin dashboard API failed')
print('Admin dashboard API OK')

code, body = api_req('/api/dashboard/hacker', token=hacker_token)
ensure(code == 200, 'Hacker dashboard API failed')
print('Hacker dashboard API OK')

# create patient
patient_payload = {"name": "FE Smoke Patient", "age": 30, "disease": "Test", "diagnosis": "FE", "medicines": ["None"], "treatment_pattern": "Standard"}
code, body = api_req('/api/patients', method='POST', token=admin_token, data=patient_payload, headers={'X-Session-Id': 'fe-smoke-1'})
ensure(code == 200, 'Patient creation failed')
print('Patient creation via API OK')

print('\nFrontend smoke checks complete')
sys.exit(0)

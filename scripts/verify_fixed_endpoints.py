import httpx

client = httpx.Client(timeout=10.0)

# Test with Doctor account
doc_login = client.post('http://localhost:8000/api/auth/login', json={'username': 'doctor', 'password': 'doctor123'})
doc_token = doc_login.json()['access_token']
print(f"[AUTH] Doctor Login: {doc_login.status_code}")

# 1. Test Autonomous Teardown
teardown_res = client.post(
    'http://localhost:8000/api/security/ado/teardown',
    json={'session_id': 'test-session-01', 'reason': 'Manual test trigger'},
    headers={'Authorization': f'Bearer {doc_token}'},
)
print(f"[1/4] Autonomous Teardown Status: {teardown_res.status_code} | Body: {teardown_res.json()}")
assert teardown_res.status_code == 200, f"Teardown failed: {teardown_res.text}"

# 2. Test Deploy Attractive Lure
lure_res = client.post(
    'http://localhost:8000/api/security/ado/lures/deploy',
    json={'session_id': 'test-session-01', 'lure_type': 'vip_executive_record'},
    headers={'Authorization': f'Bearer {doc_token}'},
)
print(f"[2/4] Deploy Attractive Lure Status: {lure_res.status_code} | Status Field: {lure_res.json().get('status')}")
assert lure_res.status_code == 200, f"Lure deploy failed: {lure_res.text}"

# 3. Test Forensics Scan
scan_res = client.post(
    'http://localhost:8000/api/security/forensics/scan',
    json={'raw_content': 'Patient medical report snippet'},
    headers={'Authorization': f'Bearer {doc_token}'},
)
print(f"[3/4] Forensics Scan Status: {scan_res.status_code} | Body: {scan_res.json()}")
assert scan_res.status_code == 200, f"Forensics scan failed: {scan_res.text}"

# 4. Test Export Audit Logs
export_res = client.get(
    'http://localhost:8000/api/audit/export',
    headers={'Authorization': f'Bearer {doc_token}'},
)
print(f"[4/4] Export Audit Logs Status: {export_res.status_code} | Content-Length: {len(export_res.content)} bytes | Type: {export_res.headers.get('content-type')}")
assert export_res.status_code == 200, f"Export audit logs failed: {export_res.text}"

print("\n=======================================================")
print("ALL 4 PREVIOUSLY FAILING ENDPOINTS FIXED & VERIFIED 100%!")
print("=======================================================")

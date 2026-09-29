"""Bounded local-only cyber-range traffic generator for the EHR development server."""

from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import cycle
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_TARGET = "http://127.0.0.1:8000"
DUMMY_USERNAME = "hacker"
DUMMY_PASSWORD = "hacker123"
DUMMY_USERS = ("test-user-01", "test-user-02", "test-user-03", "test-user-04")
MAX_REQUESTS = 100
MAX_RECORDS = 25
MIN_INTERVAL_SECONDS = 0.05


def validate_target(target: str, allow_private_network: bool = False) -> str:
    import ipaddress
    from urllib.parse import urlparse

    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("target must use http or https")

    hostname = (parsed.hostname or "").lower()
    is_valid = False
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        is_valid = True
    else:
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback:
                is_valid = True
        except ValueError:
            is_valid = False

    if not is_valid:
        raise ValueError(f"target '{target}' must be localhost, 127.0.0.1, or a private local network IP (e.g. 192.168.x.x, 10.x.x.x)")
    if hostname not in {"localhost", "127.0.0.1", "::1"} and not allow_private_network:
        raise ValueError("private-network targets require --allow-private-network")
    if parsed.username or parsed.password or not parsed.netloc:
        raise ValueError("target must not contain credentials")
    return target.rstrip("/")


def bounded(value: int, limit: int, label: str) -> int:
    if value < 1 or value > limit:
        raise ValueError(f"{label} must be between 1 and {limit}")
    return value


def request(
    target: str,
    path: str,
    method: str = "GET",
    payload: dict | None = None,
    token: str | None = None,
    session_id: str = "sim-session",
) -> tuple[int, dict | str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "ehr-security-simulator/1.0",
        "X-Session-Id": session_id,
        "X-Device": "simulation",
        "X-Browser": "python-requests",
        "X-OS": "test",
        "Connection": "close",
    }
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{target}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=25) as response:
            raw = response.read().decode("utf-8")
            try:
                return response.status, json.loads(raw)
            except json.JSONDecodeError:
                return response.status, raw
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw
    except URLError as exc:
        raise RuntimeError(f"Could not reach local target: {exc.reason}") from exc


def login(target: str, username: str = DUMMY_USERNAME, password: str = DUMMY_PASSWORD) -> str | None:
    status, response = request(target, "/api/auth/login", "POST", {"username": username, "password": password})
    if status != 200 or not isinstance(response, dict):
        return None
    return response.get("access_token")


def _clean_disease_name(raw_disease: str | None) -> str:
    if not raw_disease:
        return ""
    return str(raw_disease).strip()


def _clean_patient_id(raw_pid: str | None) -> str:
    if not raw_pid:
        return ""
    return str(raw_pid).strip()


def _clean_name(raw_name: str | None) -> str:
    if not raw_name:
        return ""
    return str(raw_name).strip()


def _format_response_summary(res: dict | str) -> str:
    if isinstance(res, dict):
        if "patient" in res and isinstance(res["patient"], dict):
            p = res["patient"]
            pid = _clean_patient_id(p.get("synthetic_patient_id") or p.get("id"))
            pname = _clean_name(p.get("name"))
            pdiag = p.get("diagnosis", "")
            return f"Patient Record (ID: {pid}, Name: '{pname}', Diagnosis: '{pdiag}')"
        if "patients" in res and isinstance(res["patients"], list):
            count = len(res["patients"])
            names = ", ".join(f"'{_clean_name(p.get('name', ''))}'" for p in res["patients"][:3])
            return f"{count} clinical records retrieved | Sample: [{names}]"
        if "detail" in res:
            return f"Detail: {res['detail']}"
        if "status" in res:
            return f"Status: {res['status']}"
        if "risk_score" in res:
            return f"Security Risk Score: {res['risk_score']}%"
    return str(res)[:60]


def _print_extracted_patient(header: str, patient_data: dict | None) -> None:
    if not patient_data:
        print(f"             {header} No persisted synthetic twin was available.")
        return
    data = patient_data or {}
    pid = _clean_patient_id(data.get("patient_id") or data.get("id") or data.get("synthetic_patient_id"))
    name = _clean_name(data.get("name") or data.get("fake_name"))
    disease = _clean_disease_name(data.get("disease") or data.get("fake_disease"))
    diagnosis = data.get("diagnosis") or ""
    doctor = data.get("doctor_assigned") or data.get("doctor") or ""
    gender = data.get("gender") or ""
    age = str(data.get("age_range") or data.get("age") or "")
    raw_wm = data.get("watermark_id")
    checksum = raw_wm or ""

    print("             --------------------------------------------------")
    print(f"             {header}")
    print("             [EXTRACTED CLINICAL EHR PAYLOAD]:")
    print(f"             - Patient ID:          {pid}")
    print(f"             - Patient Name:        {name}")
    print(f"             - Demographics:        {age} yrs • {gender}")
    print(f"             - Primary Condition:   {disease}")
    print(f"             - Clinical Diagnosis:  {diagnosis}")
    print(f"             - Attending Doctor:    {doctor}")
    print(f"             - Record Checksum:     {checksum}")
    print("             --------------------------------------------------")


def run_attack(args: argparse.Namespace) -> None:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    target = validate_target(args.target, allow_private_network=args.allow_private_network)
    attack_name = "sql-injection" if args.attack == "sqli" else args.attack
    session_id = args.session or f"sim-{attack_name}"
    interval = max(args.interval, MIN_INTERVAL_SECONDS)
    token = None

    user_count = args.count
    attempts = args.attempts if args.attempts is not None else (user_count if user_count is not None else 20)
    enum_count = args.count if args.count is not None else 20
    requests_cnt = args.requests if args.requests is not None else (user_count if user_count is not None else 30)
    records_cnt = args.records if args.records is not None else (user_count if user_count is not None else 10)

    print(f"[SIMULATION] Starting '{attack_name}' attack on {target} (Session: {session_id})")

    if attack_name not in {"brute-force", "credential-stuffing"}:
        token = login(target)
        if not token:
            raise RuntimeError("The seeded dummy hacker account could not authenticate")

    if attack_name == "brute-force":
        total = bounded(attempts, MAX_REQUESTS, "attempts")
        for index in range(1, total + 1):
            pwd = f"dummy-invalid-{index}"
            status, res = request(
                target,
                "/api/auth/login",
                "POST",
                {"username": DUMMY_USERNAME, "password": pwd},
                session_id=session_id,
            )
            summary = _format_response_summary(res)
            print(f"[SIMULATION] [{index}/{total}] POST /api/auth/login (user: {DUMMY_USERNAME}) -> HTTP {status} ({summary})")
            time.sleep(interval)

        probe_token = login(target)
        _, res = request(target, "/api/patients?patient_id=P-01", token=probe_token, session_id=session_id)
        decoy = res.get("patient") if isinstance(res, dict) else None
        _print_extracted_patient("[HACKER DATA EXTRACTION PROBE AFTER BRUTE FORCE]:", decoy)

    elif attack_name == "credential-stuffing":
        total = bounded(attempts, MAX_REQUESTS, "attempts")
        user_iter = cycle(DUMMY_USERS)
        for index in range(1, total + 1):
            username = next(user_iter)
            status, res = request(
                target,
                "/api/auth/login",
                "POST",
                {"username": username, "password": "dummy-invalid-password"},
                session_id=session_id,
            )
            summary = _format_response_summary(res)
            print(f"[SIMULATION] [{index}/{total}] POST /api/auth/login (user: {username}) -> HTTP {status} ({summary})")
            time.sleep(interval)

        probe_token = login(target)
        _, res = request(target, "/api/patients?patient_id=P-01", token=probe_token, session_id=session_id)
        decoy = res.get("patient") if isinstance(res, dict) else None
        _print_extracted_patient("[HACKER DATA EXTRACTION PROBE AFTER CREDENTIAL STUFFING]:", decoy)

    elif attack_name == "enumeration":
        total = bounded(enum_count, MAX_RECORDS, "count")
        for index in range(1, total + 1):
            path = f"/api/patients?patient_id=P-{index:02d}"
            status, res = request(target, path, token=token, session_id=session_id)
            summary = _format_response_summary(res)
            print(f"[SIMULATION] [{index}/{total}] GET {path} -> HTTP {status}")
            if isinstance(res, dict) and "patient" in res and isinstance(res["patient"], dict):
                p = res["patient"]
                _print_extracted_patient(f"[HACKER RETRIEVED RECORD FOR {path}]:", p)
            else:
                print(f"             ({summary})")
            time.sleep(interval)

    elif attack_name == "api-abuse":
        total = bounded(requests_cnt, MAX_REQUESTS, "requests")
        for index in range(1, total + 1):
            path = "/api/dashboard"
            status, res = request(target, path, token=token, session_id=session_id)
            summary = _format_response_summary(res)
            print(f"[SIMULATION] [{index}/{total}] GET {path} -> HTTP {status} ({summary})")
            time.sleep(interval)

        _, res = request(target, "/api/patients?patient_id=P-01", token=token, session_id=session_id)
        decoy = res.get("patient") if isinstance(res, dict) else None
        _print_extracted_patient("[HACKER DATA EXTRACTION PROBE AFTER API ABUSE]:", decoy)

    elif attack_name in {"patient", "single", "single-patient", "1"}:
        pat_id = getattr(args, "patient_id", None) or getattr(args, "patient", None) or (f"P-{args.count:02d}" if args.count else "P-01")
        path = f"/api/patients?patient_id={pat_id}"
        status, res = request(target, path, token=token, session_id=session_id)
        summary = _format_response_summary(res)
        print(f"[SIMULATION] [1/1] GET {path} -> HTTP {status} ({summary})")
        decoy = res.get("patient") if isinstance(res, dict) else (res.get("patients", [{}])[0] if isinstance(res, dict) and res.get("patients") else None)
        _print_extracted_patient(f"[HACKER RETRIEVED 1 RECORD FOR {path}]:", decoy)
        print(f"             [SYNTHETIC OUTPUT] Records requested: 1 | Synthetic records returned: {1 if decoy else 0}")

    elif attack_name == "exfiltration":
        dump_count = bounded(records_cnt, MAX_RECORDS, "count")
        path = f"/api/patients?limit={dump_count}"
        status, res = request(target, path, token=token, session_id=session_id)
        summary = _format_response_summary(res)
        print(f"[SIMULATION] [1/1] GET {path} -> HTTP {status} ({summary})")
        if isinstance(res, dict) and "patients" in res and isinstance(res["patients"], list):
            dumped_records = res["patients"][:dump_count]
            print(f"             [SYNTHETIC OUTPUT] Records requested: {dump_count} | Synthetic records returned: {len(dumped_records)}")
            for p in dumped_records:
                c_name = _clean_name(p.get("name"))
                c_disease = _clean_disease_name(p.get("disease"))
                pid = _clean_patient_id(p.get("synthetic_patient_id") or p.get("id"))
                checksum = p.get("watermark_id") or ""
                print(f"             - Patient Record: [{pid}] {c_name} | {c_disease} | Verification Hash: {checksum}")

    elif attack_name == "session-abuse":
        total = bounded(requests_cnt, MAX_REQUESTS, "requests")
        for index in range(1, total + 1):
            path = "/api/patients"
            status, res = request(target, path, token="invalid-test-token", session_id=session_id)
            summary = _format_response_summary(res)
            print(f"[SIMULATION] [{index}/{total}] GET {path} with invalid token -> HTTP {status} ({summary})")
            time.sleep(interval)

        _, res = request(target, "/api/patients?patient_id=P-01", token=token, session_id=session_id)
        decoy = res.get("patient") if isinstance(res, dict) else None
        _print_extracted_patient("[HACKER DATA PROBE AFTER FORGED SESSION REJECTION]:", decoy)

    elif attack_name in {"sql-injection", "traversal"}:
        marker = "TEST_SQL_INJECTION" if attack_name == "sql-injection" else "TEST_TRAVERSAL"
        status, res = request(
            target,
            "/api/security/simulation/marker",
            "POST",
            {"marker": marker},
            token=token,
            session_id=session_id,
        )
        summary = _format_response_summary(res)
        print(f"[SIMULATION] [1/1] POST /api/security/simulation/marker ({marker}) -> HTTP {status} ({summary})")

        decoy = None
        if isinstance(res, dict) and "deceptive_payload" in res:
            decoy = res["deceptive_payload"].get("sample_decoy")
        if not decoy:
            _, syn_res = request(target, "/api/patients?patient_id=P-01", token=token, session_id=session_id)
            if isinstance(syn_res, dict) and "patient" in syn_res:
                decoy = syn_res["patient"]
        label = "SQL INJECTION DUMP" if attack_name == "sql-injection" else "DIRECTORY TRAVERSAL EXFILTRATION"
        _print_extracted_patient(f"[HACKER RECEIVED {label}]:", decoy)

    else:
        raise ValueError(f"unsupported attack: {args.attack}")

    # Emit simulation finish notification silently
    try:
        request(
            target,
            "/api/security/simulation/finish",
            "POST",
            {"attack": attack_name, "session_id": session_id, "target": target},
            token=token,
            session_id=session_id,
        )
    except Exception:
        pass


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Generate bounded cyber-range traffic against a local EHR server")
    result.add_argument(
        "--attack",
        required=True,
        choices=[
            "brute-force",
            "enumeration",
            "api-abuse",
            "sql-injection",
            "sqli",
            "traversal",
            "exfiltration",
            "credential-stuffing",
            "session-abuse",
            "patient",
            "single",
            "single-patient",
            "1",
        ],
        help="Type of attack simulation to execute",
    )
    result.add_argument("--patient", default=None, help="Target patient ID for single-patient attacks (e.g. P-01)")
    result.add_argument("--patient-id", dest="patient_id", default=None, help="Target exactly one patient (e.g. P-01)")
    result.add_argument("--target", default=DEFAULT_TARGET, help=f"Target URL (must be loopback, default: {DEFAULT_TARGET})")
    result.add_argument("--allow-private-network", action="store_true", help="Explicitly allow a private LAN target such as 192.168.1.25")
    result.add_argument("--attempts", type=int, default=None, help="Number of attempts for login-based attacks (max 100)")
    result.add_argument("--count", type=int, default=None, help="Universal count or number of patient IDs to enumerate (max 25)")
    result.add_argument("--requests", type=int, default=None, help="Number of requests for API abuse or session abuse (max 100)")
    result.add_argument("--records", type=int, default=None, help="Number of exfiltration batch queries (max 25)")
    result.add_argument("--interval", type=float, default=MIN_INTERVAL_SECONDS, help="Delay between requests in seconds")
    result.add_argument("--session", help="Custom session ID string")
    return result


if __name__ == "__main__":
    try:
        run_attack(parser().parse_args())
    except (ValueError, RuntimeError) as exc:
        print(f"security simulator: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
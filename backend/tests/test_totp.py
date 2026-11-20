from app.services.security import verify_totp


def test_verify_totp_accepts_current_time_step(monkeypatch) -> None:
    monkeypatch.setattr("app.services.security.time.time", lambda: 59)

    assert verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "287082")


def test_verify_totp_accepts_adjacent_time_step_by_default(monkeypatch) -> None:
    monkeypatch.setattr("app.services.security.time.time", lambda: 59)

    assert verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "359152")


def test_verify_totp_rejects_invalid_or_malformed_input(monkeypatch) -> None:
    monkeypatch.setattr("app.services.security.time.time", lambda: 59)

    assert not verify_totp("invalid-secret", "287082")
    assert not verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "123")
    assert not verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "287082", valid_window=-1)

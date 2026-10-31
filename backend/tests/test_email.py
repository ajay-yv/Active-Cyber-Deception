import json
from urllib.error import HTTPError

from app.core.settings import Settings
from app.services import email


def test_email_delivery_is_configured_with_resend_or_smtp() -> None:
    assert email.email_delivery_configured(
        Settings(
            resend_api_key="re_test_key",
            resend_from_address="Portal <otp@example.org>",
        )
    )
    assert email.email_delivery_configured(
        Settings(smtp_user="smtp-user", smtp_pass="smtp-password")
    )
    assert not email.email_delivery_configured(Settings())


def test_send_otp_email_uses_resend_api(monkeypatch) -> None:
    settings = Settings(
        resend_api_key="re_test_key",
        resend_from_address="Portal <otp@example.org>",
    )
    monkeypatch.setattr(email, "get_settings", lambda: settings)
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(email, "urlopen", fake_urlopen)

    assert email.send_otp_email("patient@example.org", "123456", "Patient")

    request = captured["request"]
    assert request.full_url == "https://api.resend.com/emails"
    assert request.get_header("Authorization") == "Bearer re_test_key"
    assert request.get_header("Content-type") == "application/json"
    assert captured["timeout"] == 10
    body = json.loads(request.data)
    assert body["from"] == "Portal <otp@example.org>"
    assert body["to"] == ["patient@example.org"]
    assert body["text"].find("123456") >= 0
    assert "123456" in body["html"]


def test_send_otp_email_returns_false_for_resend_rejection(monkeypatch) -> None:
    settings = Settings(
        resend_api_key="re_test_key",
        resend_from_address="Portal <otp@example.org>",
    )
    monkeypatch.setattr(email, "get_settings", lambda: settings)

    def reject_request(_request, timeout):
        raise HTTPError(
            "https://api.resend.com/emails",
            401,
            "unauthorized",
            {},
            None,
        )

    monkeypatch.setattr(email, "urlopen", reject_request)

    assert not email.send_otp_email("patient@example.org", "123456")


def test_resend_settings_are_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("RESEND_FROM_ADDRESS", "Portal <otp@example.org>")

    settings = Settings(_env_file=None)

    assert settings.resend_api_key == "re_test_key"
    assert settings.resend_from_address == "Portal <otp@example.org>"

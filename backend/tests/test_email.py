import json
from io import BytesIO
from urllib.error import HTTPError

from app.core.settings import Settings
from app.services import email


def test_email_delivery_is_configured_with_brevo_resend_or_smtp() -> None:
    assert email.email_delivery_configured(
        Settings(
            _env_file=None,
            brevo_api_key="test-brevo-key",
            brevo_email_sender="otp@example.org",
        )
    )
    assert email.email_delivery_configured(
        Settings(
            _env_file=None,
            resend_api_key="re_test_key",
            resend_from_address="Portal <otp@example.org>",
        )
    )
    assert email.email_delivery_configured(
        Settings(_env_file=None, smtp_user="smtp-user", smtp_pass="smtp-password")
    )
    assert not email.email_delivery_configured(Settings(_env_file=None))


def test_send_otp_email_uses_brevo_api_when_configured(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        brevo_api_key="test-brevo-key",
        brevo_email_sender="otp@example.org",
        brevo_email_sender_name="EHR Portal",
        resend_api_key="re_test_key",
        resend_from_address="Portal <otp@example.org>",
    )
    monkeypatch.setattr(email, "get_settings", lambda: settings)
    captured = {}

    class FakeResponse:
        status = 201

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
    assert request.full_url == "https://api.brevo.com/v3/smtp/email"
    assert request.get_header("Api-key") == "test-brevo-key"
    assert request.get_header("Content-type") == "application/json"
    assert captured["timeout"] == 10
    body = json.loads(request.data)
    assert body["sender"] == {"email": "otp@example.org", "name": "EHR Portal"}
    assert body["to"] == [{"email": "patient@example.org", "name": "Patient"}]
    assert "123456" in body["textContent"]
    assert "123456" in body["htmlContent"]


def test_send_otp_email_uses_resend_api(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
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
        _env_file=None,
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


def test_send_otp_email_logs_brevo_rejection_code_without_credentials(
    monkeypatch,
    caplog,
) -> None:
    settings = Settings(
        _env_file=None,
        brevo_api_key="test-brevo-key",
        brevo_email_sender="otp@example.org",
    )
    monkeypatch.setattr(email, "get_settings", lambda: settings)

    def reject_request(_request, timeout):
        raise HTTPError(
            "https://api.brevo.com/v3/smtp/email",
            401,
            "unauthorized",
            {},
            BytesIO(
                b'{"code":"unauthorized","message":"Unrecognised IP address 203.0.113.1"}'
            ),
        )

    monkeypatch.setattr(email, "urlopen", reject_request)

    assert not email.send_otp_email("patient@example.org", "123456")
    assert "status=401" in caplog.text
    assert "code=unauthorized" in caplog.text
    assert "reason=ip_not_authorized" in caplog.text
    assert "203.0.113.1" not in caplog.text
    assert "test-brevo-key" not in caplog.text


def test_send_otp_email_falls_back_to_next_configured_provider(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        brevo_api_key="test-brevo-key",
        brevo_email_sender="otp@example.org",
        resend_api_key="re_test_key",
        resend_from_address="Portal <otp@example.org>",
        smtp_user="smtp-user",
        smtp_pass="smtp-password",
    )
    monkeypatch.setattr(email, "get_settings", lambda: settings)
    attempted = []

    def reject_brevo(*_args):
        attempted.append("Brevo")
        return False

    def reject_resend(*_args):
        attempted.append("Resend")
        return False

    def accept_smtp(*_args):
        attempted.append("SMTP")
        return True

    monkeypatch.setattr(email, "_send_brevo_email", reject_brevo)
    monkeypatch.setattr(email, "_send_resend_email", reject_resend)
    monkeypatch.setattr(email, "_send_smtp_email", accept_smtp)

    assert email.send_otp_email("patient@example.org", "123456")
    assert attempted == ["Brevo", "Resend", "SMTP"]


def test_resend_settings_are_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("RESEND_FROM_ADDRESS", "Portal <otp@example.org>")

    settings = Settings(_env_file=None)

    assert settings.resend_api_key == "re_test_key"
    assert settings.resend_from_address == "Portal <otp@example.org>"


def test_brevo_settings_are_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("BREVO_API_KEY", "environment-key")
    monkeypatch.setenv("BREVO_EMAIL_SENDER", "otp@example.org")
    monkeypatch.setenv("BREVO_EMAIL_SENDER_NAME", "EHR")

    settings = Settings(_env_file=None)

    assert settings.brevo_api_key == "environment-key"
    assert settings.brevo_email_sender == "otp@example.org"
    assert settings.brevo_email_sender_name == "EHR"

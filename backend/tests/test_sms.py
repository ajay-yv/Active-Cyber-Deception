import json
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

from app.core.settings import Settings
from app.services import sms


def test_sms_defaults_to_brevo(monkeypatch) -> None:
    monkeypatch.delenv("OTP_SMS_PROVIDER", raising=False)

    assert Settings(_env_file=None).otp_sms_provider == "brevo"


def test_sms_uses_twilio_api_key_credentials_when_configured(monkeypatch) -> None:
    settings = Settings(
        otp_sms_provider="twilio",
        twilio_account_sid="AC-test-account",
        twilio_api_key_sid="SK-test-key",
        twilio_api_key_secret="test-api-key-secret",
        twilio_from_number="+15005550006",
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)
    captured: dict[str, object] = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured["message"] = kwargs
            return type("Message", (), {"sid": "SM-test-message"})()

    class FakeClient:
        def __init__(self, username, password, *, account_sid=None):
            captured["credentials"] = (username, password)
            captured["account_sid"] = account_sid
            self.messages = FakeMessages()

    monkeypatch.setattr(sms, "Client", FakeClient)

    assert sms.send_otp_sms("+919876543210", "123456")

    assert captured["credentials"] == ("SK-test-key", "test-api-key-secret")
    assert captured["account_sid"] == "AC-test-account"
    assert captured["message"] == {
        "to": "+919876543210",
        "from_": "+15005550006",
        "body": "Your Healthcare EHR verification code is 123456. It expires in 5 minutes.",
    }


def test_sms_uses_twilio_account_token_when_api_key_is_not_configured(
    monkeypatch,
) -> None:
    settings = Settings(
        otp_sms_provider="twilio",
        twilio_account_sid="AC-test-account",
        twilio_auth_token="test-auth-token",
        twilio_from_number="+15005550006",
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)
    captured = {}

    class FakeMessages:
        def create(self, **_kwargs):
            return type("Message", (), {"sid": "SM-test-message"})()

    class FakeClient:
        def __init__(self, username, password, **kwargs):
            captured["credentials"] = (username, password)
            captured["kwargs"] = kwargs
            self.messages = FakeMessages()

    monkeypatch.setattr(sms, "Client", FakeClient)

    assert sms.send_otp_sms("+919876543210", "123456")
    assert captured["credentials"] == ("AC-test-account", "test-auth-token")
    assert captured["kwargs"] == {}


def test_sms_accepts_auth_token_when_api_key_is_not_configured(monkeypatch) -> None:
    settings = Settings(
        twilio_account_sid="AC-test-account",
        twilio_auth_token="test-auth-token",
        twilio_from_number="+15005550006",
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)

    assert sms.missing_twilio_settings(settings) == []


def test_sms_reports_missing_api_key_pair_member() -> None:
    settings = Settings(
        twilio_account_sid="AC-test-account",
        twilio_api_key_sid="SK-test-key",
        twilio_from_number="+15005550006",
    )

    assert sms.missing_twilio_settings(settings) == ["TWILIO_API_KEY_SECRET"]


def test_sms_uses_brevo_when_selected(monkeypatch) -> None:
    settings = Settings(
        otp_sms_provider="brevo",
        brevo_api_key="test-brevo-key",
        brevo_sms_sender="EHRPortal",
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)
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

    monkeypatch.setattr(sms, "urlopen", fake_urlopen)

    assert sms.send_otp_sms("9876543210", "123456")

    request = captured["request"]
    assert request.full_url == "https://api.brevo.com/v3/transactionalSMS/sms"
    assert request.get_header("Api-key") == "test-brevo-key"
    assert request.get_header("Content-type") == "application/json"
    assert captured["timeout"] == 10
    assert json.loads(request.data) == {
        "sender": "EHRPortal",
        "recipient": "+919876543210",
        "content": "Your Healthcare EHR verification code is 123456. It expires in 5 minutes.",
        "type": "transactional",
    }


def test_brevo_sms_reports_missing_settings_and_rejected_response(monkeypatch) -> None:
    settings = Settings(otp_sms_provider="brevo", _env_file=None)
    monkeypatch.setattr(sms, "get_settings", lambda: settings)

    assert sms.missing_sms_settings(settings) == [
        "BREVO_API_KEY",
        "BREVO_SMS_SENDER",
    ]
    assert not sms.send_otp_sms("+919876543210", "123456")

    configured = Settings(
        otp_sms_provider="brevo",
        brevo_api_key="test-brevo-key",
        brevo_sms_sender="EHRPortal",
        _env_file=None,
    )
    monkeypatch.setattr(sms, "get_settings", lambda: configured)

    def reject_request(_request, timeout):
        raise HTTPError(
            "https://api.brevo.com/v3/transactionalSMS/sms",
            401,
            "unauthorized",
            {},
            None,
        )

    monkeypatch.setattr(sms, "urlopen", reject_request)

    assert not sms.send_otp_sms("+919876543210", "123456")


def test_brevo_sms_rejects_unregistered_sender_formats() -> None:
    for sender in ("", "EHR Portal", "ER", "SenderNameTooLong"):
        settings = Settings(
            otp_sms_provider="brevo",
            brevo_api_key="test-key",
            brevo_sms_sender=sender,
            _env_file=None,
        )

        assert sms.missing_sms_settings(settings) == ["BREVO_SMS_SENDER"]

    for sender in ("EHRPortal", "123456789012"):
        settings = Settings(
            otp_sms_provider="brevo",
            brevo_api_key="test-key",
            brevo_sms_sender=sender,
            _env_file=None,
        )

        assert sms.missing_sms_settings(settings) == []


def test_brevo_sms_logs_safe_delivery_failure_reason(monkeypatch, caplog) -> None:
    settings = Settings(
        otp_sms_provider="brevo",
        brevo_api_key="test-key",
        brevo_sms_sender="EHRPortal",
        _env_file=None,
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)

    def reject_request(_request, timeout):
        raise HTTPError(
            "https://api.brevo.com/v3/transactionalSMS/sms",
            402,
            "payment required",
            {},
            BytesIO(b'{"code":"not_enough_credits","message":"Sensitive provider details"}'),
        )

    monkeypatch.setattr(sms, "urlopen", reject_request)

    assert not sms.send_otp_sms("+919876543210", "123456")
    assert "status=402" in caplog.text
    assert "code=not_enough_credits" in caplog.text
    assert "reason=insufficient_credits" in caplog.text
    assert "+919876543210" not in caplog.text
    assert "123456" not in caplog.text
    assert "Sensitive provider details" not in caplog.text


def test_brevo_sms_logs_unapproved_sender_without_provider_message(
    monkeypatch,
    caplog,
) -> None:
    settings = Settings(
        otp_sms_provider="brevo",
        brevo_api_key="test-key",
        brevo_sms_sender="EHRPortal",
        _env_file=None,
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)

    def reject_request(_request, timeout):
        raise HTTPError(
            "https://api.brevo.com/v3/transactionalSMS/sms",
            400,
            "bad request",
            {},
            BytesIO(
                b'{"code":"invalid_parameter","message":"Sender is not approved"}'
            ),
        )

    monkeypatch.setattr(sms, "urlopen", reject_request)

    assert not sms.send_otp_sms("+919876543210", "123456")
    assert "reason=sender_not_accepted" in caplog.text
    assert "Sender is not approved" not in caplog.text


def test_sms_uses_msg91_otp_api_when_selected(monkeypatch) -> None:
    settings = Settings(
        otp_sms_provider="msg91",
        msg91_auth_key="test-msg91-key",
        msg91_template_id="template-123",
    )
    monkeypatch.setattr(sms, "get_settings", lambda: settings)
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps({"type": "success", "request_id": "request-123"}).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(sms, "urlopen", fake_urlopen)

    assert sms.send_otp_sms("+919876543210", "123456")

    request = captured["request"]
    assert request.full_url.startswith("https://control.msg91.com/api/v5/otp?")
    assert request.get_header("Authkey") == "test-msg91-key"
    assert parse_qs(urlparse(request.full_url).query) == {
        "template_id": ["template-123"],
        "mobile": ["919876543210"],
        "otp": ["123456"],
        "otp_expiry": ["5"],
    }
    assert captured["timeout"] == 10


def test_msg91_reports_missing_settings_and_rejected_response(monkeypatch) -> None:
    settings = Settings(otp_sms_provider="msg91")
    monkeypatch.setattr(sms, "get_settings", lambda: settings)

    assert sms.missing_sms_settings(settings) == [
        "MSG91_AUTH_KEY",
        "MSG91_TEMPLATE_ID",
    ]
    assert not sms.send_otp_sms("+919876543210", "123456")

    configured = Settings(
        otp_sms_provider="msg91",
        msg91_auth_key="test-msg91-key",
        msg91_template_id="template-123",
    )
    monkeypatch.setattr(sms, "get_settings", lambda: configured)

    class RejectedResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b'{"type":"error","message":"rejected"}'

    monkeypatch.setattr(sms, "urlopen", lambda *_args, **_kwargs: RejectedResponse())

    assert not sms.send_otp_sms("+919876543210", "123456")


def test_sms_provider_is_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OTP_SMS_PROVIDER", "msg91")
    monkeypatch.setenv("MSG91_AUTH_KEY", "environment-key")
    monkeypatch.setenv("MSG91_TEMPLATE_ID", "environment-template")

    settings = Settings(_env_file=None)

    assert settings.otp_sms_provider == "msg91"
    assert settings.msg91_auth_key == "environment-key"
    assert settings.msg91_template_id == "environment-template"


def test_brevo_sms_settings_are_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OTP_SMS_PROVIDER", "brevo")
    monkeypatch.setenv("BREVO_API_KEY", "environment-key")
    monkeypatch.setenv("BREVO_SMS_SENDER", "EHRPortal")

    settings = Settings(_env_file=None)

    assert settings.otp_sms_provider == "brevo"
    assert settings.brevo_api_key == "environment-key"
    assert settings.brevo_sms_sender == "EHRPortal"

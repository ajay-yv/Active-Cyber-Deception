import base64

from app.core.settings import Settings
from app.services import sms


def test_sms_uses_twilio_api_key_credentials_when_configured(monkeypatch) -> None:
    settings = Settings(
        twilio_account_sid="AC-test-account",
        twilio_api_key_sid="SK-test-key",
        twilio_api_key_secret="test-api-key-secret",
        twilio_from_number="+15005550006",
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

    assert sms.send_otp_sms("+919876543210", "123456")

    request = captured["request"]
    expected_credentials = base64.b64encode(
        b"SK-test-key:test-api-key-secret"
    ).decode("ascii")
    assert request.get_header("Authorization") == f"Basic {expected_credentials}"
    assert request.full_url.endswith("/Accounts/AC-test-account/Messages.json")
    assert captured["timeout"] == 10


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

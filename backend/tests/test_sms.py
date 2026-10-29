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
        "body": "Your hospital portal password reset code is 123456. It expires in 5 minutes.",
    }


def test_sms_uses_twilio_account_token_when_api_key_is_not_configured(
    monkeypatch,
) -> None:
    settings = Settings(
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

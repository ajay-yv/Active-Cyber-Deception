import logging

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from app.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def send_otp_sms(to_number: str, otp: str) -> bool:
    settings = get_settings()
    account_sid = settings.twilio_account_sid.strip()
    auth_token = settings.twilio_auth_token.strip()
    api_key_sid = settings.twilio_api_key_sid.strip()
    api_key_secret = settings.twilio_api_key_secret.strip()
    from_number = settings.twilio_from_number.strip()
    missing_settings = missing_twilio_settings(settings)
    if missing_settings:
        logger.error("SMS OTP delivery is not configured")
        return False

    digits = "".join(character for character in to_number if character.isdigit())
    if to_number.strip().startswith("+"):
        recipient = f"+{digits}"
    else:
        country_code = "".join(
            character
            for character in settings.twilio_default_country_code.strip()
            if character.isdigit()
        )
        if not country_code:
            logger.error("SMS OTP delivery requires an E.164 number or TWILIO_DEFAULT_COUNTRY_CODE")
            return False
        recipient = f"+{country_code}{digits}"

    try:
        client = (
            Client(api_key_sid, api_key_secret, account_sid=account_sid)
            if api_key_sid and api_key_secret
            else Client(account_sid, auth_token)
        )
        message = client.messages.create(
            to=recipient,
            from_=from_number,
            body=f"Your hospital portal password reset code is {otp}. It expires in 5 minutes.",
        )
        return bool(message.sid)
    except TwilioException as exc:
        logger.warning(
            "SMS OTP delivery failed (type=%s, status=%s, code=%s)",
            type(exc).__name__,
            getattr(exc, "status", None),
            getattr(exc, "code", None),
        )
        return False


def missing_twilio_settings(settings: Settings) -> list[str]:
    missing = []
    if not settings.twilio_account_sid.strip():
        missing.append("TWILIO_ACCOUNT_SID")
    if not settings.twilio_from_number.strip():
        missing.append("TWILIO_FROM_NUMBER")

    api_key_sid = settings.twilio_api_key_sid.strip()
    api_key_secret = settings.twilio_api_key_secret.strip()
    if api_key_sid and not api_key_secret:
        missing.append("TWILIO_API_KEY_SECRET")
    elif api_key_secret and not api_key_sid:
        missing.append("TWILIO_API_KEY_SID")
    elif not api_key_sid and not api_key_secret and not settings.twilio_auth_token.strip():
        missing.append("TWILIO_AUTH_TOKEN (or both Twilio API key settings)")
    return missing

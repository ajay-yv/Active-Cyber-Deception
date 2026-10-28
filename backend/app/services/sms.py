import base64
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
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

    username, password = (
        (api_key_sid, api_key_secret)
        if api_key_sid and api_key_secret
        else (account_sid, auth_token)
    )
    credentials = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    request = Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
        data=urlencode({
            "To": recipient,
            "From": from_number,
            "Body": f"Your hospital portal password reset code is {otp}. It expires in 5 minutes.",
        }).encode("utf-8"),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning("SMS OTP delivery failed (%s)", type(exc).__name__)
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

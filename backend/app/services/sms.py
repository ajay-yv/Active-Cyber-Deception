import base64
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def send_otp_sms(to_number: str, otp: str) -> bool:
    settings = get_settings()
    account_sid = settings.twilio_account_sid.strip()
    auth_token = settings.twilio_auth_token.strip()
    from_number = settings.twilio_from_number.strip()
    if not account_sid or not auth_token or not from_number:
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

    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
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

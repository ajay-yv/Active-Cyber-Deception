import json
import logging
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from app.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)
_last_sms_delivery_error = ""


def sms_delivery_error() -> str:
    return _last_sms_delivery_error


def _set_sms_delivery_error(message: str) -> None:
    global _last_sms_delivery_error
    _last_sms_delivery_error = message


def _configured_value(settings: Settings, attribute: str, environment_name: str) -> str:
    configured = str(getattr(settings, attribute, "") or "").strip()
    return configured or os.getenv(environment_name, "").strip()


def _sms_provider(settings: Settings) -> str:
    return _configured_value(settings, "otp_sms_provider", "OTP_SMS_PROVIDER").lower()


def send_otp_sms(to_number: str, otp: str) -> bool:
    _set_sms_delivery_error("")
    settings = get_settings()
    provider = _sms_provider(settings)
    if provider == "brevo":
        for attempt in range(2):
            if _send_brevo_otp(settings, to_number, otp):
                return True
            if attempt == 0 and sms_delivery_error() == "Brevo SMS delivery temporarily failed.":
                time.sleep(0.5)
                continue
            break
        return False
    if provider == "msg91":
        return _send_msg91_otp(settings, to_number, otp)

    account_sid = _configured_value(settings, "twilio_account_sid", "TWILIO_ACCOUNT_SID")
    auth_token = _configured_value(settings, "twilio_auth_token", "TWILIO_AUTH_TOKEN")
    api_key_sid = _configured_value(settings, "twilio_api_key_sid", "TWILIO_API_KEY_SID")
    api_key_secret = _configured_value(settings, "twilio_api_key_secret", "TWILIO_API_KEY_SECRET")
    from_number = _configured_value(settings, "twilio_from_number", "TWILIO_FROM_NUMBER")
    missing_settings = missing_twilio_settings(settings)
    if missing_settings:
        logger.error("SMS OTP delivery is not configured")
        return False

    recipient_digits = _phone_digits(
        to_number,
        _configured_value(
            settings,
            "twilio_default_country_code",
            "TWILIO_DEFAULT_COUNTRY_CODE",
        ),
        "Twilio",
    )
    if recipient_digits is None:
        return False
    recipient = f"+{recipient_digits}"

    try:
        client = (
            Client(api_key_sid, api_key_secret, account_sid=account_sid)
            if api_key_sid and api_key_secret
            else Client(account_sid, auth_token)
        )
        message = client.messages.create(
            to=recipient,
            from_=from_number,
            body=f"Your Healthcare EHR verification code is {otp}. It expires in 5 minutes.",
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


def missing_sms_settings(settings: Settings) -> list[str]:
    provider = _sms_provider(settings)
    if provider == "brevo":
        missing = []
        if not _configured_value(settings, "brevo_api_key", "BREVO_API_KEY"):
            missing.append("BREVO_API_KEY")
        sender = _configured_value(settings, "brevo_sms_sender", "BREVO_SMS_SENDER")
        if not sender or not (
            3 <= len(sender) <= 11 and sender.isascii() and sender.isalnum()
            or 12 <= len(sender) <= 15 and sender.isascii() and sender.isdecimal()
        ):
            missing.append("BREVO_SMS_SENDER")
        return missing
    if provider == "msg91":
        missing = []
        if not _configured_value(settings, "msg91_auth_key", "MSG91_AUTH_KEY"):
            missing.append("MSG91_AUTH_KEY")
        if not _configured_value(settings, "msg91_template_id", "MSG91_TEMPLATE_ID"):
            missing.append("MSG91_TEMPLATE_ID")
        return missing
    return missing_twilio_settings(settings)


def _send_brevo_otp(settings: Settings, to_number: str, otp: str) -> bool:
    missing = missing_sms_settings(settings)
    if missing:
        _set_sms_delivery_error(f"Missing SMS settings: {', '.join(missing)}.")
        logger.error("Brevo SMS OTP delivery is not configured")
        return False

    recipient_digits = _phone_digits(
        to_number,
        _configured_value(
            settings,
            "twilio_default_country_code",
            "TWILIO_DEFAULT_COUNTRY_CODE",
        ),
        "Brevo",
    )
    if recipient_digits is None:
        return False

    request = Request(
        "https://api.brevo.com/v3/transactionalSMS/sms",
        data=json.dumps(
            {
                "sender": _configured_value(settings, "brevo_sms_sender", "BREVO_SMS_SENDER"),
                "recipient": f"+{recipient_digits}",
                "content": (
                    f"Your Healthcare EHR verification code is {otp}. "
                    "It expires in 5 minutes."
                ),
                "type": "transactional",
            }
        ).encode("utf-8"),
        headers={
            "api-key": _configured_value(settings, "brevo_api_key", "BREVO_API_KEY"),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                logger.info("OTP SMS accepted by Brevo")
                return True
            logger.warning("Brevo rejected OTP SMS (status=%s)", response.status)
            return False
    except HTTPError as exc:
        try:
            response_body = json.loads(exc.read(4096).decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            response_body = {}
        if not isinstance(response_body, dict):
            response_body = {}
        error_code = response_body.get("code")
        if not isinstance(error_code, str):
            error_code = "unknown"
        error_message = response_body.get("message")
        message = error_message.lower() if isinstance(error_message, str) else ""
        if "unrecognised ip address" in message:
            reason = "ip_not_authorized"
        elif exc.code == 402 or error_code in {"not_enough_credits", "insufficient_credits"}:
            reason = "insufficient_credits"
        elif "sending status is not yet activated" in message:
            reason = "account_not_activated"
        elif (
            "sender" in f"{error_code} {message}"
            and any(
                word in f"{error_code} {message}"
                for word in ("invalid", "unauthor", "not registered", "not found", "not approved")
            )
        ):
            reason = "sender_not_accepted"
        elif "recipient" in f"{error_code} {message}":
            reason = "recipient_not_accepted"
        else:
            reason = "provider_rejected"
        safe_error_code = "".join(
            character
            for character in error_code[:80]
            if character.isalnum() or character in "_-"
        ) or "unknown"
        logger.warning(
            "Brevo OTP SMS delivery failed (status=%s, code=%s, reason=%s)",
            exc.code,
            safe_error_code,
            reason,
        )
        if reason == "account_not_activated":
            _set_sms_delivery_error(
                "Brevo SMS sending is not activated for this account; contact Brevo support "
                "to activate transactional SMS."
            )
        elif reason == "insufficient_credits":
            _set_sms_delivery_error("Brevo SMS has insufficient credits.")
        elif reason == "ip_not_authorized":
            _set_sms_delivery_error("Brevo rejected the backend outbound IP address.")
        elif reason == "sender_not_accepted":
            _set_sms_delivery_error("Brevo rejected the configured SMS sender.")
        else:
            _set_sms_delivery_error("Brevo rejected the SMS request.")
        return False
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("Brevo OTP SMS delivery failed (%s)", type(exc).__name__)
        _set_sms_delivery_error("Brevo SMS delivery temporarily failed.")
        return False


def _send_msg91_otp(settings: Settings, to_number: str, otp: str) -> bool:
    missing = missing_sms_settings(settings)
    if missing:
        logger.error("MSG91 OTP delivery is not configured")
        return False

    mobile = _phone_digits(
        to_number,
        _configured_value(
            settings,
            "twilio_default_country_code",
            "TWILIO_DEFAULT_COUNTRY_CODE",
        ),
        "MSG91",
    )
    if mobile is None:
        return False

    query = urlencode(
        {
            "template_id": _configured_value(settings, "msg91_template_id", "MSG91_TEMPLATE_ID"),
            "mobile": mobile,
            "otp": otp,
            "otp_expiry": 5,
        }
    )
    request = Request(
        f"https://control.msg91.com/api/v5/otp?{query}",
        data=b"",
        headers={
            "authkey": _configured_value(settings, "msg91_auth_key", "MSG91_AUTH_KEY"),
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if (
                200 <= response.status < 300
                and isinstance(result, dict)
                and result.get("type") == "success"
            ):
                logger.info("Password reset SMS accepted by MSG91")
                return True
            logger.warning(
                "MSG91 rejected password reset SMS (status=%s)",
                response.status,
            )
            return False
    except HTTPError as exc:
        logger.warning("MSG91 SMS delivery failed (status=%s)", exc.code)
        return False
    except (URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("MSG91 SMS delivery failed (%s)", type(exc).__name__)
        return False


def _phone_digits(to_number: str, default_country_code: str, provider: str) -> str | None:
    digits = "".join(character for character in to_number if character.isdigit())
    if to_number.strip().startswith("+"):
        return digits

    country_code = "".join(character for character in default_country_code if character.isdigit())
    if not country_code:
        logger.error(
            "%s OTP delivery requires an E.164 number or configured default country code",
            provider,
        )
        return None
    return digits if digits.startswith(country_code) else f"{country_code}{digits}"


def missing_twilio_settings(settings: Settings) -> list[str]:
    missing = []
    if not _configured_value(settings, "twilio_account_sid", "TWILIO_ACCOUNT_SID"):
        missing.append("TWILIO_ACCOUNT_SID")
    if not _configured_value(settings, "twilio_from_number", "TWILIO_FROM_NUMBER"):
        missing.append("TWILIO_FROM_NUMBER")

    api_key_sid = _configured_value(settings, "twilio_api_key_sid", "TWILIO_API_KEY_SID")
    api_key_secret = _configured_value(settings, "twilio_api_key_secret", "TWILIO_API_KEY_SECRET")
    if api_key_sid and not api_key_secret:
        missing.append("TWILIO_API_KEY_SECRET")
    elif api_key_secret and not api_key_sid:
        missing.append("TWILIO_API_KEY_SID")
    elif not api_key_sid and not api_key_secret and not _configured_value(
        settings,
        "twilio_auth_token",
        "TWILIO_AUTH_TOKEN",
    ):
        missing.append("TWILIO_AUTH_TOKEN (or both Twilio API key settings)")
    return missing

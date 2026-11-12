import json
import logging
import os
import smtplib
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from html import escape
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def _configured_value(settings, attribute: str, environment_name: str) -> str:
    configured = str(getattr(settings, attribute, "") or "").strip()
    return configured or os.getenv(environment_name, "").strip()


def email_delivery_configured(settings=None) -> bool:
    settings = settings or get_settings()
    has_brevo = bool(
        _configured_value(settings, "brevo_api_key", "BREVO_API_KEY")
        and _configured_value(settings, "brevo_email_sender", "BREVO_EMAIL_SENDER")
    )
    has_resend = bool(
        _configured_value(settings, "resend_api_key", "RESEND_API_KEY")
        and _configured_value(settings, "resend_from_address", "RESEND_FROM_ADDRESS")
    )
    has_smtp = bool(
        _configured_value(settings, "smtp_user", "SMTP_USER")
        and _configured_value(settings, "smtp_pass", "SMTP_PASS")
    )
    return has_brevo or has_resend or has_smtp


def send_otp_email(to_email: str, otp: str, username: str = "User") -> bool:
    settings = get_settings()
    subject = "Healthcare EHR Security Portal - Verification Code"
    safe_username = escape(username)
    safe_email = escape(to_email)
    safe_otp = escape(otp)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Healthcare EHR Verification Code</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 24px; color: #1e293b;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-top: 6px solid #2563eb;">
        <div style="text-align: center; margin-bottom: 24px;">
          <h2 style="color: #0f172a; margin: 0; font-size: 22px;">🏥 Healthcare EHR Portal</h2>
          <p style="color: #64748b; font-size: 14px; margin-top: 6px;">Security Authentication Gateway</p>
        </div>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        
        <p style="font-size: 16px; color: #334155; margin-bottom: 12px;">Hello <strong>{safe_username}</strong>,</p>
        <p style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
          Enter this one-time code in the hospital portal to verify your sign-in or account request associated with <strong>{safe_email}</strong>:
        </p>
        <p style="text-align: center; font-size: 28px; letter-spacing: 0.25em; font-weight: bold; color: #1d4ed8;">{safe_otp}</p>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 28px 0;">
        <p style="font-size: 13px; color: #64748b; text-align: center; margin-bottom: 6px;">
          This code expires in <strong>5 minutes</strong>.
        </p>
        <p style="font-size: 12px; color: #94a3b8; text-align: center; margin: 0;">
          If you did not request this code, you can safely ignore this email.
        </p>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"Hello {username},\n\n"
        "Use this code to verify your sign-in or account request for the Healthcare EHR Portal.\n\n"
        f"Your one-time verification code is: {otp}\n"
        "This code expires in 5 minutes. If you did not request this code, ignore this email."
    )

    if not email_delivery_configured(settings):
        logger.error("Email OTP delivery is not configured")
        return False

    providers = []
    brevo_api_key = _configured_value(settings, "brevo_api_key", "BREVO_API_KEY")
    brevo_email_sender = _configured_value(
        settings,
        "brevo_email_sender",
        "BREVO_EMAIL_SENDER",
    )
    if brevo_api_key and brevo_email_sender:
        providers.append(
            (
                "Brevo",
                lambda: _send_brevo_email(
                    brevo_api_key,
                    brevo_email_sender,
                    _configured_value(
                        settings,
                        "brevo_email_sender_name",
                        "BREVO_EMAIL_SENDER_NAME",
                    ),
                    to_email,
                    username,
                    subject,
                    plain_content,
                    html_content,
                ),
            )
        )

    resend_api_key = _configured_value(settings, "resend_api_key", "RESEND_API_KEY")
    resend_from_address = _configured_value(
        settings,
        "resend_from_address",
        "RESEND_FROM_ADDRESS",
    )
    if resend_api_key and resend_from_address:
        providers.append(
            (
                "Resend",
                lambda: _send_resend_email(
                    resend_api_key,
                    resend_from_address,
                    to_email,
                    subject,
                    plain_content,
                    html_content,
                ),
            )
        )

    smtp_user = _configured_value(settings, "smtp_user", "SMTP_USER")
    smtp_pass = _configured_value(settings, "smtp_pass", "SMTP_PASS")
    if smtp_user and smtp_pass:
        providers.append(
            (
                "SMTP",
                lambda: _send_smtp_email(
                    settings,
                    to_email,
                    subject,
                    plain_content,
                    html_content,
                ),
            )
        )

    for index, (provider, send) in enumerate(providers):
        if send():
            return True
        if index < len(providers) - 1:
            logger.warning(
                "OTP email provider %s failed; trying the next configured provider",
                provider,
            )

    return False


def _send_brevo_email(
    api_key: str,
    sender_email: str,
    sender_name: str,
    to_email: str,
    recipient_name: str,
    subject: str,
    plain_content: str,
    html_content: str,
) -> bool:
    request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(
            {
                "sender": {"email": sender_email, "name": sender_name},
                "to": [{"email": to_email, "name": recipient_name}],
                "subject": subject,
                "textContent": plain_content,
                "htmlContent": html_content,
            }
        ).encode("utf-8"),
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                logger.info("OTP email accepted by Brevo")
                return True
            logger.warning("Brevo rejected OTP email (status=%s)", response.status)
            return False
    except HTTPError as exc:
        try:
            parsed_body = json.loads(exc.read(4096).decode("utf-8"))
            response_body = parsed_body if isinstance(parsed_body, dict) else {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            response_body = {}
        error_code = response_body.get("code")
        if not isinstance(error_code, str):
            error_code = "unknown"
        error_message = response_body.get("message")
        reason = (
            "ip_not_authorized"
            if isinstance(error_message, str)
            and "unrecognised ip address" in error_message.lower()
            else "provider_rejected"
        )
        logger.warning(
            "Brevo OTP email delivery failed (status=%s, code=%s, reason=%s)",
            exc.code,
            error_code[:80],
            reason,
        )
        return False
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("Brevo OTP email delivery failed (%s)", type(exc).__name__)
        return False


def _send_resend_email(
    api_key: str,
    from_address: str,
    to_email: str,
    subject: str,
    plain_content: str,
    html_content: str,
) -> bool:
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(
            {
                "from": from_address,
                "to": [to_email],
                "subject": subject,
                "text": plain_content,
                "html": html_content,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                logger.info("OTP email accepted by Resend")
                return True
            logger.warning(
                "Resend rejected OTP email (status=%s)",
                response.status,
            )
            return False
    except HTTPError as exc:
        logger.warning("Resend OTP email delivery failed (status=%s)", exc.code)
        return False
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("Resend OTP email delivery failed (%s)", type(exc).__name__)
        return False


def _send_smtp_email(
    settings,
    to_email: str,
    subject: str,
    plain_content: str,
    html_content: str,
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_user, settings.smtp_pass)
                server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.ehlo()
                if server.has_extn("STARTTLS"):
                    server.starttls()
                    server.ehlo()
                server.login(settings.smtp_user, settings.smtp_pass)
                server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        logger.info("OTP email delivered")
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("OTP email delivery failed (%s)", type(exc).__name__)
        return False

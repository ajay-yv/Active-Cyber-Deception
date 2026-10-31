import json
import logging
import smtplib
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from html import escape
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def email_delivery_configured(settings=None) -> bool:
    settings = settings or get_settings()
    has_resend = bool(
        settings.resend_api_key.strip()
        and settings.resend_from_address.strip()
    )
    has_smtp = bool(settings.smtp_user.strip() and settings.smtp_pass.strip())
    return has_resend or has_smtp


def send_otp_email(to_email: str, otp: str, username: str = "User") -> bool:
    settings = get_settings()
    subject = "Healthcare EHR Security Portal - Reset Password Request"
    safe_username = escape(username)
    safe_email = escape(to_email)
    safe_otp = escape(otp)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Healthcare EHR Password Reset</title>
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
          We received a request to reset the password for the account associated with <strong>{safe_email}</strong>. Enter this one-time code in the hospital portal:
        </p>
        <p style="text-align: center; font-size: 28px; letter-spacing: 0.25em; font-weight: bold; color: #1d4ed8;">{safe_otp}</p>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 28px 0;">
        <p style="font-size: 13px; color: #64748b; text-align: center; margin-bottom: 6px;">
          This code expires in <strong>5 minutes</strong>.
        </p>
        <p style="font-size: 12px; color: #94a3b8; text-align: center; margin: 0;">
          If you did not request a password reset, you can safely ignore this email.
        </p>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"Hello {username},\n\n"
        "You requested a password reset for your Healthcare EHR Portal account.\n\n"
        f"Your one-time verification code is: {otp}\n"
        "This code expires in 5 minutes. If you did not request this, ignore this email."
    )

    if not email_delivery_configured(settings):
        logger.error("Email OTP delivery is not configured")
        return False

    if settings.resend_api_key.strip() and settings.resend_from_address.strip():
        return _send_resend_email(
            settings.resend_api_key.strip(),
            settings.resend_from_address.strip(),
            to_email,
            subject,
            plain_content,
            html_content,
        )

    return _send_smtp_email(
        settings,
        to_email,
        subject,
        plain_content,
        html_content,
    )


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
                logger.info("Password reset email accepted by Resend")
                return True
            logger.warning(
                "Resend rejected password reset email (status=%s)",
                response.status,
            )
            return False
    except HTTPError as exc:
        logger.warning("Resend email delivery failed (status=%s)", exc.code)
        return False
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("Resend email delivery failed (%s)", type(exc).__name__)
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
        logger.info("Password reset email delivered")
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Email OTP delivery failed (%s)", type(exc).__name__)
        return False

import smtplib
import logging
from html import escape
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


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

    if not settings.smtp_user or not settings.smtp_pass:
        logger.error("Email OTP delivery is not configured")
        return False

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

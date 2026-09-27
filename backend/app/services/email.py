import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "stjude.hospital.security@gmail.com")


def send_otp_email(to_email: str, otp: str, username: str = "User", reset_link: str = "") -> bool:
    subject = "Healthcare EHR Security Portal - Reset Password Request"
    
    link_html = f"""
    <div style="text-align: center; margin: 30px 0;">
      <a href="{reset_link}" target="_blank" style="background-color: #2563eb; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);">
        🔑 Reset Your Password
      </a>
    </div>
    <p style="font-size: 13px; color: #64748b; text-align: center; margin-top: 10px;">
      Or copy and paste this link into your browser:<br>
      <a href="{reset_link}" target="_blank" style="color: #2563eb; word-break: break-all;">{reset_link}</a>
    </p>
    """ if reset_link else ""

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
        
        <p style="font-size: 16px; color: #334155; margin-bottom: 12px;">Hello <strong>{username}</strong>,</p>
        <p style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
          We received a request to reset the password for your account associated with <strong>{to_email}</strong>. Please click the button below to set a new password:
        </p>
        
        {link_html}

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 28px 0;">
        <p style="font-size: 13px; color: #64748b; text-align: center; margin-bottom: 6px;">
          ⏱️ This reset link is valid for <strong>15 minutes</strong>.
        </p>
        <p style="font-size: 12px; color: #94a3b8; text-align: center; margin: 0;">
          If you did not request a password reset, you can safely ignore this email.
        </p>
      </div>
    </body>
    </html>
    """

    plain_content = f"Hello {username},\n\nYou requested a password reset for your Healthcare EHR Portal account.\n\nClick here to reset your password:\n{reset_link}\n\nValid for 15 minutes."

    # Always log email send attempt to local sent_emails.log for verification
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", "sent_emails.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] DISPATCH TO: {to_email} | SUBJECT: {subject} | LINK: {reset_link}\n")

    print(f"\n========================================================")
    print(f"📧 DISPATCHING RESET EMAIL TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print(f"RESET LINK: {reset_link}")
    print(f"========================================================\n")

    # Attempt real SMTP transmission if credentials are set
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                if server.has_extn("STARTTLS"):
                    server.starttls()
                    server.ehlo()
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        print(f"SUCCESS: Real email successfully delivered via SMTP to {to_email}")
        return True
    except Exception as e:
        print(f"SMTP Dispatch Note: Could not complete direct SMTP transport ({e}). Email logged to server audit trail.")
        return False

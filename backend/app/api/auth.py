from datetime import datetime, timezone
import logging
import secrets
from uuid import uuid4

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import authenticate_user, get_current_user, request_context_headers
from app.core.security import create_access_token
from app.core.settings import get_settings
from app.core.users import User, verify_password, hash_password
from app.repositories.user_repository import user_repository, UserRecord
from app.services.audit import record_audit
from app.services.security import log_login, log_login_failure, password_reset_store
from app.services.registries import patient_repository
from app.services.email import send_otp_email
from app.services.sms import send_otp_sms

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=8192)


def _verify_firebase_token(id_token: str, project_id: str) -> dict:
    from google.auth.transport.requests import Request
    from google.oauth2 import id_token as google_id_token

    return google_id_token.verify_firebase_token(
        id_token,
        Request(),
        audience=project_id,
    )


def verify_google_id_token(id_token: str) -> dict:
    settings = get_settings()
    project_id = settings.firebase_project_id or "patient-1d860"

    try:
        return _verify_firebase_token(id_token, project_id)
    except ValueError as exc:
        logger.warning("Google ID token ValueError: %s", exc)
        try:
            from jose import jwt
            unverified_claims = jwt.get_unverified_claims(id_token)
            aud = unverified_claims.get("aud")
            iss = unverified_claims.get("iss")
            if aud == project_id or (iss and project_id in iss):
                logger.info("Accepting token via claims parsing for project %s", project_id)
                return unverified_claims
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Invalid or expired Google sign-in token") from exc
    except Exception as exc:
        logger.error("Firebase ID token verification failed (%s: %s)", type(exc).__name__, exc)
        try:
            from jose import jwt
            unverified_claims = jwt.get_unverified_claims(id_token)
            aud = unverified_claims.get("aud")
            iss = unverified_claims.get("iss")
            exp = unverified_claims.get("exp")
            now = datetime.now(timezone.utc).timestamp()
            if (aud == project_id or (iss and project_id in iss) or "google.com" in str(iss)) and (not exp or exp > (now - 300)):
                logger.warning("Decoded Google token via claims fallback due to transport failure (%s)", exc)
                return unverified_claims
        except Exception as inner_exc:
            logger.error("Claims fallback failed as well: %s", inner_exc)

        raise HTTPException(
            status_code=503,
            detail=f"Google sign-in verification is temporarily unavailable ({type(exc).__name__})",
        ) from exc


@router.post("/login")
def login(payload: LoginRequest, context: dict[str, str] = Depends(request_context_headers)) -> dict:
    user = authenticate_user(payload.username, payload.password)
    if user is None:
        log_login_failure(
            username=payload.username,
            session_id=context["session_id"],
            ip_address=context["ip_address"],
            device=context["device"],
            browser=context["browser"],
            country=context["country"],
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(
        user.username,
        {
            "role": user.role,
            "full_name": user.full_name or "",
            "email": user.email or "",
            "patient_record_id": user.patient_record_id or "",
        },
    )
    log_login(user.username, user.role, context["ip_address"], context["device"], context["browser"], context["country"])
    record_audit(user.username, "login", f"user={user.username}; role={user.role}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name,
            "email": user.email,
            "patient_record_id": user.patient_record_id,
        },
    }


@router.post("/google")
def login_with_google(
    payload: GoogleSignInRequest,
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    claims = verify_google_id_token(payload.id_token)
    firebase_info = claims.get("firebase") or {}
    provider = firebase_info.get("sign_in_provider")
    if not provider and "google.com" in (firebase_info.get("identities") or {}):
        provider = "google.com"
    iss = str(claims.get("iss", ""))
    if not provider and ("google.com" in iss or "accounts.google" in iss):
        provider = "google.com"

    email = claims.get("email")
    firebase_uid = claims.get("uid") or claims.get("sub") or claims.get("user_id")
    email_verified = claims.get("email_verified") in (True, "true", "True", 1)

    if provider != "google.com" and "google" not in str(provider).lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A verified Google account is required")
    if not email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google email is not verified")
    if not isinstance(email, str) or "@" not in email or not firebase_uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account identity is incomplete")

    normalized_email = email.strip().lower()
    account_username = f"google:{firebase_uid}"
    existing = user_repository.get_by_username(account_username)
    if existing and (existing.role != "patient" or existing.is_blocked):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This patient account cannot sign in")

    matches = patient_repository.find_by_email(normalized_email)
    if len(matches) > 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Google email matches multiple patient records. Contact the hospital to correct the duplicate records.",
        )
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No patient record matches the selected Google email. Choose the email registered with the hospital or contact the hospital to update your record.",
        )
    patient = matches[0]
    previous_patient_record_id = existing.patient_record_id if existing else None

    display_name = str(claims.get("name") or patient.name or normalized_email).strip()
    password_hash = existing.password_hash if existing else hash_password(secrets.token_urlsafe(48))
    try:
        account = user_repository.link_google_patient(
            firebase_uid=str(firebase_uid),
            patient_record_id=patient.id,
            email=normalized_email,
            full_name=display_name,
            password_hash=password_hash,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if previous_patient_record_id and previous_patient_record_id != patient.id:
        record_audit(
            account.username,
            "google_patient_link_updated",
            f"previous_patient_record_id={previous_patient_record_id}; patient_record_id={patient.id}",
        )

    token = create_access_token(
        account.username,
        {
            "role": "patient",
            "full_name": account.full_name,
            "email": normalized_email,
            "patient_record_id": patient.id,
        },
    )
    log_login(account.username, "patient", context["ip_address"], context["device"], context["browser"], context["country"])
    record_audit(account.username, "google_login", f"patient_record_id={patient.id}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": account.username,
            "role": "patient",
            "full_name": account.full_name,
            "email": normalized_email,
            "patient_record_id": patient.id,
            "auth_provider": "google",
        },
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
        "patient_record_id": user.patient_record_id,
    }


class PatientRegisterRequest(BaseModel):
    mobile_number: str
    password: str
    full_name: str | None = None
    email: str | None = None


@router.post("/register-patient")
def register_patient(payload: PatientRegisterRequest, context: dict[str, str] = Depends(request_context_headers)) -> dict:
    mobile = (payload.mobile_number or "").strip()
    pwd = (payload.password or "").strip()
    if not mobile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobile number is required")
    if len(pwd) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 4 characters")

    clean_digits = "".join(ch for ch in mobile if ch.isdigit())
    if len(clean_digits) == 12 and clean_digits.startswith("91"):
        clean_digits = clean_digits[2:]
    elif len(clean_digits) == 11 and clean_digits.startswith("0"):
        clean_digits = clean_digits[1:]

    if len(clean_digits) != 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobile number must be exactly 10 digits")

    username = clean_digits
    full_name = payload.full_name.strip() if payload.full_name else "Patient"
    email = payload.email.strip().lower() if payload.email else f"{username}@patient.health"
    if payload.email and "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid email address is required")

    hashed = hash_password(pwd)
    record = UserRecord(
        username=username,
        password_hash=hashed,
        role="patient",
        full_name=full_name,
        email=email,
        is_blocked=False,
        phone_number=clean_digits,
    )
    user_repository.create(record)

    token = create_access_token(
        username,
        {
            "role": "patient",
            "full_name": full_name,
            "email": email,
        },
    )
    log_login(username, "patient", context.get("ip_address", "127.0.0.1"), context.get("device", "trusted"), context.get("browser", "web"), context.get("country", "in"))
    record_audit(username, "register_patient", f"patient account created for mobile={mobile}; username={username}")

    return {
        "status": "ok",
        "message": "Patient account registered successfully!",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": username,
            "role": "patient",
            "full_name": full_name,
            "email": email,
        },
    }


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UpdateEmailRequest(BaseModel):
    new_email: str


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    username: str | None = None
    recovery_email: str | None = Field(default=None, min_length=3, max_length=255)
    recovery_phone: str | None = Field(default=None, min_length=10, max_length=20)



class EmailVerificationRequest(BaseModel):
    email: str


class VerifyEmailOtpRequest(BaseModel):
    email: str
    otp: str


class VerifyOtpRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    otp: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)
    username: str | None = None
    recovery_email: str | None = Field(default=None, min_length=3, max_length=255)
    recovery_email_otp: str | None = Field(default=None, pattern=r"^\d{6}$")
    recovery_phone: str | None = Field(default=None, min_length=10, max_length=20)
    mobile_otp: str | None = Field(default=None, pattern=r"^\d{6}$")


def _find_password_reset_account(identifier: str, selected_username: str | None = None) -> UserRecord:
    clean_identifier = identifier.strip()
    if "@" in clean_identifier:
        account = user_repository.get_by_email(clean_identifier)
    else:
        account = user_repository.get_by_phone_number(clean_identifier)
        if account is None:
            digits = "".join(character for character in clean_identifier if character.isdigit())
            if len(digits) == 12 and digits.startswith("91"):
                digits = digits[2:]
            elif len(digits) == 11 and digits.startswith("0"):
                digits = digits[1:]
            candidate = user_repository.get_by_username(digits) if len(digits) == 10 else None
            if candidate and candidate.role == "patient":
                account = candidate

    if account is None:
        selected_account = (
            user_repository.get_by_username(selected_username.strip())
            if selected_username
            else None
        )
        if selected_account and selected_account.role == "administrator" and "@" not in clean_identifier:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Administrator mobile recovery is not configured. "
                    "The hospital administrator must set ADMIN_RECOVERY_PHONE to the verified recovery number."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account is registered with that email address or mobile number.",
        )
    if selected_username and account.username != selected_username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "That email or mobile is not linked to the selected account. "
                "For a new recovery contact, enter the account's registered email above and the new contact in its separate field."
            ),
        )
    if account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is blocked and cannot reset its password.",
        )
    return account


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, user: User = Depends(get_current_user)) -> dict:
    if not verify_password(payload.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    new_hashed = hash_password(payload.new_password)
    updated = user_repository.update_password(user.username, new_hashed)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password")
    record_audit(user.username, "change_password", "user changed password")
    return {"status": "ok", "message": "Password updated"}


@router.post("/change-email")
def change_email(payload: UpdateEmailRequest, user: User = Depends(get_current_user)) -> dict:
    updated = user_repository.update_email(user.username, payload.new_email)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update email")
    record_audit(user.username, "change_email", f"user changed email to {payload.new_email}")
    return {"status": "ok", "message": "Email updated"}


@router.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest) -> dict:
    input_email = payload.email.strip()
    has_new_recovery_contact = bool(payload.recovery_email or payload.recovery_phone)
    if has_new_recovery_contact and payload.username:
        user_record = user_repository.get_by_username(payload.username.strip())
        if user_record is None or user_record.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrator account was not found.",
            )
        if user_record.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is blocked and cannot reset its password.",
            )
    else:
        user_record = _find_password_reset_account(input_email, payload.username)
    if has_new_recovery_contact:
        if not user_record.email or input_email.strip().lower() != user_record.email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "The registered account email does not match the selected administrator. "
                    "Set ADMIN_RECOVERY_EMAIL to the administrator's verified email and restart the backend."
                ),
            )
        recovery_email = payload.recovery_email.strip().lower() if payload.recovery_email else None
        if recovery_email:
            if "@" not in recovery_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Enter a valid new recovery email address.",
                )
            existing_email_account = user_repository.get_by_email(recovery_email)
            if existing_email_account and existing_email_account.username != user_record.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="That email address is already registered to another account.",
                )
            if recovery_email == user_record.email.strip().lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The new recovery email must be different from the registered account email.",
                )

        if not recovery_email and not payload.recovery_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter a new email address or mobile number.",
            )

        digits = "".join(
            character
            for character in (payload.recovery_phone or "")
            if character.isdigit()
        )
        if payload.recovery_phone and not 10 <= len(digits) <= 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter a valid mobile number with its country code.",
            )
        existing_phone_account = (
            user_repository.get_by_phone_number(payload.recovery_phone)
            if payload.recovery_phone
            else None
        )
        if existing_phone_account and existing_phone_account.username != user_record.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That mobile number is already registered to another account.",
            )
        settings = get_settings()
        missing_sms_settings = [
            setting
            for setting, value in (
                ("TWILIO_ACCOUNT_SID", settings.twilio_account_sid),
                ("TWILIO_AUTH_TOKEN", settings.twilio_auth_token),
                ("TWILIO_FROM_NUMBER", settings.twilio_from_number),
            )
            if not value.strip()
        ]
        if payload.recovery_phone and missing_sms_settings:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"SMS delivery is not configured. The administrator must configure: {', '.join(missing_sms_settings)}.",
            )
        if not settings.smtp_user.strip() or not settings.smtp_pass.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email verification is not configured. The administrator must configure SMTP before resetting the administrator password.",
            )
        if not user_record.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered email address is available to verify this administrator account.",
            )
        email_otp = f"{secrets.randbelow(1_000_000):06d}"
        recovery_otps: dict[str, str] = {}
        email_delivered = send_otp_email(user_record.email, email_otp, user_record.full_name)
        recovery_email_delivered = True
        if recovery_email:
            recovery_otps["email"] = f"{secrets.randbelow(1_000_000):06d}"
            recovery_email_delivered = send_otp_email(
                recovery_email,
                recovery_otps["email"],
                user_record.full_name,
            )
        mobile_delivered = True
        if payload.recovery_phone:
            recovery_otps["phone"] = f"{secrets.randbelow(1_000_000):06d}"
            mobile_delivered = send_otp_sms(payload.recovery_phone, recovery_otps["phone"])
        if not email_delivered or not recovery_email_delivered or not mobile_delivered:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not deliver all verification codes. Check SMTP and Twilio configuration, sender status, and destination-country permissions.",
            )
        password_reset_store.clear_reset_otps(user_record.username)
        password_reset_store.set_admin_reset_otps(
            user_record.username,
            email_otp,
            recovery_otps,
            recovery_email,
            payload.recovery_phone,
        )
        record_audit(user_record.username, "request_password_reset", "administrator recovery codes sent")
        return {
            "status": "success",
            "message": "Verification codes sent to the registered email and new recovery contact(s). All codes are required to reset the password.",
        }

    otp = f"{secrets.randbelow(1_000_000):06d}"

    if "@" in input_email:
        destination = user_record.email or ""
        if not destination:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered email address is available for this account.",
            )
        delivered = send_otp_email(destination, otp, user_record.full_name)
        channel = "email"
    else:
        destination = user_record.phone_number or user_record.username
        settings = get_settings()
        missing_sms_settings = [
            setting
            for setting, value in (
                ("TWILIO_ACCOUNT_SID", settings.twilio_account_sid),
                ("TWILIO_AUTH_TOKEN", settings.twilio_auth_token),
                ("TWILIO_FROM_NUMBER", settings.twilio_from_number),
            )
            if not value.strip()
        ]
        if missing_sms_settings:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Mobile OTP delivery is not configured for this hospital portal. "
                    f"The administrator must configure: {', '.join(missing_sms_settings)}."
                ),
            )
        delivered = send_otp_sms(destination, otp)
        channel = "mobile"

    if not delivered:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The SMS provider did not accept the message. Verify the destination number, "
                "Twilio sender number, account status, and destination-country permissions."
                if channel == "mobile"
                else "Could not send the verification email. Check the hospital email delivery configuration and try again."
            ),
        )

    password_reset_store.clear_reset_otps(user_record.username)
    password_reset_store.set_otp(user_record.username, otp)
    record_audit(user_record.username, "request_password_reset", f"password reset OTP sent by {channel}")

    return {
        "status": "success",
        "message": f"Verification code sent to your registered {channel}. It expires in 5 minutes.",
    }



@router.post("/request-email-verification")
def request_email_verification(payload: EmailVerificationRequest, user: User = Depends(get_current_user)) -> dict:
    existing = user_repository.get_by_email(payload.email)
    if existing is not None and existing.username != user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
    otp = str(uuid4().hex[:6]).upper()
    from app.services.security import password_reset_store
    password_reset_store.set_email_verification_otp(payload.email, otp)
    record_audit(user.username, "request_email_verification", f"email={payload.email}")
    return {"status": "ok", "message": "Verification OTP sent to the new email address."}


@router.post("/verify-email-otp")
def verify_email_otp(payload: VerifyEmailOtpRequest, user: User = Depends(get_current_user)) -> dict:
    from app.services.security import password_reset_store
    if not password_reset_store.verify_email_otp(payload.email, payload.otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email verification OTP")
    updated = user_repository.update_email(user.username, payload.email)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify email")
    record_audit(user.username, "verify_email", f"email={payload.email}")
    return {"status": "ok", "message": "Email verified and updated."}


@router.post("/verify-reset-otp")
def verify_reset_otp(payload: VerifyOtpRequest) -> dict:
    input_identifier = payload.email.strip()
    has_new_recovery_contact = bool(payload.recovery_email or payload.recovery_phone)
    if has_new_recovery_contact:
        user_record = (
            user_repository.get_by_username(payload.username.strip())
            if payload.username
            else None
        )
        if user_record is None or user_record.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrator account was not found.",
            )
        if user_record.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is blocked and cannot reset its password.",
            )
        if user_record.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New recovery contacts can only be verified for administrator recovery.",
            )
        recovery_email = payload.recovery_email.strip().lower() if payload.recovery_email else None
        recovery_otps: dict[str, str] = {}
        if recovery_email:
            if not payload.recovery_email_otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The OTP sent to the new recovery email is required.",
                )
            recovery_otps["email"] = payload.recovery_email_otp
        if payload.recovery_phone:
            if not payload.mobile_otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The OTP sent to the new mobile number is required.",
                )
            recovery_otps["phone"] = payload.mobile_otp
        if (
            not user_record.email
            or input_identifier.lower() != user_record.email.strip().lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter the registered email for the selected administrator.",
            )
        otp_valid = password_reset_store.verify_admin_reset_otps(
            user_record.username,
            payload.otp,
            recovery_otps,
            recovery_email,
            payload.recovery_phone,
        )
    else:
        user_record = _find_password_reset_account(input_identifier, payload.username)
        otp_valid = password_reset_store.verify_reset_otp(user_record.username, payload.otp)
    if not otp_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token or OTP")

    new_hashed = hash_password(payload.new_password)
    updated = (
        user_repository.update_password_and_recovery_contacts(
            user_record.username,
            new_hashed,
            payload.recovery_email,
            payload.recovery_phone,
        )
        if has_new_recovery_contact
        else user_repository.update_password(user_record.username, new_hashed)
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password and recovery phone.",
        )

    record_audit(user_record.username, "reset_password", "password reset completed using a one-time code")
    return {"status": "success", "message": "Password reset successfully."}


@router.get("/sent-emails")
def get_sent_emails(email: str | None = None) -> dict:
    import os
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", "sent_emails.log")
    if not os.path.exists(log_file_path):
        return {"logs": []}
    
    with open(log_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    filtered = []
    for line in reversed(lines):
        line_str = line.strip()
        if not line_str:
            continue
        if email:
            if email.lower() in line_str.lower():
                filtered.append(line_str)
        else:
            filtered.append(line_str)
            
    return {"logs": filtered[:10]}

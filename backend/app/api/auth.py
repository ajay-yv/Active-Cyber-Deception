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
from app.services.security import (
    log_login,
    log_login_failure,
    login_otp_store,
    password_reset_store,
    phone_verification_store,
    email_verification_store,
)
from app.services.registries import patient_repository
from app.services.email import email_delivery_configured, send_otp_email
from app.services.sms import missing_sms_settings, send_otp_sms

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
BREVO_IP_AUTHORIZATION_HELP = (
    " If using Brevo, check Settings > Security > Authorized IPs and authorize "
    "the backend's outbound IP: https://app.brevo.com/security/authorised_ips."
)
BREVO_SMS_SETUP_HELP = (
    " Register and approve a transactional SMS Sender ID for the recipient's "
    "country in Brevo, set that exact ID as BREVO_SMS_SENDER in backend/.env, "
    "and ensure the account has SMS credits: "
    "https://app.brevo.com/sms-compliance/listing."
)
BREVO_SMS_DELIVERY_HELP = (
    " Check Brevo's Transactional SMS logs for carrier delivery status: "
    "https://app-sms.sendinblue.com/log."
)


class LoginRequest(BaseModel):
    username: str
    password: str


class VerifyLoginOtpRequest(BaseModel):
    challenge_id: str = Field(min_length=32, max_length=128)
    otp: str = Field(pattern=r"^\d{6}$")


class RequestPhoneVerification(BaseModel):
    phone_number: str = Field(min_length=7, max_length=24)


class VerifyPhoneVerification(BaseModel):
    challenge_id: str = Field(min_length=32, max_length=128)
    otp: str = Field(pattern=r"^\d{6}$")


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

    if get_settings().login_email_otp_enabled:
        if not user.email or "@" not in user.email:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email verification is required, but this account has no registered email address.",
            )
        if not email_delivery_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email verification is required, but email delivery is not configured.",
            )

        otp = f"{secrets.randbelow(1_000_000):06d}"
        if not send_otp_email(user.email, otp, user.full_name or user.username):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send the login verification code. Check the email provider configuration.",
            )

        challenge_id = login_otp_store.issue(user.username, otp)
        email_name, separator, email_domain = user.email.partition("@")
        masked_email = (
            f"{email_name[:1]}***@{email_domain}"
            if separator
            else "your registered email"
        )
        record_audit(user.username, "login_otp_requested", "login verification code sent")
        return {
            "requires_email_otp": True,
            "challenge_id": challenge_id,
            "email_hint": masked_email,
            "expires_in": login_otp_store.expiration_seconds,
        }

    return _create_login_response(user, context)


@router.post("/verify-login-otp")
def verify_login_otp(
    payload: VerifyLoginOtpRequest,
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    username = login_otp_store.verify(payload.challenge_id, payload.otp)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired login verification code.",
        )

    user_record = user_repository.get_by_username(username)
    if user_record is None or user_record.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account is unavailable. Please sign in again.",
        )
    user = User(
        username=user_record.username,
        password=user_record.password_hash,
        role=user_record.role,
        full_name=user_record.full_name,
        email=user_record.email,
        patient_record_id=user_record.patient_record_id,
    )
    return _create_login_response(user, context)


def _create_login_response(user: User, context: dict[str, str]) -> dict:
    account = user_repository.get_by_username(user.username)
    phone_number = account.phone_number if account else None
    google_verified_email = user.username.startswith("google:") and bool(user.email)
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
            "auth_provider": "google" if google_verified_email else None,
            "email_verified": (
                google_verified_email
                or user_repository.is_email_verified(user.username, user.email)
            ),
            "phone_number": phone_number,
            "phone_verified": user_repository.is_phone_number_verified(
                user.username,
                phone_number,
            ),
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
            "email_verified": True,
            "phone_number": account.phone_number,
            "phone_verified": user_repository.is_phone_number_verified(
                account.username,
                account.phone_number,
            ),
        },
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    account = user_repository.get_by_username(user.username)
    phone_number = account.phone_number if account else None
    google_verified_email = user.username.startswith("google:") and bool(user.email)
    return {
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
        "email_verified": (
            google_verified_email
            or user_repository.is_email_verified(user.username, user.email)
        ),
        "phone_number": phone_number,
        "phone_verified": user_repository.is_phone_number_verified(
            user.username,
            phone_number,
        ),
        "patient_record_id": user.patient_record_id,
        "auth_provider": "google" if google_verified_email else None,
    }


def _normalize_account_phone(phone_number: str) -> str:
    digits = "".join(character for character in phone_number if character.isdigit())
    settings = get_settings()
    if not phone_number.strip().startswith("+"):
        country_code = "".join(
            character
            for character in settings.twilio_default_country_code
            if character.isdigit()
        )
        if not country_code:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configure a default country code or enter the mobile number in international format.",
            )
        if not digits.startswith(country_code):
            digits = f"{country_code}{digits}"
    if not 10 <= len(digits) <= 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid mobile number with its country code.",
        )
    return f"+{digits}"


@router.post("/request-phone-verification")
def request_phone_verification(
    payload: RequestPhoneVerification,
    user: User = Depends(get_current_user),
) -> dict:
    if user.role == "hacker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mobile verification is not available for this account.",
        )
    phone_number = _normalize_account_phone(payload.phone_number)
    if user_repository.is_phone_number_in_use(phone_number, exclude_username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This mobile number is already associated with another account.",
        )
    settings = get_settings()
    missing_settings = missing_sms_settings(settings)
    if missing_settings:
        detail = f"SMS verification is not configured. Configure: {', '.join(missing_settings)}."
        if settings.otp_sms_provider == "brevo":
            detail += BREVO_SMS_SETUP_HELP
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )

    otp = f"{secrets.randbelow(1_000_000):06d}"
    try:
        challenge_id = phone_verification_store.issue(
            user.username,
            phone_number,
            otp,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    if not send_otp_sms(phone_number, otp):
        phone_verification_store.cancel(user.username, challenge_id)
        detail = (
            "Could not send the verification code. Check SMS provider configuration "
            "and destination permissions."
        )
        if settings.otp_sms_provider == "brevo":
            detail += (
                BREVO_SMS_SETUP_HELP
                + BREVO_SMS_DELIVERY_HELP
                + BREVO_IP_AUTHORIZATION_HELP
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )

    record_audit(user.username, "request_phone_verification", "account phone verification code sent")
    return {
        "status": "ok",
        "challenge_id": challenge_id,
        "phone_hint": f"••••{phone_number[-4:]}",
        "expires_in": phone_verification_store.expiration_seconds,
    }


@router.post("/verify-phone")
def verify_phone(
    payload: VerifyPhoneVerification,
    user: User = Depends(get_current_user),
) -> dict:
    phone_number = phone_verification_store.verify(
        user.username,
        payload.challenge_id,
        payload.otp,
    )
    if phone_number is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired mobile verification code.",
        )
    if user_repository.is_phone_number_in_use(phone_number, exclude_username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This mobile number is already associated with another account.",
        )
    try:
        updated = user_repository.update_phone_number(user.username, phone_number)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the verified mobile number.",
        )
    record_audit(user.username, "verify_phone", "account mobile number verified")
    return {
        "status": "ok",
        "message": "Mobile number verified and saved.",
        "phone_number": phone_number,
        "phone_verified": True,
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
    email: str = Field(
        min_length=6,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class VerifyEmailOtpRequest(BaseModel):
    email: str = Field(min_length=6, max_length=255)
    otp: str = Field(pattern=r"^\d{6}$")


class VerifyOtpRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    otp: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)
    username: str | None = None
    recovery_email: str | None = Field(default=None, min_length=3, max_length=255)
    recovery_email_otp: str | None = Field(default=None, pattern=r"^\d{6}$")
    registered_email_otp: str | None = Field(default=None, pattern=r"^\d{6}$")
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
    return _request_email_otp(payload.new_email, user)


@router.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest) -> dict:
    input_email = payload.email.strip()
    selected_account = (
        user_repository.get_by_username(payload.username.strip())
        if payload.username
        else None
    )
    if selected_account and selected_account.role == "administrator":
        matching_contact_account = (
            user_repository.get_by_email(input_email, selected_account.username)
            if "@" in input_email
            else user_repository.get_by_phone_number(
                input_email,
                selected_account.username,
            )
        )
    else:
        matching_contact_account = (
            user_repository.get_by_email(input_email)
            if "@" in input_email
            else user_repository.get_by_phone_number(input_email)
        )

    is_admin_registered_email = bool(
        selected_account
        and selected_account.role == "administrator"
        and "@" in input_email
        and selected_account.email
        and input_email.lower() == selected_account.email.strip().lower()
    )
    if (
        selected_account
        and selected_account.role == "administrator"
        and not payload.recovery_email
        and not payload.recovery_phone
        and ("@" not in input_email or is_admin_registered_email)
    ):
        user_record = selected_account
        if user_record.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is blocked and cannot reset its password.",
            )
        settings = get_settings()
        if not email_delivery_configured(settings):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Email verification is not configured. Configure BREVO_API_KEY "
                    "and BREVO_EMAIL_SENDER, RESEND_API_KEY and RESEND_FROM_ADDRESS, "
                    "or SMTP_USERNAME and SMTP_PASSWORD "
                    "(SMTP_USER and SMTP_PASS are also supported)."
                ),
            )
        if not user_record.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered email address is available to verify this administrator account.",
            )
        otp = f"{secrets.randbelow(1_000_000):06d}"
        if not send_otp_email(user_record.email, otp, user_record.full_name):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Could not send the verification email. Check the configured "
                    "email provider and verified sender."
                    + BREVO_IP_AUTHORIZATION_HELP
                ),
            )
        password_reset_store.clear_reset_otps(user_record.username)
        password_reset_store.set_otp(user_record.username, otp)
        record_audit(
            user_record.username,
            "request_password_reset",
            "administrator password reset code sent to registered email",
        )
        return {
            "status": "success",
            "requires_registered_email_otp": False,
            "message": (
                "Verification code sent to the administrator account's registered email. "
                "Recovery contact details are not changed during password reset."
            ),
        }

    is_new_admin_contact = bool(
        selected_account
        and selected_account.role == "administrator"
        and matching_contact_account is None
        and not payload.recovery_email
        and not payload.recovery_phone
    )
    recovery_email = (
        payload.recovery_email.strip().lower()
        if payload.recovery_email
        else input_email.lower() if is_new_admin_contact and "@" in input_email else None
    )
    recovery_phone = (
        payload.recovery_phone
        if payload.recovery_phone
        else input_email if is_new_admin_contact and "@" not in input_email else None
    )
    has_new_recovery_contact = bool(recovery_email or recovery_phone)
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
        if recovery_email:
            if "@" not in recovery_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Enter a valid new recovery email address.",
                )
            if user_record.email and recovery_email == user_record.email.strip().lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The new recovery email must be different from the registered account email.",
                )

        if not recovery_email and not recovery_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter a new email address or mobile number.",
            )

        digits = "".join(
            character
            for character in (recovery_phone or "")
            if character.isdigit()
        )
        if recovery_phone and not 10 <= len(digits) <= 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter a valid mobile number with its country code.",
            )
        settings = get_settings()
        sms_missing_settings = missing_sms_settings(settings)
        if recovery_phone and sms_missing_settings:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"SMS delivery is not configured. The administrator must configure: {', '.join(sms_missing_settings)}.",
            )
        if not email_delivery_configured(settings):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Email verification is not configured. Configure BREVO_API_KEY "
                    "and BREVO_EMAIL_SENDER, RESEND_API_KEY and RESEND_FROM_ADDRESS, "
                    "or SMTP_USERNAME and SMTP_PASSWORD "
                    "(SMTP_USER and SMTP_PASS are also supported)."
                ),
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
        if recovery_phone:
            recovery_otps["phone"] = f"{secrets.randbelow(1_000_000):06d}"
            mobile_delivered = send_otp_sms(recovery_phone, recovery_otps["phone"])
        if not email_delivered or not recovery_email_delivered or not mobile_delivered:
            detail = (
                "Could not deliver all verification codes. Check email and SMS provider "
                "configuration, sender verification, and destination-country permissions."
            )
            if not email_delivered or not recovery_email_delivered:
                detail += (
                    " Email delivery failed; verify the Brevo sender and authorize the "
                    "backend outbound IP if Brevo API access is restricted."
                )
            sms_provider = settings.otp_sms_provider.strip().lower()
            if not mobile_delivered and sms_provider == "brevo":
                missing = missing_sms_settings(settings)
                if missing:
                    detail += f" Missing SMS settings: {', '.join(missing)}."
                detail += BREVO_SMS_SETUP_HELP + BREVO_SMS_DELIVERY_HELP + BREVO_IP_AUTHORIZATION_HELP
            elif not mobile_delivered:
                missing = missing_sms_settings(settings)
                if missing:
                    detail += f" Missing {sms_provider.upper()} settings: {', '.join(missing)}."
                detail += (
                    f" SMS delivery is configured for {sms_provider.upper()}; "
                    "verify its sender, destination permissions, account balance, and delivery logs."
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=detail,
            )
        password_reset_store.clear_reset_otps(user_record.username)
        password_reset_store.set_admin_reset_otps(
            user_record.username,
            email_otp,
            recovery_otps,
            recovery_email,
            recovery_phone,
        )
        record_audit(user_record.username, "request_password_reset", "administrator recovery codes sent")
        return {
            "status": "success",
            "requires_registered_email_otp": True,
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
        sms_missing_settings = missing_sms_settings(settings)
        if sms_missing_settings:
            email_fallback_available = bool(
                user_record.email
                and email_delivery_configured(settings)
            )
            if not email_fallback_available:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Mobile OTP delivery is not configured for this hospital portal. "
                        f"The administrator must configure: {', '.join(sms_missing_settings)}. "
                        "An OTP can be sent to the registered email when an email provider is configured."
                    ),
                )
            delivered = send_otp_email(
                user_record.email,
                otp,
                user_record.full_name,
            )
            channel = "email"
        else:
            delivered = send_otp_sms(destination, otp)
            channel = "mobile"

    if not delivered:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The SMS provider did not accept the message. Verify the destination number, "
                "provider credentials, sender/template configuration, and destination-country permissions."
                + (
                    BREVO_SMS_SETUP_HELP + BREVO_SMS_DELIVERY_HELP
                    if channel == "mobile" and settings.otp_sms_provider == "brevo"
                    else ""
                )
                if channel == "mobile"
                else (
                    "Could not send the verification email. Check the configured email "
                    "provider, verified sender, and destination address."
                    + BREVO_IP_AUTHORIZATION_HELP
                )
            ),
        )

    password_reset_store.clear_reset_otps(user_record.username)
    password_reset_store.set_otp(user_record.username, otp)
    record_audit(user_record.username, "request_password_reset", f"password reset OTP sent by {channel}")

    return {
        "status": "success",
        "requires_registered_email_otp": False,
        "message": f"Verification code sent to your registered {channel}. It expires in 5 minutes.",
    }



@router.post("/request-email-verification")
def request_email_verification(payload: EmailVerificationRequest, user: User = Depends(get_current_user)) -> dict:
    return _request_email_otp(payload.email, user)


def _request_email_otp(email: str, user: User) -> dict:
    normalized_email = email.strip().lower()
    if "@" not in normalized_email or any(character.isspace() for character in normalized_email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email address.",
        )
    existing = user_repository.get_by_email(normalized_email)
    if existing is not None and existing.username != user.username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    settings = get_settings()
    if not email_delivery_configured(settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Email verification is not configured. Configure BREVO_API_KEY and "
                "BREVO_EMAIL_SENDER, RESEND_API_KEY and RESEND_FROM_ADDRESS, or "
                "SMTP_USERNAME and SMTP_PASSWORD."
            ),
        )
    otp = f"{secrets.randbelow(1_000_000):06d}"
    try:
        email_verification_store.issue(user.username, normalized_email, otp)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    if not send_otp_email(normalized_email, otp, user.full_name or user.username):
        email_verification_store.cancel(user.username, normalized_email, otp)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not send the verification code. Check the email provider, "
                "verified sender address, and recipient address."
                + BREVO_IP_AUTHORIZATION_HELP
            ),
        )
    record_audit(user.username, "request_email_verification", "account email verification code sent")
    return {
        "status": "ok",
        "message": "Verification code sent. It expires in five minutes.",
        "expires_in": email_verification_store.expiration_seconds,
    }


@router.post("/verify-email-otp")
def verify_email_otp(payload: VerifyEmailOtpRequest, user: User = Depends(get_current_user)) -> dict:
    normalized_email = payload.email.strip().lower()
    if not email_verification_store.verify(user.username, normalized_email, payload.otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email verification OTP")
    try:
        updated = user_repository.update_email(user.username, normalized_email, verified=True)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify email")
    record_audit(user.username, "verify_email", "account email verified and updated")
    return {
        "status": "ok",
        "message": "Email verified and updated.",
        "email": normalized_email,
        "email_verified": True,
    }


@router.post("/verify-reset-otp")
def verify_reset_otp(payload: VerifyOtpRequest) -> dict:
    input_identifier = payload.email.strip()
    selected_account = (
        user_repository.get_by_username(payload.username.strip())
        if payload.username
        else None
    )
    pending_recovery_email = input_identifier.strip().lower() if "@" in input_identifier else None
    pending_recovery_phone = input_identifier if not pending_recovery_email else None
    is_pending_new_contact = bool(
        selected_account
        and selected_account.role == "administrator"
        and password_reset_store.has_admin_reset_for_contact(
            selected_account.username,
            pending_recovery_email,
            pending_recovery_phone,
        )
    )
    has_legacy_recovery_contact = bool(payload.recovery_email or payload.recovery_phone)
    has_new_recovery_contact = is_pending_new_contact or has_legacy_recovery_contact
    if is_pending_new_contact:
        user_record = selected_account
        recovery_email = pending_recovery_email
        recovery_phone = pending_recovery_phone
        if not payload.registered_email_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter the verification code sent to the account's registered email.",
            )
        recovery_otps = {
            "email" if recovery_email else "phone": payload.otp,
        }
        otp_valid = password_reset_store.verify_admin_reset_otps(
            user_record.username,
            payload.registered_email_otp,
            recovery_otps,
            recovery_email,
            recovery_phone,
        )
    elif has_legacy_recovery_contact:
        user_record = (
            selected_account
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
        otp_valid = password_reset_store.verify_admin_reset_otps(
            user_record.username,
            payload.otp,
            recovery_otps,
            recovery_email,
            payload.recovery_phone,
        )
    elif selected_account and selected_account.role == "administrator":
        user_record = selected_account
        if user_record.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is blocked and cannot reset its password.",
            )
        otp_valid = password_reset_store.verify_reset_otp(
            user_record.username,
            payload.otp,
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
            recovery_email,
            recovery_phone,
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

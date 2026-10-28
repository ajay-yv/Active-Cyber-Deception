from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.db.engines import SecuritySessionLocal
from app.models.security import UserAccount


def _normalize_phone_number(value: str | None) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        return digits[1:]
    return digits


def _normalize_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "none", "null"}
    if isinstance(value, int):
        return value != 0
    return bool(value)


@dataclass
class UserRecord:
    username: str
    password_hash: str
    role: str
    full_name: str
    email: str | None = None
    is_blocked: bool = False
    patient_record_id: str | None = None
    phone_number: str | None = None


class UserRepository:
    def get_by_username(self, username: str) -> UserRecord | None:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return None
            return UserRecord(
                username=row.username,
                password_hash=row.password_hash,
                role=row.role,
                full_name=row.full_name,
                email=row.email,
                is_blocked=_normalize_bool(getattr(row, "is_blocked", False)),
                patient_record_id=getattr(row, "patient_record_id", None),
                phone_number=getattr(row, "phone_number", None),
            )

    def create(self, record: UserRecord) -> UserRecord:
        with SecuritySessionLocal() as session:
            session.merge(UserAccount(
                username=record.username,
                password_hash=record.password_hash,
                role=record.role,
                full_name=record.full_name,
                email=record.email,
                phone_number=record.phone_number,
                patient_record_id=record.patient_record_id,
                is_blocked=record.is_blocked,
            ))
            session.commit()
        return record

    def update_password(self, username: str, new_hashed: str) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.password_hash = new_hashed
            session.add(row)
            session.commit()
        return True

    def update_email(self, username: str, new_email: str) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.email = new_email
            session.add(row)
            session.commit()
        return True

    def update_phone_number(self, username: str, phone_number: str) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.phone_number = phone_number
            session.add(row)
            session.commit()
        return True

    def update_password_and_recovery_contacts(
        self,
        username: str,
        password_hash: str,
        email: str | None,
        phone_number: str | None,
    ) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.password_hash = password_hash
            if email:
                row.email = email.strip().lower()
            if phone_number:
                row.phone_number = phone_number
            session.add(row)
            session.commit()
        return True

    def get_by_email(
        self,
        email: str,
        username: str | None = None,
    ) -> UserRecord | None:
        with SecuritySessionLocal() as session:
            query = session.query(UserAccount).filter(
                func.lower(func.trim(UserAccount.email)) == email.strip().lower()
            )
            if username:
                query = query.filter(UserAccount.username == username)
            row = query.first()
            if row is None:
                return None
            return UserRecord(
                username=row.username,
                password_hash=row.password_hash,
                role=row.role,
                full_name=row.full_name,
                email=row.email,
                is_blocked=_normalize_bool(getattr(row, "is_blocked", False)),
                patient_record_id=getattr(row, "patient_record_id", None),
                phone_number=getattr(row, "phone_number", None),
            )

    def get_by_phone_number(
        self,
        phone_number: str,
        username: str | None = None,
    ) -> UserRecord | None:
        normalized_phone = _normalize_phone_number(phone_number)
        if not normalized_phone:
            return None
        with SecuritySessionLocal() as session:
            query = session.query(UserAccount).filter(UserAccount.phone_number.isnot(None))
            if username:
                query = query.filter(UserAccount.username == username)
            rows = query.all()
            matches = [
                row for row in rows
                if _normalize_phone_number(row.phone_number) == normalized_phone
            ]
            if len(matches) != 1:
                return None
            row = matches[0]
            return UserRecord(
                username=row.username,
                password_hash=row.password_hash,
                role=row.role,
                full_name=row.full_name,
                email=row.email,
                is_blocked=_normalize_bool(getattr(row, "is_blocked", False)),
                patient_record_id=getattr(row, "patient_record_id", None),
                phone_number=getattr(row, "phone_number", None),
            )

    def link_google_patient(
        self,
        firebase_uid: str,
        patient_record_id: str,
        email: str,
        full_name: str,
        password_hash: str,
    ) -> UserRecord:
        username = f"google:{firebase_uid}"
        with SecuritySessionLocal() as session:
            linked_by_another_account = session.query(UserAccount.username).filter(
                UserAccount.patient_record_id == patient_record_id,
                UserAccount.username != username,
            ).first()
            if linked_by_another_account is not None:
                raise ValueError("This patient record is already linked to another Google account")

            row = session.get(UserAccount, username)
            if row is None:
                row = UserAccount(
                    username=username,
                    password_hash=password_hash,
                    role="patient",
                    full_name=full_name,
                    email=email,
                    patient_record_id=patient_record_id,
                    phone_number=None,
                    is_blocked=False,
                )
                session.add(row)
            else:
                if row.role != "patient":
                    raise ValueError("This Google account is not registered as a patient")
                if _normalize_bool(getattr(row, "is_blocked", False)):
                    raise ValueError("This patient account is blocked")
                row.patient_record_id = patient_record_id
                row.email = email
                row.full_name = full_name
                session.add(row)

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError("This patient record is already linked to another Google account") from exc
            return UserRecord(
                username=row.username,
                password_hash=row.password_hash,
                role=row.role,
                full_name=row.full_name,
                email=row.email,
                is_blocked=_normalize_bool(getattr(row, "is_blocked", False)),
                patient_record_id=row.patient_record_id,
                phone_number=getattr(row, "phone_number", None),
            )

    def set_block(self, username: str, blocked: bool) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.is_blocked = blocked
            session.add(row)
            session.commit()
        return True


user_repository = UserRepository()

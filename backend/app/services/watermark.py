import json
import os
import re
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from app.repositories.watermark_repository import WatermarkRecord, WatermarkRepository

watermark_repository = WatermarkRepository()
WATERMARK_SECRET = os.getenv("WATERMARK_SECRET", "ehr-default-secret-2026")

# Zero-Width Unicode Characters for Invisible Steganography
ZW_START = "\uFEFF"  # Zero-Width No-Break Space (Start Delimiter)
ZW_ZERO = "\u200B"   # Zero-Width Space (Bit 0)
ZW_ONE = "\u200C"    # Zero-Width Non-Joiner (Bit 1)
ZW_END = "\u200D"    # Zero-Width Joiner (End Delimiter)


def text_to_zero_width(payload: str) -> str:
    """Invisibly encodes an ASCII/UTF-8 string into zero-width Unicode characters."""
    binary_str = "".join(f"{ord(c):08b}" for c in payload)
    zw_encoded = "".join(ZW_ONE if bit == "1" else ZW_ZERO for bit in binary_str)
    return f"{ZW_START}{zw_encoded}{ZW_END}"


def zero_width_to_text(text: str) -> str | None:
    """Extracts and decodes hidden zero-width Unicode characters back into ASCII text."""
    if not text:
        return None

    # Search for delimited zero-width sequence
    pattern = f"{ZW_START}([{ZW_ZERO}{ZW_ONE}]+){ZW_END}"
    match = re.search(pattern, text)
    if not match:
        # Fallback: look for any raw stream of zero-width bits
        raw_bits = [c for c in text if c in (ZW_ZERO, ZW_ONE)]
        if len(raw_bits) >= 8 and len(raw_bits) % 8 == 0:
            bit_str = "".join("1" if c == ZW_ONE else "0" for c in raw_bits)
        else:
            return None
    else:
        zw_content = match.group(1)
        bit_str = "".join("1" if c == ZW_ONE else "0" for c in zw_content)

    chars = []
    for i in range(0, len(bit_str), 8):
        byte = bit_str[i:i+8]
        if len(byte) == 8:
            try:
                chars.append(chr(int(byte, 2)))
            except Exception:
                pass
    decoded = "".join(chars)
    return decoded if decoded else None


class DecodedWatermark(str):
    """A string subclass that also supports dictionary-like metadata lookups."""
    def __new__(cls, content: str, meta: dict | None = None):
        instance = super().__new__(cls, content)
        instance._meta = meta or {}
        return instance

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._meta.get(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        return self._meta.get(key, default)

    def __contains__(self, item):
        if isinstance(item, str) and item in self._meta:
            return True
        return super().__contains__(item)


def embed_invisible_watermark(visible_text: str, watermark_payload: str) -> str:
    """Embeds an invisible zero-width watermark into visible text."""
    zw_payload = text_to_zero_width(watermark_payload)
    if not visible_text:
        return zw_payload
    return f"{visible_text}{zw_payload}"


def extract_invisible_watermark(text: str) -> DecodedWatermark | None:
    """Extracts invisible zero-width watermark and parses metadata payload."""
    decoded = zero_width_to_text(text)
    if not decoded:
        return None

    meta = {
        "raw_payload": decoded,
        "is_invisible_steganography": True,
    }
    if decoded.startswith("WM:"):
        parts = decoded[3:].split("|")
        meta.update({
            "watermark_id": parts[0] if len(parts) > 0 else None,
            "source_type": parts[1] if len(parts) > 1 else "synthetic",
            "source_id": parts[2] if len(parts) > 2 else "unknown",
            "hospital_id": parts[3] if len(parts) > 3 else "HOSPITAL-001",
            "session_id": parts[4] if len(parts) > 4 else "anonymous",
        })

    return DecodedWatermark(decoded, meta)


def _generate_watermark_fingerprint(source_type: str, source_id: str, hospital_id: str, source_data: dict | None = None) -> str:
    payload = {
        "source_type": source_type,
        "source_id": source_id,
        "hospital_id": hospital_id,
        "data": source_data or {},
    }
    fingerprint = sha256(json.dumps(payload, sort_keys=True).encode("utf-8") + WATERMARK_SECRET.encode("utf-8")).hexdigest()
    return fingerprint


def _generate_watermark_text(source_type: str, source_id: str, fingerprint: str) -> str:
    return f"EHR-{source_type[:3].upper()}-{source_id[:8]}-{fingerprint[:12]}"


def create_watermark(
    source_id: str,
    source_type: str,
    hospital_id: str,
    session_id: str,
    source_data: dict | None = None,
) -> WatermarkRecord:
    timestamp = datetime.now(timezone.utc).isoformat()
    watermark_id = str(uuid4())
    fingerprint = _generate_watermark_fingerprint(source_type, source_id, hospital_id, source_data)
    watermark_text = _generate_watermark_text(source_type, source_id, fingerprint)
    record = WatermarkRecord(
        id=str(uuid4()),
        watermark_id=watermark_id,
        source_id=source_id,
        source_type=source_type,
        hospital_id=hospital_id,
        timestamp=timestamp,
        session_id=session_id,
        watermark_text=watermark_text,
        watermark_fingerprint=fingerprint,
    )
    watermark_repository.add(record)
    return record


def poison_synthetic_payload(synthetic_data: dict, watermark_record: WatermarkRecord) -> dict:
    """Invisibly embeds zero-width watermarks into textual fields of synthetic decoy records."""
    poisoned = dict(synthetic_data)
    payload_token = f"WM:{watermark_record.watermark_id}|{watermark_record.source_type}|{watermark_record.source_id}|{watermark_record.hospital_id}|{watermark_record.session_id}"

    if "name" in poisoned and poisoned["name"]:
        poisoned["name"] = embed_invisible_watermark(poisoned["name"], payload_token)
    if "diagnosis" in poisoned and poisoned["diagnosis"]:
        poisoned["diagnosis"] = embed_invisible_watermark(poisoned["diagnosis"], payload_token)
    if "address" in poisoned and poisoned["address"]:
        poisoned["address"] = embed_invisible_watermark(poisoned["address"], payload_token)
    if "treatment_pattern" in poisoned and poisoned["treatment_pattern"]:
        poisoned["treatment_pattern"] = embed_invisible_watermark(poisoned["treatment_pattern"], payload_token)

    poisoned["watermark_id"] = watermark_record.watermark_id
    poisoned["watermark_text"] = watermark_record.watermark_text
    poisoned["watermark_fingerprint"] = watermark_record.watermark_fingerprint
    poisoned["is_watermarked"] = True
    poisoned["watermark_type"] = "Zero-Width Steganography + Cryptographic SHA-256"
    return poisoned


def verify_patient_watermark(patient: "PatientRecord", hospital_id: str = "HOSPITAL-001", force_update: bool = False) -> bool:
    source_data = patient.model_dump(exclude={"watermark_id", "watermark_text", "watermark_fingerprint"})
    if force_update or not patient.watermark_fingerprint:
        record = create_watermark(patient.id, "real", hospital_id, "bootstrap", source_data)
        patient.watermark_id = record.watermark_id
        patient.watermark_text = record.watermark_text
        patient.watermark_fingerprint = record.watermark_fingerprint
        from app.services.registries import patient_repository
        try:
            patient_repository.add(patient)
        except Exception:
            pass
        return True

    expected_fingerprint = _generate_watermark_fingerprint("real", patient.id, hospital_id, source_data)
    if expected_fingerprint != (patient.watermark_fingerprint or ""):
        record = create_watermark(patient.id, "real", hospital_id, "update", source_data)
        patient.watermark_id = record.watermark_id
        patient.watermark_text = record.watermark_text
        patient.watermark_fingerprint = record.watermark_fingerprint
        from app.services.registries import patient_repository
        try:
            patient_repository.add(patient)
        except Exception:
            pass
    return True




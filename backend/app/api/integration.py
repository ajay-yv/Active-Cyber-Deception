from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import User, require_roles
from app.services.audit import record_audit
from app.services.integration import fetch_lab_results
from app.services.registries import patient_repository
from fastapi import File, UploadFile
import os
from uuid import uuid4

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
os.makedirs(UPLOAD_ROOT, exist_ok=True)

router = APIRouter(prefix="/integration", tags=["integration"])


@router.get("/lab-results/{patient_id}")
def get_lab_results(
    patient_id: str,
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist", "patient")),
) -> dict:
    if current_user.role == "patient":
        patient = patient_repository.find_by_id(patient_id)
        if patient is None or patient.id != current_user.patient_record_id:
            raise HTTPException(status_code=404, detail="Lab results not found")
    lab_result = fetch_lab_results(patient_id)
    if lab_result is None:
        raise HTTPException(status_code=404, detail="Lab results not found")
    record_audit(current_user.username, "fetch_lab_results", f"patient_id={patient_id}")
    return lab_result


@router.post("/upload")
def upload_files(files: list[UploadFile] = File(...), _: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    saved = []
    for f in files:
        ext = os.path.splitext(f.filename)[1]
        name = f"{uuid4().hex}{ext}"
        dest = os.path.join(UPLOAD_ROOT, name)
        with open(dest, 'wb') as out:
            out.write(f.file.read())
        saved.append({"original": f.filename, "stored": name, "path": dest})
    record_audit("system", "upload_files", f"files={','.join([s['stored'] for s in saved])}")
    return {"files": saved}

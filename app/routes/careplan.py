# app/routes/careplan.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile, os, asyncio
from ..pdf_parser import parse_pdf
from ..service.crud_careplan import create_careplan, get_pending_appointments, get_medication_by_patient
from ..models import CarePlanCreate

router = APIRouter()

@router.post("/upload-careplan")
async def upload_careplan(patient_id: str = Form(...), file: UploadFile = File(...)):
    # save uploaded file to a temp file
    suffix = os.path.splitext(file.filename)[1] or ".pdf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()
        # parse in a threadpool (pdf parsing is blocking)
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(None, parse_pdf, tmp.name, patient_id)

        parsed_careplan: CarePlanCreate = await loop.run_in_executor(None, parse_pdf, tmp.name, patient_id)
        inserted = await create_careplan(parsed_careplan.dict())  # convert to dict for Mongo insertion

        return {"status": "ok", "careplan": inserted}

    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass

@router.get("/patients/{patient_id}/pending-appointments")
async def pending_appointments(patient_id: str):
    pending = await get_pending_appointments(patient_id)
    return {"patient_id": patient_id, "pending": pending}

@router.get("/patients/{patient_id}/medications")
async def get_medication(patient_id: str):
    doc = await get_medication_by_patient(patient_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Medications not found")
    return doc

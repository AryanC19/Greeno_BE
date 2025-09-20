# app/routes/careplan.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile, os, asyncio
from ..pdf_parser import parse_pdf
from ..service.crud_careplan import create_careplan, get_medication_by_patient , get_careplan
from ..models import CarePlanCreate

router = APIRouter()


@router.post("/upload-careplan")
async def upload_careplan(file: UploadFile = File(...)):
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
        parsed_careplan: CarePlanCreate = await loop.run_in_executor(None, parse_pdf, tmp.name, "1")  # hardcoded patient_id="1"
        inserted = await create_careplan(parsed_careplan.dict())  # convert to dict for Mongo insertion
        # notify subscribers

        return {"status": "ok", "careplan": inserted}

    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass



# 🔹 New endpoint to view entire careplan
@router.get("/careplan")
async def view_careplan():
    doc = await get_careplan()
    if not doc:
        raise HTTPException(status_code=404, detail="No careplan found")
    return {"status": "ok", "careplan": doc}



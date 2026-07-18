from fastapi import APIRouter, UploadFile, File, Form
from typing import List

from backend.services.analysis_service import handle_upload

router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "Insurance Gap Analysis API Running"
    }


@router.post("/upload/")
async def upload_files(

    user_id: str = Form(...),
    case_id: str = Form(...),
    document_type: str = Form(...),

    # Frontend sends JSON string
    policy_config: str = Form(None),

    files: List[UploadFile] = File(...)

):

    return handle_upload(
        user_id=user_id,
        case_id=case_id,
        document_type=document_type,
        policy_config=policy_config,
        files=files,
    )

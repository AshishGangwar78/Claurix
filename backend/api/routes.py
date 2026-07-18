from fastapi import APIRouter, UploadFile, File, Form
from typing import List

from backend.schemas.premium import PremiumExtractRequest, PremiumExtractResponse
from backend.services.analysis_service import handle_upload
from backend.services.premium_calculation.service import extract_premium_values

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


@router.post(
    "/premium/extract/",
    response_model=PremiumExtractResponse,
)
def extract_premium(
    payload: PremiumExtractRequest,
):
    """
    Extract Total Sum Insured and Premium from one or more policy blocks.

    Accepts block grids or sparse cell lists. Does not alter the clause
    extraction pipeline.
    """
    blocks = [block.model_dump() for block in payload.blocks]
    config = payload.config.model_dump(exclude_none=True) if payload.config else None

    return extract_premium_values(
        blocks=blocks,
        config=config,
    )

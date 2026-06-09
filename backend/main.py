from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import shutil
import os
import json
from datetime import datetime

from backend.extraction.pdf_extractor import extract_pdf_text
from backend.extraction.policy_block_extractor import extract_policy_block
from backend.llm.policy_clause_extractor import extract_policy_clauses
from backend.gap_analysis.process_policy import process_policy
from backend.gap_analysis.policy_merger import (
    merge_policy_files
)

app = FastAPI()

BASE_STORAGE_DIR = "backend/storage"

os.makedirs(BASE_STORAGE_DIR, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "Insurance Gap Analysis API Running"
    }


@app.post("/upload/")
async def upload_files(

    user_id: str = Form(...),
    case_id: str = Form(...),
    document_type: str = Form(...),

    # Frontend sends JSON string
    policy_config: str = Form(None),

    files: List[UploadFile] = File(...)

):

    if document_type.lower() not in ["rfq", "proposals"]:

        return {
            "error": "document_type must be rfq or proposals"
        }

    base_case_dir = os.path.join(
        BASE_STORAGE_DIR,
        "users",
        user_id,
        case_id,
        document_type
    )

    upload_dir = os.path.join(
        base_case_dir,
        "uploads"
    )

    results_dir = os.path.join(
        base_case_dir,
        "results"
    )

    policies_dir = os.path.join(
        results_dir,
        "policies"
    )
    merged_dir = os.path.join(
        results_dir,
        "merged"
    )


    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(policies_dir, exist_ok=True)
    os.makedirs(merged_dir, exist_ok=True)

    uploaded_files = []

    policy_list = []

    if policy_config:

        try:

            policy_list = json.loads(
                policy_config
            )

        except Exception as e:

            return {
                "error":
                f"Invalid policy_config: {str(e)}"
            }

    print("\n========================")
    print("UPLOAD REQUEST RECEIVED")
    print("========================")
    print(f"User ID      : {user_id}")
    print(f"Case ID      : {case_id}")
    print(f"Document Type: {document_type}")
    print(f"Files Count  : {len(files)}")
    print("========================\n")



    for file in files:

        print("\n=================================") 
        print(f"PROCESSING FILE: {file.filename}")
        print("=================================\n")   
        company_name = os.path.splitext(
            file.filename
        )[0]

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        new_filename = (
            f"{timestamp}_{file.filename}"
        )

        file_path = os.path.join(
            upload_dir,
            new_filename
        )

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        uploaded_files.append({
            "original_filename":
                file.filename,
            "stored_filename":
                new_filename,
            "file_path":
                file_path

         })

        # =====================
        # RFQ
        # =====================

        if document_type.lower() == "rfq":

            print(
                f"RFQ Stored Successfully: {file.filename}"
            )

    # =====================
    # PROPOSALS
    # =====================

        elif document_type.lower() == "proposals":

            company_results_dir = os.path.join(
                policies_dir,
                company_name
            )

            os.makedirs(
                company_results_dir,
                exist_ok=True
            )

            for policy_info in policy_list:

                policy_name = policy_info["policy"]

                sheet_name = policy_info["sheet_name"]

                start_row = policy_info["start_row"]

                end_row = policy_info["end_row"]

                print(
                    f"\n[POLICY START]"
                )
                print(
                    f"Company : {company_name}"
                )
                print(
                    f"Policy  : {policy_name}"
                )
                print(
                    f"Sheet   : {sheet_name}"
                )
                print(
                    f"Rows    : {start_row} -> {end_row}"
                )

                policy_block = extract_policy_block(

                    file_path,

                    sheet_name,

                    start_row,

                    end_row

                )
                print(
                f"[BLOCK EXTRACTED] {policy_name}"
                )
                print(
                f"Rows In Block: {len(policy_block)}"
                )
                print(
                f"Columns In Block: {len(policy_block.columns)}"
                )

                structured_policy = extract_policy_clauses(
                company_name,           
                policy_name,
                sheet_name,
                start_row,
                end_row,
                policy_block
                )
                print(
                f"[QWEN FINISHED] {policy_name}"
                )

                structured_policy= process_policy(
                    structured_policy
                )
                print(
                    f"[UW CLASSIFICATION FINISHED] {policy_name}"
                )
                policy_json_path = os.path.join(
                company_results_dir,
                f"{policy_name}.json"
                )

                with open(
                policy_json_path,
                "w",
                encoding="utf-8"
  
                ) as json_file:

                    json.dump(
                    structured_policy,
                    json_file,
                    indent=4,
                    ensure_ascii=False,
                    default=str
                )
            
            # print(
            #     policy_block.to_string()
            # )

    else:

        print(
            f"Unsupported File Type: {file.filename}"
        )

    print("\n========================")
    print("MERGING POLICIES")
    print("========================")
    
    for policy_info in policy_list:

        policy_name = policy_info["policy"]

        policy_files = []

        for company_folder in os.listdir(
        policies_dir
        ):

            policy_path = os.path.join(
                policies_dir,
                company_folder,
                f"{policy_name}.json"
            )

            if os.path.exists(
                policy_path
            ):

                policy_files.append(
                    policy_path
                )

        if len(policy_files) > 1:

            merged_policy = merge_policy_files(
                policy_files
            )

            merged_path = os.path.join(
                merged_dir,
                f"{policy_name}.json"
            )
            with open(
                merged_path,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    merged_policy,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            print(
                f"[MERGED] {policy_name}"
            )
        else:
            print(
                f"[SKIPPED] {policy_name} - Only {len(policy_files)} file found"
            )

    return {

        "status":
            "success",

        "user_id":
            user_id,

        "case_id":
            case_id,

        "document_type":
            document_type,

        "policies_processed":
            len(policy_list),

        "files_uploaded":
            len(uploaded_files)

    }
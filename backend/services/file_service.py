import json
import os
import shutil
from datetime import datetime

import pdfplumber
import pandas as pd

from backend.core.config import BASE_STORAGE_DIR


def extract_pdf_text(pdf_path):

    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:
                full_text += text + "\n"

    return full_text


def extract_policy_block(
    excel_path,
    sheet_name,
    start_row,
    end_row
):

    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        header=None,
        dtype=str
    )

    start_idx = start_row - 1
    end_idx = end_row

    block = df.iloc[
        start_idx:end_idx
    ].copy()

    block["__excel_row__"] = (
        block.index + 1
    )

    block = block.fillna("")

    print(
        block["__excel_row__"].tolist()
    )

    return block


def build_case_directories(user_id, case_id, document_type):
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

    return {
        "base_case_dir": base_case_dir,
        "upload_dir": upload_dir,
        "results_dir": results_dir,
        "policies_dir": policies_dir,
        "merged_dir": merged_dir,
    }


def save_upload_file(upload_file, upload_dir):
    company_name = os.path.splitext(
        upload_file.filename
    )[0]

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    new_filename = (
        f"{timestamp}_{upload_file.filename}"
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
            upload_file.file,
            buffer
        )

    return {
        "company_name": company_name,
        "original_filename": upload_file.filename,
        "stored_filename": new_filename,
        "file_path": file_path,
    }


def ensure_company_results_dir(policies_dir, company_name):
    company_results_dir = os.path.join(
        policies_dir,
        company_name
    )

    os.makedirs(
        company_results_dir,
        exist_ok=True
    )

    return company_results_dir


def save_policy_json(company_results_dir, policy_name, structured_policy):
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

    return policy_json_path


def save_merged_json(merged_dir, policy_name, merged_policy):
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

    return merged_path


def list_policy_files(policies_dir, policy_name):
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

    return policy_files


def merged_excel_path(merged_dir, policy_name):
    return os.path.join(
        merged_dir,
        f"{policy_name}.xlsx"
    )

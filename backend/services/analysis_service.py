import json

from backend.services import file_service
from backend.services.clause_extraction.module1 import extract_policy_clauses
from backend.services.gap_analyzer import (
    json_to_excel,
    merge_policy_files,
    process_policy,
)


def handle_upload(
    user_id,
    case_id,
    document_type,
    policy_config,
    files,
):

    if document_type.lower() not in ["rfq", "proposals"]:

        return {
            "error": "document_type must be rfq or proposals"
        }

    directories = file_service.build_case_directories(
        user_id,
        case_id,
        document_type,
    )

    upload_dir = directories["upload_dir"]
    policies_dir = directories["policies_dir"]
    merged_dir = directories["merged_dir"]

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
        saved = file_service.save_upload_file(
            file,
            upload_dir,
        )

        company_name = saved["company_name"]
        file_path = saved["file_path"]

        uploaded_files.append({
            "original_filename":
                saved["original_filename"],
            "stored_filename":
                saved["stored_filename"],
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

            company_results_dir = file_service.ensure_company_results_dir(
                policies_dir,
                company_name,
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

                policy_block = file_service.extract_policy_block(

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
                file_service.save_policy_json(
                    company_results_dir,
                    policy_name,
                    structured_policy,
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

        policy_files = file_service.list_policy_files(
            policies_dir,
            policy_name,
        )

        if len(policy_files) > 1:

            merged_policy = merge_policy_files(
                policy_files
            )

            merged_path = file_service.save_merged_json(
                merged_dir,
                policy_name,
                merged_policy,
            )

            excel_path = file_service.merged_excel_path(
                merged_dir,
                policy_name,
            )

            json_to_excel(
                merged_path,
                excel_path
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

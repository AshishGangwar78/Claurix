import json

from backend.services.clause_extraction.module2 import classify_clause_rows
from backend.services.clause_extraction.module3 import identify_columns
from backend.services.clause_extraction.module4 import build_policy_json


def extract_policy_clauses(
    company_name,
    policy_name,
    sheet_name,
    start_row,
    end_row,
    policy_block_df
):

    rows_for_llm = [] # this will contain data for llm

    row_metadata = {} # this is for metadata

    

    for local_idx, (_, row) in enumerate(#iterating through block rawwise
        policy_block_df.iterrows()
    ):

        excel_row = start_row + local_idx 

        columns = []

        for col_idx, value in enumerate(row):

            value = str(value).strip()

            if (
                value == ""
                or value.lower() == "nan"
                or value == "0"
                or value == "0.0"
            ):
                continue
            if col_idx == len(row) - 1:
                continue
            columns.append({

                "column_index":
                    col_idx + 1,

                "value":
                    value

    })

        rows_for_llm.append({

            "row_id":
                local_idx,

            "columns":
                columns

        })
        
        row_metadata[local_idx] = {

            "sheet_name":
                sheet_name,

            "excel_row":
                excel_row

        }

    print("\n====================================")
    print("QWEN INPUT PREPARATION")
    print("====================================")
    print(f"Rows Sent To Qwen : {len(rows_for_llm)}")
    print(f"Columns Found     : {len(policy_block_df.columns)}")
    print("====================================\n")
    print(
            json.dumps(
            rows_for_llm,
            indent=2
           )
        )

    clause_rows= classify_clause_rows(
        company_name,
        policy_name,
        rows_for_llm,
        row_metadata
    )
    if not clause_rows:
        print(
            f"[NO Clause Rows Found]{policy_name}"
        )
        return []

    column_info = identify_columns(
        company_name,
        policy_name,
        clause_rows
    )

    final_json=build_policy_json(
        company_name,
        policy_name,
        sheet_name,
        clause_rows,
        column_info
    )

    # print(
    # json.dumps(
    #     column_info,
    #     indent=2
    # )
    # )
    
    return final_json

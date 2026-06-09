import json
import ollama


def column_number_to_excel(col_num): #this is for changing column no. to colmun name

    result = ""# example 1 to A , 28 to AB

    while col_num > 0:

        col_num, remainder = divmod(
            col_num - 1,
            26
        )

        result = chr(
            65 + remainder
        ) + result

    return result


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
    
#this is i am calling modelu 2 it is taking all the colmns and checking
#it is a clause row or not....
    
def classify_clause_rows(
        company_name,
        policy_name,
        rows_for_llm,
        row_metadata
    ):
    print("\n====================================")
    print("CLAUSE ROW CLASSIFICATION STARTED")
    print("====================================")

    print(
        f"Rows Sent To Qwen : {len(rows_for_llm)}"
    )


    prompt = f"""
You are an insurance clause detector.

Company:
{company_name}

Policy:
{policy_name}

Task:
You MUST classify EVERY row.
Return one JSON object for EVERY row_id provided.
If 8 rows are given, return exactly 8 JSON objects.
Never skip rows.
Output example:
[
  {{
    "row_id":0,
    "is_clause":false
  }},
  {{
    "row_id":1,
    "is_clause":true
  }}
]
Clause rows include:
- Coverage clauses
- Extensions
- Conditions
- Deductibles
- Excess clauses
- Special terms

NOT clause rows include:
- Policy titles
- Section titles
- Premium rows
- Rate rows
- Total rows
- Sum insured rows
- Blank rows

Return ONLY valid json array
Rows:

{json.dumps(rows_for_llm, indent=2)}
"""

    try:

        response = ollama.chat(

            model="qwen2.5:7b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

        )

        content = response["message"]["content"]
        # print("\n========== RAW CONTENT ==========")
        # print(repr(content))
        # print("================================")
        print("\n====================================")
        print("RAW QWEN RESPONSE")
        print("====================================")
        print(content)
        print("====================================\n")

        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        )

        content = content.strip()

        result = json.loads(
            content
        )
        # print("\n========== TYPE OF RESULT ==========")
        # print(type(result))

        # print("\n========== RESULT BEFORE NORMALIZATION ==========")
        # print(result)

        if isinstance(result, dict):

            if "rows" in result:

                result = result["rows"]

            elif "row_id" in result:

                result = [result]

            else:

                result = []
        
        # print("\n========== RESULT AFTER NORMALIZATION ==========")
        # print(result)

        clause_row_ids = []

        for item in result:

            if item.get(
                "is_clause",
                False
            ):

                clause_row_ids.append(
                    item["row_id"]
                )
        print("\n========== CLAUSE ROW IDS ==========")
        print(clause_row_ids)

        clause_rows = []#contians clause rows

        for row in rows_for_llm:

            if row["row_id"] in clause_row_ids:

                clause_rows.append({

                    "row_id":
                        row["row_id"],

                    "excel_row":
                        row_metadata[
                            row["row_id"]
                        ]["excel_row"],

                    "columns":
                        row["columns"]
                    })
        # print("\n====================================")
        # print("CLAUSE ROWS")
        # print("====================================")

        print(
            json.dumps(
            clause_rows,
            indent=2
            )
         ) #they will print clauses rows
        print(
            f"Clause Rows Found : {len(clause_rows)}"
        )

        return clause_rows

    except Exception as e:

        print(
            f"[CLAUSE DETECTION ERROR] {str(e)}"
        )

        return [] 


#---------------------------------------------------------------
#Module 3 for identifying colums

def identify_columns(
        company_name,
        policy_name,
        clause_rows
):  

    # sample_rows = clause_rows[:min(3,len(clause_rows))]
    sample_rows = clause_rows
    
    prompt = f"""
You are analyzing an insurance proposal table.

Determine which column contains:

1. Clause Text
2. Requirement
3. UW Remark

Rules:

- Clause column contains insurance clauses/extensions/conditions.
- Requirement column contains values like Yes, Required, Limits, Sum Insured.
- UW Remark column contains insurer responses such as:
  Agreed,
  Not Agreed,
  Covered,
  As per policy,
  Specific limits.

Return ONLY JSON.

Output Format:

{{
    "clause_column": 2,
    "requirement_column": 3,
    "uw_remark_column": 6
}}

Rows:

{json.dumps(sample_rows, indent=2)}
"""
    try:

        response = ollama.chat(

            model="qwen2.5:7b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json"

        )
        content = response["message"]["content"]
        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        )

        content = content.strip()
        columns=json.loads(content)

        print("\n====================================")
        print("COLUMN DETECTION")
        print("====================================")

        print(
            json.dumps(
            columns,
            indent=2
            )
        )
    
        return columns
    
    except Exception as e:

        print(
            f"[COLUMN DETECTION ERROR] {str(e)}"
        )

        return {}
    
#----------------------------------------------------------#
#Module 4 for final json output
#NO AI just python
def get_column_value(

    columns,

    target_column

):

    for cell in columns:

        if cell["column_index"] == target_column:

            return cell["value"]

    return ""


def build_policy_json(
    company_name,
    policy_name,
    sheet_name,
    clause_rows,
    column_info
):
    #here we have to change if clause column,reqiurement, uw remarks not found
    #raise exceptions
    clause_column = column_info.get(
        "clause_column"
    )

    requirement_column = column_info.get(
        "requirement_column"
    )

    uw_remark_column = column_info.get(
        "uw_remark_column"
    )

    clauses = []
    
    for row in clause_rows:

        clause_text = get_column_value(

            row["columns"],

            clause_column

        )

        requirement = get_column_value(

            row["columns"],

            requirement_column

        )

        uw_remark = get_column_value(

            row["columns"],

            uw_remark_column

        )

        clauses.append({

            "clause":
                clause_text,

            "requirement":
                requirement,

            "uw_remark":
                uw_remark,

            "source": {

                "sheet_name":
                    sheet_name,

                "excel_row":
                    row["excel_row"],

                "clause_cell":
                    f"{column_number_to_excel(clause_column)}{row['excel_row']}",

                "requirement_cell":
                    f"{column_number_to_excel(requirement_column)}{row['excel_row']}",

                "uw_remark_cell":
                    f"{column_number_to_excel(uw_remark_column)}{row['excel_row']}"

            }

        })
    
    return {

        "company":
            company_name,

        "policy":
            policy_name,
        
        "column_mapping": {

            "clause_column":
                clause_column,

            "requirement_column":
                requirement_column,

            "uw_remark_column":
                uw_remark_column

        },

        "clauses":
            clauses

    }
#final result stores in the rsult folder now.
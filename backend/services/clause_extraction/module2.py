import json

from backend.services import llm_service


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

        response = llm_service.chat(

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

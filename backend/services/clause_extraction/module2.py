import json

from backend.services import llm_service


# Rule-based clause markers (case-insensitive, partial match).
CLAUSE_KEYWORDS = [
    "required",
    "requirement",
    "mandatory",
    "must",
    "shall",
    "minimum requirement",
    "coverage required",
    "limit required",
]


def _row_matches_clause_keywords(row):
    """Return True if any cell value contains a clause keyword."""

    for cell in row.get("columns", []):

        value = str(
            cell.get("value", "")
        ).lower()

        for keyword in CLAUSE_KEYWORDS:

            if keyword in value:

                return True

    return False


def _build_clause_row(row, row_metadata):

    return {

        "row_id":
            row["row_id"],

        "excel_row":
            row_metadata[
                row["row_id"]
            ]["excel_row"],

        "columns":
            row["columns"]
    }


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

    rule_based_clause_ids = []
    rows_needing_llm = []

    for row in rows_for_llm:

        if _row_matches_clause_keywords(row):

            rule_based_clause_ids.append(
                row["row_id"]
            )

        else:

            rows_needing_llm.append(
                row
            )

    print(
        f"Rule-Based Clause Rows : {len(rule_based_clause_ids)}"
    )
    print(
        f"Rows Sent To Qwen : {len(rows_needing_llm)}"
    )

    clause_row_ids = list(
        rule_based_clause_ids
    )

    if not rows_needing_llm:

        print(
            "[RULE-BASED] All rows classified without LLM"
        )

    else:

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

{json.dumps(rows_needing_llm, indent=2)}
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

            for item in result:

                if item.get(
                    "is_clause",
                    False
                ):

                    clause_row_ids.append(
                        item["row_id"]
                    )

        except Exception as e:

            print(
                f"[CLAUSE DETECTION ERROR] {str(e)}"
            )

            if not rule_based_clause_ids:

                return []

    print("\n========== CLAUSE ROW IDS ==========")
    print(clause_row_ids)

    clause_rows = []#contians clause rows

    for row in rows_for_llm:

        if row["row_id"] in clause_row_ids:

            clause_rows.append(
                _build_clause_row(
                    row,
                    row_metadata
                )
            )
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

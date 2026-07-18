import json

from backend.services import llm_service


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

        response = llm_service.chat(

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

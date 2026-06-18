import json

import pandas as pd


def json_to_excel(json_file, excel_file):

    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    rows = []

    for clause in data.get("clauses", []):
        row = {
            "Excel Row": clause.get("excel_row", ""),
            "Clause": clause.get("clause", ""),
            "Requirement": clause.get("requirement", "")
        }

        for insurer in clause.get("insurers", []):
            company = insurer.get("company", "Unknown Insurer")
            row[f"{company} Remark"] = insurer.get("uw_remark", "")
            row[f"{company} Status"] = insurer.get("remark_status", "")

        rows.append(row)

    pd.DataFrame(rows).to_excel(excel_file, index=False)

    print(f"[EXCEL EXPORTED] {excel_file}")


def merge_policy_files(policy_files):

    policies = []

    for file_path in policy_files:
        with open(file_path, "r", encoding="utf-8") as file:
            policies.append(json.load(file))

    if not policies:
        return {}

    master_policy = policies[0]

    # Create row lookup for every policy
    policy_maps = []

    for policy in policies:

        row_map = {}

        for clause in policy.get("clauses", []):

            row = clause.get(
                "source",
                {}
            ).get(
                "excel_row"
            )

            if row is not None:
                row_map[row] = clause

        policy_maps.append(
            {
                "company": policy.get("company", ""),
                "row_map": row_map
            }
        )

    merged_clauses = []

    for master_clause in master_policy.get("clauses", []):

        excel_row = master_clause.get(
            "source",
            {}
        ).get(
            "excel_row"
        )

        insurers = []

        for policy_map in policy_maps:

            clause = policy_map[
                "row_map"
            ].get(
                excel_row
            )

            if clause:

                insurers.append({
                    "company":
                        policy_map["company"],

                    "uw_remark":
                        clause.get(
                            "uw_remark",
                            ""
                        ),

                    "remark_status":
                        clause.get(
                            "remark_status",
                            ""
                        ),

                    "source":
                        clause.get(
                            "source",
                            {}
                        )
                })

            else:

                insurers.append({
                    "company":
                        policy_map["company"],

                    "uw_remark":
                        "",

                    "remark_status":
                        "",

                    "source":
                        {}
                })

        merged_clauses.append({

            "excel_row":
                excel_row,

            "clause":
                master_clause.get(
                    "clause",
                    ""
                ),

            "requirement":
                master_clause.get(
                    "requirement",
                    ""
                ),

            "insurers":
                insurers

        })

    return {

        "policy":
            master_policy.get(
                "policy",
                ""
            ),

        "clauses":
            merged_clauses

    }

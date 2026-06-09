import json


def merge_policy_files(
    policy_files
):

    policies = []

    for file_path in policy_files:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            policies.append(
                json.load(file)
            )

    if not policies:

        return {}

    master_policy = policies[0]

    merged_clauses = []

    for idx, master_clause in enumerate(
        master_policy["clauses"]
    ):

        excel_row = master_clause[
            "source"
        ][
            "excel_row"
        ]

        insurers = []

        for policy in policies:

            company = policy[
                "company"
            ]

            clause = policy[
                "clauses"
            ][
                idx
            ]

            insurers.append({

                "company":
                    company,

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
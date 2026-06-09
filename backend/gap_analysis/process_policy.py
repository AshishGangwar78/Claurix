import json

from backend.gap_analysis.uw_remark_classifier import (
    classify_uw_remark
)

def process_policy(
    policy_json
):

    for clause in policy_json.get(
        "clauses",
        []
    ):

        clause["remark_status"] = (
            classify_uw_remark(
                clause.get(
                    "uw_remark",
                    ""
                )
            )
        )

    return policy_json
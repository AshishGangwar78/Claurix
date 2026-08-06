"""MasterSheet schema contract used by the SQL generator."""

from backend.core.settings import get_settings


MASTERSHEET_COLUMNS = [
    ("case_id", "TEXT", "Case identifier — scope all queries to the active case when provided"),
    ("insurer", "TEXT", "Insurance company / insurer name"),
    ("policy", "TEXT", "Policy / section name"),
    ("premium", "NUMERIC", "Quoted premium amount"),
    ("clause", "TEXT", "Clause / coverage / condition text"),
    ("clause_remarks", "TEXT", "Insurer remarks on the clause"),
    ("acceptance_status", "TEXT", "AGREED | NOT_AGREED | PARTIALLY_AGREED | similar"),
    ("deviation", "TEXT", "Deviation notes from requirement"),
    ("remarks", "TEXT", "General remarks"),
    ("coverage", "TEXT", "Coverage description"),
    ("policy_metadata", "JSONB", "Additional policy metadata"),
    ("sum_insured", "NUMERIC", "Sum insured / TSI when available"),
]


def get_mastersheet_schema_prompt() -> str:
    settings = get_settings()
    table = settings.copilot_mastersheet_table
    case_col = settings.copilot_case_filter_column

    lines = [
        f"Table name: {table}",
        f"Case scope column: {case_col}",
        "",
        "Columns:",
    ]
    for name, dtype, desc in MASTERSHEET_COLUMNS:
        lines.append(f"- {name} ({dtype}): {desc}")

    lines.extend(
        [
            "",
            "Rules:",
            f"- Prefer filtering by {case_col} = :case_id when a case_id is provided in context.",
            "- Use ILIKE for fuzzy text matches on insurer, policy, clause.",
            "- Never invent columns that are not listed.",
            "- Return only SELECT queries.",
        ]
    )
    return "\n".join(lines)

"""SQL safety validation for generated queries."""

import re
from typing import Tuple


FORBIDDEN_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "MERGE",
    "GRANT",
    "REVOKE",
    "ATTACH",
    "DETACH",
    "COPY",
    "EXECUTE",
    "CALL",
    "INTO",
    "REPLACE",
]


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def normalize_sql(sql: str) -> str:
    text = (sql or "").strip()
    text = text.replace("```sql", "").replace("```", "").strip()

    # If the model returned prose + SQL, extract the first SELECT/WITH block
    upper = text.upper()
    select_idx = upper.find("SELECT")
    with_idx = upper.find("WITH")
    candidates = [i for i in (select_idx, with_idx) if i >= 0]
    if candidates:
        start = min(candidates)
        text = text[start:]

    # Drop trailing semicolon for single-statement checks (kept optional)
    if text.endswith(";"):
        text = text[:-1].strip()
    return text


def validate_select_sql(sql: str) -> Tuple[bool, str]:
    """
    Validate that SQL is a single safe SELECT statement.

    Returns (is_valid, reason).
    """
    cleaned = normalize_sql(sql)
    if not cleaned:
        return False, "SQL is empty"

    no_comments = _strip_comments(cleaned)
    compact = " ".join(no_comments.split())
    upper = compact.upper()

    # Multiple statements
    if ";" in compact:
        return False, "Multiple SQL statements are not allowed"

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        return False, "Only SELECT / WITH (CTE) queries are allowed"

    # Forbidden keywords as whole words
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            # Allow SELECT ... INTO OUTFILE style blocked by INTO above
            return False, f"Forbidden keyword detected: {keyword}"

    # Basic injection patterns
    if re.search(r";\s*(SELECT|WITH|DROP|DELETE|UPDATE|INSERT)", upper):
        return False, "Potential stacked-query injection detected"

    if re.search(r"\bpg_sleep\b|\bpg_read_file\b|\blo_import\b", upper):
        return False, "Dangerous PostgreSQL function detected"

    return True, "ok"

# Insurance Gap Analysis Backend

## Overview

This backend processes insurance proposal Excel files and extracts policy clauses, requirements, underwriting remarks, and proposal comparisons.

The system:

1. Receives proposal files through API.
2. Extracts policy blocks from Excel.
3. Detects clause rows using Qwen.
4. Identifies Clause / Requirement / UW Remark columns.
5. Builds structured JSON.
6. Classifies UW remarks as:

   * AGREED
   * NOT_AGREED
   * PARTIALLY_AGREED
7. Merges proposals from multiple insurers for comparison.

---

## Tech Stack

* FastAPI
* Pandas
* Ollama
* Qwen 2.5 7B
* Python 3.11+

---

## Start Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Ollama:

```bash
ollama serve
```

Ensure model exists:

```bash
ollama run qwen2.5:7b
```

Start API:

```bash
uvicorn backend.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

---

## Upload API

### Endpoint

```http
POST /upload/
```

### Form Data

| Field         | Type        | Required |
| ------------- | ----------- | -------- |
| user_id       | string      | Yes      |
| case_id       | string      | Yes      |
| document_type | string      | Yes      |
| policy_config | JSON string | Yes      |
| files         | Excel files | Yes      |

---

## document_type

Supported:

```json
"proposals"
```

---

## Example policy_config

```json
[
    {
        "policy": "Neon Signage",
        "sheet_name": "RFQ Package Policy",
        "start_row": 80,
        "end_row": 85
    },
    {
        "policy": "Plate Glass",
        "sheet_name": "RFQ Package Policy",
        "start_row": 86,
        "end_row": 92
    }
]
```

---

## Response

```json
{
    "status": "success",
    "user_id": "5",
    "case_id": "101",
    "document_type": "proposals",
    "policies_processed": 10,
    "files_uploaded": 2
}
```

---

## Storage Structure

```text
backend/storage/

users/
└── {user_id}/
    └── {case_id}/
        └── proposals/
            ├── uploads/
            └── results/
                ├── policies/
                └── merged/
```

---

## Individual Policy Output

Example:

```json
{
    "company": "ABC Insurance",
    "policy": "Neon Signage",
    "column_mapping": {
        "clause_column": 2,
        "requirement_column": 3,
        "uw_remark_column": 6
    },
    "clauses": [
        {
            "clause": "FAR Clause",
            "requirement": "Required",
            "uw_remark": "Covered",
            "remark_status": "AGREED",
            "source": {
                "sheet_name": "RFQ Package Policy",
                "excel_row": 82,
                "clause_cell": "B82",
                "requirement_cell": "C82",
                "uw_remark_cell": "F82"
            }
        }
    ]
}
```

---

## Merged Policy Output

Located inside:

```text
results/merged/
```

Example:

```json
{
    "policy": "Neon Signage",
    "clauses": [
        {
            "excel_row": 82,
            "clause": "FAR Clause",
            "requirement": "Required",
            "insurers": [
                {
                    "company": "ABC Insurance",
                    "uw_remark": "Covered",
                    "remark_status": "AGREED"
                },
                {
                    "company": "XYZ Insurance",
                    "uw_remark": "Not Agreed",
                    "remark_status": "NOT_AGREED"
                }
            ]
        }
    ]
}
```

---

## Notes For Frontend

Frontend should primarily consume:

```text
results/merged/
```

These files contain side-by-side insurer comparisons and are intended for UI rendering.

The `source` object should be preserved because it provides traceability back to the original Excel sheet and cell locations.

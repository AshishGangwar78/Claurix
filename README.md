# Insurance Gap Analysis Backend

Production-ready FastAPI backend for insurance proposal gap analysis. Upload insurer proposal Excel files, extract policy clauses with a local LLM (Ollama / Qwen), classify underwriting remarks, and merge multi-insurer results for comparison.

## Features

- Upload RFQ or proposal documents via a multipart API
- Extract policy row blocks from Excel by sheet and row range
- Detect clause rows and map Clause / Requirement / UW Remark columns with Qwen
- Classify UW remarks as `AGREED`, `NOT_AGREED`, or `PARTIALLY_AGREED`
- Merge multiple insurer proposals into a side-by-side comparison
- Export merged results to JSON and Excel
- Clean layered architecture ready for PostgreSQL, auth, and background workers

## Tech Stack

| Layer | Technology |
| --- | --- |
| API | FastAPI, Uvicorn |
| Data | Pandas, OpenPyXL |
| PDF (available) | pdfplumber |
| LLM | Ollama + Qwen 2.5 7B |
| Language | Python 3.11+ |

## Folder Structure

```text
backend/
├── api/                      # FastAPI routers / endpoints only
├── services/
│   ├── llm_service.py        # All LLM (Ollama) interactions
│   ├── file_service.py       # Upload, paths, Excel/PDF helpers
│   ├── analysis_service.py   # Upload orchestration workflow
│   ├── gap_analyzer.py       # UW classification, merge, Excel export
│   └── clause_extraction/    # Clause pipeline (modules 1–4)
├── repositories/             # Placeholders for future PostgreSQL
├── schemas/                  # Request/response schema models
├── models/                   # Domain model placeholders
├── utils/                    # Shared helpers
├── core/                     # App config (storage path, etc.)
├── storage/                  # Uploads and generated results
├── extraction/               # Compatibility re-exports
├── llm/                      # Compatibility re-exports
├── gap_analysis/             # Compatibility re-exports
└── main.py                   # Application entrypoint
```

Compatibility packages (`extraction/`, `llm/`, `gap_analysis/`) re-export the same public functions so existing integrations keep working.

## Prerequisites

1. **Python 3.11+** (3.12–3.14 also work with current wheels)
2. **Ollama** installed and running locally
3. **Qwen model** pulled:

```bash
ollama serve
ollama pull qwen2.5:7b
```

## Installation

Clone the repository:

```bash
git clone <your-repo-url>
cd Insurance_Gap_Analysis
```

### Virtual environment (Windows)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Virtual environment (Linux / macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

A `.env` file is **not required** for the current release. Defaults are used for storage and the local Ollama client.

Optional template:

```bash
cp .env.example .env
```

Future configuration keys (documented in `.env.example`):

| Variable | Purpose | Required today |
| --- | --- | --- |
| `OLLAMA_HOST` | Ollama server URL | No |
| `STORAGE_DIR` | Override storage root | No |
| `LOG_LEVEL` | Logging verbosity | No |

## Running the Application

From the project root (with the virtual environment activated):

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API base URL:

```text
http://127.0.0.1:8000
```

## API Documentation (Swagger)

Interactive docs (recommended):

```text
http://127.0.0.1:8000/docs
```

Alternative ReDoc UI:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

## Endpoints

### `GET /`

Health / status check.

**Response**

```json
{
  "message": "Insurance Gap Analysis API Running"
}
```

### `POST /upload/`

Upload RFQ or proposal files and process policies.

#### Form fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `user_id` | string | Yes | Tenant / user identifier |
| `case_id` | string | Yes | Case identifier |
| `document_type` | string | Yes | `rfq` or `proposals` |
| `policy_config` | JSON string | For proposals | Policy sheet/row ranges |
| `files` | file(s) | Yes | Excel proposal files |

#### Example `policy_config`

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

#### Success response

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

## Storage Layout

Generated at runtime under `backend/storage/`:

```text
backend/storage/users/{user_id}/{case_id}/{document_type}/
├── uploads/
└── results/
    ├── policies/{company}/{policy}.json
    └── merged/{policy}.json
    └── merged/{policy}.xlsx
```

User uploads and results are gitignored. An empty `backend/storage/` directory is kept in the repository.

## Processing Flow

1. API receives upload request
2. Files are stored under the user/case path
3. For `proposals`, each configured policy block is extracted from Excel
4. Clause rows are detected and columns are mapped via Qwen
5. Structured policy JSON is built and UW remarks are classified
6. When multiple insurers exist for the same policy, results are merged and exported to Excel

## Notes for Frontend Integrations

Prefer consuming merged outputs:

```text
results/merged/
```

Preserve the `source` object on clauses for Excel cell traceability.

Existing Python imports such as the following remain supported:

```python
from backend.llm.policy_clause_extractor import extract_policy_clauses
from backend.gap_analysis.process_policy import process_policy
from backend.gap_analysis.policy_merger import merge_policy_files, json_to_excel
from backend.extraction.policy_block_extractor import extract_policy_block
```

## Extensibility

The codebase is structured for incremental production features:

- **PostgreSQL** — implement `repositories/` interfaces and swap filesystem persistence
- **Authentication** — add middleware / dependencies in `api/` without changing service logic
- **Background workers** — move long-running proposal processing from the request path into a queue consumer that calls the same services
- **Config** — promote settings from `core/config.py` and optional `.env` values

## License

Proprietary / internal use unless otherwise specified by the repository owner.

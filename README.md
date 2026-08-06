# Claurix — Insurance Gap Analysis Backend

Production-ready **FastAPI** backend for insurance proposal gap analysis, premium extraction, and an **AI Copilot** that answers natural-language questions from the PostgreSQL **MasterSheet**.

This README is written for backend and **frontend** engineers integrating with the API.

---

## Features

### Document / gap analysis
- Upload RFQ or proposal Excel files
- Extract policy blocks by sheet + row range
- Detect clause rows (rule-based prefilter + Qwen LLM)
- Map Clause / Requirement / UW Remark columns
- Classify UW remarks: `AGREED` | `NOT_AGREED` | `PARTIALLY_AGREED`
- Merge multi-insurer proposals and export JSON + Excel

### Premium calculation
- Extract **Total Sum Insured** and **Premium** from policy blocks
- Hybrid label detection (keywords + embeddings)
- Nearby numeric value search with confidence scores

### AI Copilot (LangGraph V1)
- Natural language → safe `SELECT` SQL → MasterSheet → business answer
- Case-scoped queries via `case_id`
- Short-term conversation memory (follow-ups)
- Debug mode for SQL / planner inspection (never enable in production UI by default)

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| API | FastAPI, Uvicorn |
| Data | Pandas, OpenPyXL, pdfplumber |
| LLM | Ollama + Qwen 2.5 7B |
| Copilot orchestration | LangGraph |
| Database | PostgreSQL via SQLAlchemy (optional until configured) |
| Language | Python 3.11+ |

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/AshishGangwar78/Claurix.git
cd Claurix
```

### 2. Virtual environment

**Windows (PowerShell)**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Ollama (required for LLM features)

```bash
ollama serve
ollama pull qwen2.5:7b
```

### 4. Environment

```bash
cp .env.example .env
```

Minimum for Copilot SQL execution:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
```

Optional MasterSheet DDL: `backend/copilot/schema/mastersheet.sql`

### 5. Run API

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

| Resource | URL |
| --- | --- |
| API root | http://127.0.0.1:8000/ |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

---

## Folder Structure

```text
backend/
├── api/                         # Shared routers + deps (auth placeholder)
├── copilot/                     # LangGraph AI Copilot module
│   ├── graph/                   # state, nodes, routing, builder
│   ├── tools/                   # SQL tool + tool registry
│   ├── prompts/                 # planner / sql / answer markdown prompts
│   ├── services/                # CopilotService + conversation memory
│   ├── routers/                 # /api/copilot/*
│   ├── schemas/                 # Copilot request/response models
│   └── schema/                  # MasterSheet contract + DDL
├── services/                    # Upload, clause extraction, gap, premium
├── repositories/                # Future PostgreSQL repositories
├── schemas/                     # Upload / premium API schemas
├── models/                      # Domain models
├── core/                        # settings, logging, database, config
├── storage/                     # Runtime uploads/results (gitignored)
└── main.py                      # FastAPI entrypoint
```

---

## Frontend Integration Guide

Base URL (local):

```text
http://127.0.0.1:8000
```

All JSON endpoints accept `Content-Type: application/json` unless noted.
Upload uses `multipart/form-data`.

Suggested frontend flow for Copilot:

1. User opens a **Case** in the UI.
2. Frontend keeps `case_id` (and optionally `conversation_id`) in client state.
3. Each chat message calls `POST /api/copilot/chat` or `/api/copilot/chat/stream` with that `case_id`.
4. Store returned `conversation_id` / `message_id` and reuse `conversation_id` on follow-ups.
5. Render `response.content` (markdown) and separately render `artifacts` (e.g. tables).
6. Keep `debug: false` in production UI — never show SQL to end users.

---

## API Reference

### 1) Health

`GET /`

```json
{ "message": "Insurance Gap Analysis API Running" }
```

---

### 2) Upload proposals / RFQ

`POST /upload/`  
`Content-Type: multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `user_id` | string | Yes | User / tenant id |
| `case_id` | string | Yes | Active case id |
| `document_type` | string | Yes | `rfq` or `proposals` |
| `policy_config` | JSON string | For proposals | Policy sheet/row ranges |
| `files` | file(s) | Yes | Excel files |

Example `policy_config`:

```json
[
  {
    "policy": "Neon Signage",
    "sheet_name": "RFQ Package Policy",
    "start_row": 80,
    "end_row": 85
  }
]
```

Success response:

```json
{
  "status": "success",
  "user_id": "5",
  "case_id": "101",
  "document_type": "proposals",
  "policies_processed": 1,
  "files_uploaded": 2
}
```

Storage layout:

```text
backend/storage/users/{user_id}/{case_id}/{document_type}/
├── uploads/
└── results/
    ├── policies/{company}/{policy}.json
    └── merged/{policy}.json
    └── merged/{policy}.xlsx
```

Frontend should primarily consume **merged** results for comparison UI.

---

### 3) Premium extraction

`POST /premium/extract/`

Request (grid example):

```json
{
  "blocks": [
    {
      "policy_name": "Neon Signage",
      "sheet_name": "RFQ Package Policy",
      "start_row": 80,
      "start_col": 1,
      "grid": [
        ["Total Sum Insured", "Rs. 12,50,000"],
        ["Premium", "25,000"]
      ]
    }
  ]
}
```

Response (shape):

```json
{
  "status": "success",
  "results": [
    {
      "policy_name": "Neon Signage",
      "total_sum_insured": {
        "value": 1250000.0,
        "label_cell": "A81",
        "value_cell": "B81",
        "confidence": 0.93
      },
      "premium": {
        "value": 25000.0,
        "label_cell": "A82",
        "value_cell": "B82",
        "confidence": 0.77
      }
    }
  ]
}
```

---

### 4) AI Copilot chat ⭐ (frontend primary)

LangGraph internals are **never** exposed. Both sync and stream endpoints share the same request body and the same final envelope.

#### Endpoints

| Method | Path | Content-Type | Description |
| --- | --- | --- | --- |
| `POST` | `/api/copilot/chat` | `application/json` | Synchronous envelope response |
| `POST` | `/api/copilot/chat/stream` | request JSON → response `text/event-stream` | SSE progress + final envelope |

#### Headers (optional)

| Header | Description |
| --- | --- |
| `Authorization: Bearer <token>` | Required only when `AUTH_ENABLED=true` |
| `X-Case-Id: <case_id>` | Alternate case scope (body `case_id` also works) |

#### Request body (both endpoints)

```json
{
  "message": "Which insurer quoted the lowest premium?",
  "conversation_id": null,
  "case_id": "101",
  "debug": false
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `message` | string | Yes | User question |
| `conversation_id` | string \| null | No | Omit/null on first turn; reuse for follow-ups |
| `case_id` | string \| null | Recommended | Scopes MasterSheet SQL to the active case |
| `debug` | boolean | No | Default `false`. Debug fields only under `metadata.debug` |

#### Standard response envelope

```json
{
  "success": true,
  "conversation_id": "8f2c9e2a-....",
  "message_id": "msg_01HXYZ",
  "response": {
    "type": "markdown",
    "content": "**Tata AIG** quoted the lowest premium at **18500**."
  },
  "artifacts": [
    {
      "id": "art_table_1",
      "type": "table",
      "title": "MasterSheet results",
      "data": {
        "columns": ["insurer", "lowest_premium"],
        "rows": [
          {"insurer": "Tata AIG", "lowest_premium": 18500},
          {"insurer": "ICICI Lombard", "lowest_premium": 22000}
        ]
      },
      "schema_version": "1.0"
    }
  ],
  "suggestions": [
    {"label": "Compare insurers", "message": "Compare the top two insurer premiums"}
  ],
  "metadata": {
    "intent": "premium_analysis",
    "execution_time": 1.84,
    "rows_returned": 3,
    "retries": 0,
    "case_id": "101",
    "tools_used": ["sql_mastersheet"],
    "debug": null
  },
  "error": null
}
```

##### Response fields

| Field | Description |
| --- | --- |
| `success` | `true` on soft success (including empty results); `false` on structured errors |
| `conversation_id` | Persist and resend for follow-ups |
| `message_id` | Unique id for this assistant message |
| `response.type` | `text` \| `markdown` \| `table` \| `chart` |
| `response.content` | Primary user-visible content |
| `artifacts[]` | Structured tool outputs (render separately from text) |
| `suggestions[]` | Optional follow-up chips (`label` + prefills `message`) |
| `metadata` | Intent, timing, rows, tools — safe for UI telemetry |
| `error` | Present only when `success=false` |

##### Artifact types (extensible)

| `type` | `data` shape (V1) | Notes |
| --- | --- | --- |
| `table` | `{ columns: string[], rows: object[] }` | Produced by SQL tool today |
| `chart` | chart spec object | Reserved for analytics tools |
| `markdown` | string or `{ markdown: string }` | Secondary markdown blocks |
| `json` | arbitrary JSON | Raw structured payloads |
| `file` | `{ url, filename, mime }` | Future exports/downloads |

Future LangGraph tools should **only add artifacts** — do not invent new top-level response keys.

##### Debug mode (`debug: true`)

Debug details are nested (never top-level SQL leakage):

```json
{
  "metadata": {
    "debug": {
      "planner_output": { "intent": "premium_analysis", "..." : "..." },
      "generated_sql": "SELECT ...",
      "execution_time": 1.84,
      "retry_count": 0
    }
  }
}
```

Use only in admin/internal tooling.

##### Structured errors (`success: false`)

```json
{
  "success": false,
  "conversation_id": "...",
  "message_id": "...",
  "response": { "type": "text", "content": "I couldn't retrieve MasterSheet data right now." },
  "artifacts": [],
  "suggestions": [],
  "metadata": { "execution_time": 0.12, "rows_returned": 0, "retries": 0 },
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "I couldn't retrieve MasterSheet data right now.",
    "details": null
  }
}
```

Error codes:

| Code | Meaning |
| --- | --- |
| `VALIDATION_ERROR` | Bad request payload |
| `UNAUTHORIZED` | Auth required / invalid |
| `UNSUPPORTED_QUERY` | Outside MasterSheet scope |
| `SQL_GENERATION_FAILED` | Could not produce safe SQL |
| `SQL_EXECUTION_FAILED` | Query failed at runtime |
| `DATABASE_UNAVAILABLE` | `DATABASE_URL` missing / DB down |
| `EMPTY_RESULT` | Reserved (empty results are usually soft-success) |
| `LLM_TIMEOUT` | Model timeout |
| `INTERNAL_ERROR` | Unexpected failure |

No stack traces are returned to the client.

#### SSE streaming — `POST /api/copilot/chat/stream`

Each SSE message:

```text
event: planning
data: {"event":"planning","conversation_id":"...","message_id":"...","data":{"status":"started"}}
```

Event types:

| Event | When | `data` highlights |
| --- | --- | --- |
| `planning` | Planner start/complete | `status`, optional `intent` |
| `tool_call` | Tool about to run | `tool`, `status` |
| `tool_result` | Tool finished | `tool`, `rows_returned` |
| `answer_chunk` | Answer text chunk | `index`, `content` |
| `error` | Structured failure | `code`, `message` |
| `completed` | Always last | `envelope` = full sync response |

Frontend should:

1. Open EventSource/fetch stream to `/api/copilot/chat/stream`
2. Show planning/tool progress from events
3. Append `answer_chunk` content to the chat bubble
4. On `completed`, replace/reconcile with `data.envelope` (source of truth)

#### Frontend TypeScript types (suggested)

```ts
export type ResponseContentType = "text" | "markdown" | "table" | "chart";
export type ArtifactType = "table" | "chart" | "markdown" | "json" | "file";
export type StreamEventType =
  | "planning"
  | "tool_call"
  | "tool_result"
  | "answer_chunk"
  | "completed"
  | "error";

export type CopilotChatRequest = {
  message: string;
  conversation_id?: string | null;
  case_id?: string | null;
  debug?: boolean;
};

export type Artifact = {
  id: string;
  type: ArtifactType;
  title?: string | null;
  data: unknown;
  schema_version?: string;
};

export type CopilotChatResponse = {
  success: boolean;
  conversation_id: string;
  message_id: string;
  response: { type: ResponseContentType; content: unknown } | null;
  artifacts: Artifact[];
  suggestions: { label: string; message: string }[];
  metadata: {
    intent?: string | null;
    execution_time: number;
    rows_returned: number;
    retries: number;
    case_id?: string | null;
    tools_used: string[];
    debug?: {
      planner_output?: Record<string, unknown> | null;
      generated_sql?: string | null;
      execution_time?: number | null;
      retry_count?: number | null;
    } | null;
  };
  error?: { code: string; message: string; details?: Record<string, unknown> | null } | null;
};
```

#### Example `fetch` (sync)

```ts
async function askCopilot(message: string, caseId: string, conversationId?: string) {
  const res = await fetch("http://127.0.0.1:8000/api/copilot/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Case-Id": caseId,
    },
    body: JSON.stringify({
      message,
      case_id: caseId,
      conversation_id: conversationId ?? null,
      debug: false,
    }),
  });
  const body = (await res.json()) as CopilotChatResponse;
  if (!body.success) {
    // handle body.error.code
  }
  return body;
}
```

#### Example questions the Copilot supports

Premium
- Which insurer quoted the lowest premium?
- Show the top 10 highest premiums.
- Compare Tata AIG and ICICI Lombard premiums.
- Average premium by insurer.

Clause
- What did ICICI mention about the Terrorism clause?
- Show remarks for Flood clause.
- Which insurers accepted Waiver of Subrogation?
- Which insurer rejected Cyber clause?

Analytics
- Which insurer accepted the maximum clauses?
- Which insurer has the fewest deviations?
- Which insurer has the highest acceptance rate?

#### UX notes for frontend
- Prefer `/chat/stream` for progressive UI; fall back to `/chat` if needed.
- Render `response.content` as markdown when `type` is `markdown`/`text`.
- Render `artifacts` of type `table` as data grids.
- Keep `conversation_id` per chat panel / case session.
- Always send the active `case_id`.
- Treat `"No matching data found."` as an empty-state (still `success: true`).
- Never show SQL / planner output to end users (`debug` stays off).

---

## Copilot Architecture (backend)

```text
START
  → Planner
  → SQL Generator
  → SQL Validator  ←── retry (max 3) if invalid
  → SQL Executor   (via SQL tool only)
  → Answer Generator
END
```

- Prompts live in `backend/copilot/prompts/*.md` (not hardcoded in nodes).
- Graph never talks to PostgreSQL directly — uses `execute_sql()`.
- Tool registry supports future tools (policy search, gap analysis, docs, recommendations) without redesign.
- Conversation memory is in-process for V1; replaceable with Redis later.

### MasterSheet columns (expected)

`case_id`, `insurer`, `policy`, `premium`, `clause`, `clause_remarks`, `acceptance_status`, `deviation`, `remarks`, `coverage`, `policy_metadata`, `sum_insured`

---

## Auth

- Default: `AUTH_ENABLED=false` (open local/dev access, same as existing upload APIs).
- When enabled, send `Authorization: Bearer <token>`.
- Hook real JWT verification in `backend/api/deps.py` when platform auth is ready.

---

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | For Copilot SQL | SQLAlchemy URL, e.g. `postgresql+psycopg2://...` |
| `OLLAMA_HOST` | No | Default `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | No | Default `qwen2.5:7b` |
| `STORAGE_DIR` | No | Default `backend/storage` |
| `LOG_LEVEL` | No | Default `INFO` |
| `COPILOT_MAX_SQL_RETRIES` | No | Default `3` |
| `COPILOT_MEMORY_TURNS` | No | Default `6` |
| `COPILOT_MASTERSHEET_TABLE` | No | Default `mastersheet` |
| `AUTH_ENABLED` | No | Default `false` |

---

## CORS (frontend local dev)

If the UI runs on another origin (e.g. `http://localhost:3000`), add CORS in `backend/main.py` or ask backend to enable it. Until then, use a Next.js/Vite proxy or same-origin gateway.

Example (backend change, if needed):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Verified Copilot behaviour (sample)

With MasterSheet-like sample data and case `101`, the chat pipeline successfully:

| Question type | Result |
| --- | --- |
| Lowest premium | Returns ranked insurer premiums |
| Compare Tata AIG vs ICICI | Returns both premiums |
| Terrorism / Flood remarks | Returns clause remarks + status |
| Waiver accepted | Returns accepting insurers |
| Cyber rejected | Returns rejecting insurer(s) |
| Max accepted clauses | Returns acceptance counts |
| Follow-up + same `conversation_id` | Memory retained |
| `debug: false` | SQL hidden from response |

Without `DATABASE_URL`, Copilot still plans/generates SQL but returns a friendly DB-unavailable message instead of crashing.

---

## Extensibility roadmap

Designed so new tools only require:
1. New tool implementation
2. Registry entry
3. Planner routing update

Planned tools: Policy Search, Gap Analysis, Document Search, Proposal Comparison, Recommendations, Report Generation.

---

## License

Proprietary / internal use unless otherwise specified by the repository owner.

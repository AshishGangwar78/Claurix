-- Optional DDL for the Copilot MasterSheet (PostgreSQL).
-- Align COPILOT_MASTERSHEET_TABLE with this table name.

CREATE TABLE IF NOT EXISTS mastersheet (
    id              BIGSERIAL PRIMARY KEY,
    case_id         TEXT,
    insurer         TEXT,
    policy          TEXT,
    premium         NUMERIC,
    clause          TEXT,
    clause_remarks  TEXT,
    acceptance_status TEXT,
    deviation       TEXT,
    remarks         TEXT,
    coverage        TEXT,
    policy_metadata JSONB,
    sum_insured     NUMERIC,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mastersheet_case_id ON mastersheet (case_id);
CREATE INDEX IF NOT EXISTS idx_mastersheet_insurer ON mastersheet (insurer);
CREATE INDEX IF NOT EXISTS idx_mastersheet_policy ON mastersheet (policy);

CREATE TABLE IF NOT EXISTS omega_runs (
    run_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor TEXT NOT NULL,
    domain_type TEXT NOT NULL,
    input_payload JSONB NOT NULL,
    summary_payload JSONB NOT NULL,
    branch_count INTEGER NOT NULL,
    horizon INTEGER NOT NULL,
    status TEXT NOT NULL,
    receipt_hash TEXT NOT NULL,
    chain_verified BOOLEAN NOT NULL DEFAULT FALSE,
    provisional BOOLEAN NOT NULL DEFAULT TRUE,
    canon_version INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_omega_runs_created_at ON omega_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_omega_runs_domain_type ON omega_runs(domain_type);

CREATE TABLE IF NOT EXISTS omega_branches (
    branch_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES omega_runs(run_id) ON DELETE CASCADE,
    branch_index INTEGER NOT NULL,
    assumptions JSONB NOT NULL,
    transitions JSONB NOT NULL,
    outputs JSONB NOT NULL,
    likelihood DOUBLE PRECISION NOT NULL,
    confidence_payload JSONB NOT NULL,
    breach_points JSONB NOT NULL,
    divergence_components JSONB NOT NULL,
    realized_status TEXT NOT NULL DEFAULT 'simulated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omega_branches_run_id ON omega_branches(run_id, branch_index);

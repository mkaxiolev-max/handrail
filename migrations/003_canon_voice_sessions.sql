-- canon_commits: versioned, signed policy authority
CREATE TABLE IF NOT EXISTS canon_commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INTEGER NOT NULL UNIQUE,
    policy_hash TEXT NOT NULL,
    policy_content JSONB NOT NULL,
    signed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    signature TEXT NOT NULL,
    supersedes_version INTEGER,
    CONSTRAINT fk_supersedes FOREIGN KEY (supersedes_version) REFERENCES canon_commits(version)
);

CREATE INDEX IF NOT EXISTS idx_canon_commits_version ON canon_commits(version DESC);

-- voice_sessions: call state, linked to atoms
CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL UNIQUE,
    phone TEXT,
    initiator TEXT,
    state TEXT NOT NULL DEFAULT 'idle',
    transcript JSONB,
    memory_atom_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_state ON voice_sessions(state);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_created ON voice_sessions(created_at DESC);

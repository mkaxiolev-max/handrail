-- Boot state
CREATE TABLE IF NOT EXISTS bindings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Source discovery
CREATE TABLE IF NOT EXISTS source_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  path TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL,
  size_bytes BIGINT,
  ingest_status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Parse bundles
CREATE TABLE IF NOT EXISTS parse_bundles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_item_id UUID REFERENCES source_items(id),
  parser_type TEXT,
  structure_json JSONB,
  text_content TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Story Atoms
CREATE TABLE IF NOT EXISTS atoms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL,
  content TEXT,
  source_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Graph edges
CREATE TABLE IF NOT EXISTS edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_id UUID REFERENCES atoms(id),
  to_id UUID REFERENCES atoms(id),
  type TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Feed
CREATE TABLE IF NOT EXISTS feed_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Models
CREATE TABLE IF NOT EXISTS models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  provider TEXT,
  locality TEXT,
  enabled BOOLEAN DEFAULT true
);

-- Model routes
CREATE TABLE IF NOT EXISTS model_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_kind TEXT NOT NULL,
  preferred_model_id UUID REFERENCES models(id),
  fallback_model_id UUID REFERENCES models(id)
);

-- UI sessions
CREATE TABLE IF NOT EXISTS ui_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at TIMESTAMP DEFAULT NOW(),
  status TEXT
);

-- Receipts
CREATE TABLE IF NOT EXISTS receipts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event TEXT NOT NULL,
  payload JSONB,
  hash TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

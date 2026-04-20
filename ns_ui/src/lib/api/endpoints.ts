import { NS_API, NS_URL, HANDRAIL_URL } from '../runtime/env'

export const EP = {
  // UI aggregation (ns_api :9011)
  ui: {
    summary:      () => `${NS_API}/api/v1/ui/summary`,
    voice:        () => `${NS_API}/api/v1/ui/voice`,
    timeline:     () => `${NS_API}/api/v1/ui/timeline`,
    execution:    () => `${NS_API}/api/v1/ui/execution`,
    build:        () => `${NS_API}/api/v1/ui/build`,
    memory:       () => `${NS_API}/api/v1/ui/memory`,
    architecture: () => `${NS_API}/api/v1/ui/architecture`,
    governance:   () => `${NS_API}/api/v1/ui/governance`,
  },

  // System / runtime (ns_api :9011)
  system: {
    state:    () => `${NS_API}/api/v1/system/state`,
    timeline: () => `${NS_API}/api/v1/system/timeline`,
  },
  engine: {
    live:    () => `${NS_API}/api/v1/engine/live`,
    liveSSE: () => `${NS_API}/api/v1/engine/live/stream`,
  },
  programs:   () => `${NS_API}/api/v1/programs`,
  governance: () => `${NS_API}/api/v1/governance/state`,
  memory: {
    receipts: () => `${NS_API}/api/v1/memory/receipts`,
  },
  omega: {
    healthz: () => `${NS_API}/api/v1/omega/healthz`,
    runs:    () => `${NS_API}/api/v1/omega/runs`,
    run:     (id: string) => `${NS_API}/api/v1/omega/runs/${id}`,
  },

  // NS Core direct (ns_core :9000)
  violet: {
    identity: () => `${NS_URL}/violet/identity`,
    isr:      () => `${NS_URL}/violet/isr`,
    chat:     () => `${NS_URL}/violet/chat`,
    status:   () => `${NS_URL}/violet/status`,
  },
  intent: {
    execute: () => `${NS_URL}/intent/execute`,
  },
  organism: {
    overview: () => `${NS_URL}/api/organism/overview`,
  },
  capability: {
    graph:  () => `${NS_URL}/capability/graph`,
    update: () => `${NS_URL}/capability/update`,
  },

  // Handrail (:8011)
  handrail: {
    healthz: () => `${HANDRAIL_URL}/healthz`,
    cps:     () => `${HANDRAIL_URL}/ops/cps`,
  },
} as const

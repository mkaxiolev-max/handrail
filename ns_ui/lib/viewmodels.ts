/**
 * Founder-native objects — the semantic layer between raw API data and UI surfaces.
 * These are not decorative abstractions; they are what turns NS∞ into a founder environment.
 */

export type SupportClass =
  | 'observation'
  | 'interpretation'
  | 'hypothesis'
  | 'proposal'
  | 'canon'
  | 'receipt'
  | 'program'
  | 'challenge'

export type Urgency = 'critical' | 'high' | 'normal' | 'low'

export interface FounderArc {
  id: string
  label: string
  phase: 'ideation' | 'structuring' | 'execution' | 'receipted' | 'canonized'
  open_loops: OpenLoop[]
  reality_deltas: RealityDelta[]
  ts_started: string
  ts_updated: string
}

export interface ThresholdRequest {
  id: string
  op: string
  risk_tier: 'R0' | 'R1' | 'R2' | 'R3' | 'R4'
  label: string
  requires_yubikey: boolean
  payload: Record<string, unknown>
  ts: string
  status: 'pending' | 'approved' | 'denied' | 'expired'
}

export interface OpenLoop {
  id: string
  kind: 'OpenLoop'
  label: string
  source_class: SupportClass
  urgency: Urgency
  ts?: string
  resolution?: string
}

export interface RealityDelta {
  id: string
  kind: 'RealityDelta'
  label: string
  event_type: string
  op?: string
  ts: string
  receipt_id?: string
  source_class: SupportClass
  causal_delta?: string
}

export interface OrganismHealth {
  ns_core:   { ok: boolean; shalom: boolean }
  handrail:  { ok: boolean }
  continuum: { ok: boolean; tier?: number | null }
  omega:     { ok: boolean }
  alexandria_mounted: boolean
}

export interface FounderSummary {
  ts: string
  priorities: Array<{ rank: number; label: string; urgency: Urgency }>
  open_loops: OpenLoop[]
  reality_deltas: RealityDelta[]
  organism_health: OrganismHealth
  governance_alerts: Array<{ label: string; severity: string }>
  receipt_count: number
}

export function isStale(ts: string | undefined, maxAgeMs = 30_000): boolean {
  if (!ts) return true
  return Date.now() - new Date(ts).getTime() > maxAgeMs
}

export function healthColor(ok: boolean): string {
  return ok ? '#00FF88' : '#FF3333'
}

export function urgencyColor(u: Urgency): string {
  switch (u) {
    case 'critical': return '#FF3333'
    case 'high':     return '#FFAA00'
    case 'normal':   return '#00D4FF'
    case 'low':      return '#88CCFF'
  }
}

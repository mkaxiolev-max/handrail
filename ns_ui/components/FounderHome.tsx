'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import type { FounderSummary, OpenLoop, RealityDelta } from '@/lib/viewmodels'
import { isStale, urgencyColor, healthColor } from '@/lib/viewmodels'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

function StaleBadge() {
  return (
    <span style={{
      fontSize: 8, padding: '1px 5px',
      background: 'rgba(255,170,0,0.15)', border: '1px solid rgba(255,170,0,0.4)',
      borderRadius: 3, color: '#FFAA00', fontFamily: 'monospace',
    }}>STALE</span>
  )
}

function HealthDot({ ok }: { ok: boolean }) {
  return <span style={{ color: healthColor(ok), fontSize: 10 }}>{ok ? '●' : '○'}</span>
}

function PriorityCard({ rank, label, urgency }: { rank: number; label: string; urgency: string }) {
  const c = urgencyColor(urgency as any)
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px',
      background: `${c}08`, border: `1px solid ${c}33`, borderRadius: 6, marginBottom: 6,
    }}>
      <span style={{ fontSize: 10, color: c, fontWeight: 700, minWidth: 16 }}>#{rank}</span>
      <span style={{ fontSize: 11, color: tokens.colors.textPrimary, lineHeight: 1.4 }}>{label}</span>
      <span style={{
        marginLeft: 'auto', fontSize: 8, padding: '1px 5px',
        background: `${c}22`, border: `1px solid ${c}44`, borderRadius: 3, color: c,
        textTransform: 'uppercase', flexShrink: 0,
      }}>{urgency}</span>
    </div>
  )
}

function OpenLoopRow({ loop }: { loop: OpenLoop }) {
  const c = urgencyColor(loop.urgency)
  return (
    <div style={{
      display: 'flex', gap: 8, padding: '5px 10px',
      borderBottom: `1px solid ${tokens.colors.border}`,
      alignItems: 'center',
    }}>
      <span style={{ fontSize: 8, color: '#88CCFF', minWidth: 28, fontFamily: 'monospace' }}>LOOP</span>
      <span style={{ fontSize: 10, color: tokens.colors.textPrimary, flex: 1 }}>{loop.label}</span>
      <span style={{ fontSize: 8, color: tokens.colors.textSecondary }}>{loop.source_class}</span>
      <span style={{ fontSize: 8, color: c, minWidth: 40, textAlign: 'right' }}>{loop.urgency}</span>
    </div>
  )
}

function DeltaRow({ delta }: { delta: RealityDelta }) {
  const ts = delta.ts ? new Date(delta.ts).toLocaleTimeString('en-US', { hour12: false }) : '—'
  return (
    <div style={{
      display: 'flex', gap: 8, padding: '5px 10px',
      borderBottom: `1px solid ${tokens.colors.border}`,
      alignItems: 'center',
    }}>
      <span style={{ fontSize: 8, color: tokens.colors.adjudication, minWidth: 28, fontFamily: 'monospace' }}>Δ</span>
      <span style={{ fontSize: 10, color: tokens.colors.textPrimary, flex: 1 }}>{delta.label}</span>
      <span style={{ fontSize: 8, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>{ts}</span>
    </div>
  )
}

export function FounderHome() {
  const [summary, setSummary] = useState<FounderSummary | null>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/summary`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setSummary(d)
      setFetchTs(new Date().toISOString())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    }
  }

  useEffect(() => { load(); const id = setInterval(load, 8000); return () => clearInterval(id) }, [])

  const stale = isStale(fetchTs ?? undefined, 20_000)
  const health = summary?.organism_health

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: 'auto auto auto', gap: 12 }}>

      {/* Header row: organism health */}
      <div style={{
        gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 16,
        padding: '8px 14px', background: '#080C1E', borderRadius: 8,
        border: `1px solid ${tokens.colors.border}`,
      }}>
        <span style={{ fontSize: 11, color: tokens.colors.founder, fontWeight: 700 }}>ORGANISM</span>
        {stale && <StaleBadge />}
        {health ? (
          <>
            <span style={{ fontSize: 10, color: tokens.colors.textSecondary, display: 'flex', alignItems: 'center', gap: 4 }}>
              <HealthDot ok={health.ns_core.ok} /> NS Core
              {health.ns_core.shalom && <span style={{ fontSize: 8, color: tokens.colors.healthy, marginLeft: 2 }}>✓ Shalom</span>}
            </span>
            <span style={{ fontSize: 10, color: tokens.colors.textSecondary, display: 'flex', alignItems: 'center', gap: 4 }}>
              <HealthDot ok={health.handrail.ok} /> Handrail
            </span>
            <span style={{ fontSize: 10, color: tokens.colors.textSecondary, display: 'flex', alignItems: 'center', gap: 4 }}>
              <HealthDot ok={health.continuum.ok} /> Continuum
              {health.continuum.tier != null && health.continuum.tier > 0 &&
                <span style={{ fontSize: 8, color: '#FFAA00', marginLeft: 2 }}>tier={health.continuum.tier}</span>}
            </span>
            <span style={{ fontSize: 10, color: tokens.colors.textSecondary, display: 'flex', alignItems: 'center', gap: 4 }}>
              <HealthDot ok={health.alexandria_mounted} /> Alexandria
            </span>
          </>
        ) : error ? (
          <span style={{ fontSize: 10, color: tokens.colors.error }}>API unreachable: {error}</span>
        ) : (
          <span style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>connecting...</span>
        )}
        {summary && (
          <span style={{ marginLeft: 'auto', fontSize: 9, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>
            {summary.receipt_count} receipts
          </span>
        )}
      </div>

      {/* Top priorities */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.founder}33`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.founder, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          TOP PRIORITIES
        </div>
        {summary?.priorities.length ? (
          summary.priorities.slice(0, 3).map(p => (
            <PriorityCard key={p.rank} rank={p.rank} label={p.label} urgency={p.urgency} />
          ))
        ) : (
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>
            {error ? 'Cannot reach API' : 'Loading…'}
          </div>
        )}
        {summary?.governance_alerts.map((a, i) => (
          <div key={i} style={{
            fontSize: 9, padding: '4px 8px',
            background: 'rgba(255,170,0,0.08)', border: '1px solid rgba(255,170,0,0.2)',
            borderRadius: 4, color: '#FFAA00', marginTop: 4,
          }}>{a.label}</div>
        ))}
      </div>

      {/* Reality deltas */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.adjudication}33`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.adjudication, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          RECENT CHANGES
        </div>
        {summary?.reality_deltas.length ? (
          summary.reality_deltas.slice(0, 5).map(d => (
            <DeltaRow key={d.id} delta={d} />
          ))
        ) : (
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>
            {error ? 'Cannot reach API' : 'No receipts yet'}
          </div>
        )}
      </div>

      {/* Open loops */}
      <div style={{ gridColumn: '1 / -1', background: '#0D1533', border: `1px solid ${tokens.colors.textSecondary}22`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.textSecondary, fontSize: 11, fontWeight: 700, marginBottom: 8 }}>
          OPEN LOOPS
        </div>
        {summary?.open_loops.length ? (
          summary.open_loops.map(l => <OpenLoopRow key={l.id} loop={l} />)
        ) : (
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5, padding: '4px 10px' }}>
            {error ? 'Cannot reach API' : summary ? 'No open loops — organism clear' : 'Loading…'}
          </div>
        )}
      </div>
    </div>
  )
}

'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { isStale } from '@/lib/viewmodels'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

const RISK_COLORS: Record<string, string> = {
  R0: '#00FF88', R1: '#88CCFF', R2: '#FFFF00', R3: '#FFAA00', R4: '#FF3333',
}

function DispatchRow({ r }: { r: any }) {
  const ts = r.ts ? new Date(r.ts).toLocaleTimeString('en-US', { hour12: false }) : '—'
  const rc = RISK_COLORS[r.risk_tier] || tokens.colors.textSecondary
  return (
    <div style={{
      display: 'flex', gap: 8, padding: '5px 10px',
      borderBottom: `1px solid ${tokens.colors.border}`, alignItems: 'center',
    }}>
      <span style={{ fontSize: 8, color: rc, fontFamily: 'monospace', minWidth: 22 }}>{r.risk_tier}</span>
      <span style={{ fontSize: 10, color: r.ok !== false ? tokens.colors.textPrimary : '#FF8888', flex: 1 }}>
        {r.op}
      </span>
      <span style={{ fontSize: 8, color: r.reversible ? tokens.colors.healthy : '#FFAA00' }}>
        {r.reversible ? '↩ rev' : '⚑ irrev'}
      </span>
      <span style={{ fontSize: 8, color: tokens.colors.textSecondary, fontFamily: 'monospace', flexShrink: 0 }}>{ts}</span>
    </div>
  )
}

export function ExecutionSpace() {
  const [data, setData] = useState<any>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/execution`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setData(d)
      setFetchTs(new Date().toISOString())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    }
  }

  useEffect(() => { load(); const id = setInterval(load, 8000); return () => clearInterval(id) }, [])

  const stale = isStale(fetchTs ?? undefined, 20_000)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>

      {/* Handrail moat banner */}
      <div style={{
        gridColumn: '1 / -1', padding: '10px 16px',
        background: 'rgba(0,255,255,0.04)', border: `1px solid ${tokens.colors.handrail}44`,
        borderRadius: 8, display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 11, color: tokens.colors.handrail, fontWeight: 700 }}>HANDRAIL</span>
        {stale && <span style={{ fontSize: 8, color: '#FFAA00' }}>STALE</span>}
        <span style={{
          fontSize: 9, padding: '2px 8px',
          background: data?.handrail?.ok ? 'rgba(0,255,136,0.1)' : 'rgba(255,51,51,0.1)',
          border: `1px solid ${data?.handrail?.ok ? 'rgba(0,255,136,0.3)' : 'rgba(255,51,51,0.3)'}`,
          borderRadius: 3, color: data?.handrail?.ok ? tokens.colors.healthy : tokens.colors.error,
        }}>{data?.handrail?.ok ? '● LIVE' : '○ OFFLINE'}</span>
        {error && <span style={{ fontSize: 9, color: tokens.colors.error }}>{error}</span>}
        <span style={{ marginLeft: 'auto', fontSize: 9, color: tokens.colors.textSecondary, fontStyle: 'italic' }}>
          {data?.handrail?.notice || 'All real-world actions dispatch through Handrail. No UI surface bypasses this boundary.'}
        </span>
      </div>

      {/* Dispatch history */}
      <div style={{
        gridColumn: '1 / -1', background: '#0D1533',
        border: `1px solid ${tokens.colors.border}`, borderRadius: 8,
        overflow: 'hidden',
      }}>
        <div style={{ padding: '10px 14px', borderBottom: `1px solid ${tokens.colors.border}`, display: 'flex', gap: 8 }}>
          <span style={{ fontSize: 11, color: tokens.colors.adjudication, fontWeight: 700 }}>DISPATCH HISTORY</span>
          <span style={{ marginLeft: 'auto', fontSize: 9, color: tokens.colors.textSecondary }}>
            {data?.receipt_count ?? 0} receipts
          </span>
        </div>

        {/* Risk tier legend */}
        <div style={{
          padding: '4px 14px', borderBottom: `1px solid ${tokens.colors.border}`,
          display: 'flex', gap: 12,
        }}>
          {Object.entries(RISK_COLORS).map(([tier, c]) => (
            <span key={tier} style={{ fontSize: 8, color: c, fontFamily: 'monospace' }}>
              {tier}
            </span>
          ))}
          <span style={{ fontSize: 8, color: tokens.colors.textSecondary, marginLeft: 4 }}>risk tiers</span>
        </div>

        <div style={{ maxHeight: 320, overflowY: 'auto' }}>
          {data?.dispatch_history?.length ? (
            data.dispatch_history.map((r: any, i: number) => <DispatchRow key={i} r={r} />)
          ) : (
            <div style={{ padding: 14, fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>
              {error ? 'Cannot reach API' : data ? 'No dispatch history' : 'Loading…'}
            </div>
          )}
        </div>
      </div>

      {/* Failures */}
      {data?.failures?.length > 0 && (
        <div style={{
          gridColumn: '1 / -1', background: 'rgba(255,51,51,0.05)',
          border: '1px solid rgba(255,51,51,0.2)', borderRadius: 8, padding: 14,
        }}>
          <div style={{ color: tokens.colors.error, fontSize: 11, fontWeight: 700, marginBottom: 8 }}>FAILURES</div>
          {data.failures.map((f: any, i: number) => (
            <div key={i} style={{
              padding: '6px 10px', borderBottom: '1px solid rgba(255,51,51,0.15)',
              fontSize: 10, color: '#FF8888',
            }}>
              <span style={{ fontFamily: 'monospace', fontSize: 9 }}>{f.op}: </span>
              {String(f.error || '').slice(0, 120)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

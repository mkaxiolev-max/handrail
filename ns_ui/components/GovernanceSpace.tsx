'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { isStale } from '@/lib/viewmodels'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

export function GovernanceSpace() {
  const [data, setData] = useState<any>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [simInput, setSimInput] = useState('')
  const [simResult, setSimResult] = useState<any>(null)
  const [simLoading, setSimLoading] = useState(false)

  const load = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/governance`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setData(await r.json())
      setFetchTs(new Date().toISOString())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    }
  }

  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id) }, [])

  const simulatePolicy = async () => {
    const text = simInput.trim()
    if (!text || simLoading) return
    setSimLoading(true)
    try {
      const r = await fetch(`${NS_API}/api/v1/governance/simulate-policy`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, requested_by: 'founder' }),
      })
      setSimResult(await r.json())
    } catch (e: any) {
      setSimResult({ error: e.message })
    } finally {
      setSimLoading(false)
    }
  }

  const stale = isStale(fetchTs ?? undefined, 30_000)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      {/* Authority header */}
      <div style={{
        gridColumn: '1 / -1', padding: '8px 14px',
        background: '#080C1E', border: `1px solid ${tokens.colors.kernel}33`,
        borderRadius: 8, display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 11, color: tokens.colors.kernel, fontWeight: 700 }}>GOVERNANCE</span>
        {stale && <span style={{ fontSize: 8, color: '#FFAA00' }}>STALE</span>}
        {data ? (
          <>
            <span style={{
              fontSize: 9, padding: '1px 7px',
              background: 'rgba(255,51,51,0.08)', border: '1px solid rgba(255,51,51,0.25)',
              borderRadius: 3, color: tokens.colors.kernel, textTransform: 'uppercase',
            }}>{data.authority_state}</span>
            <span style={{ fontSize: 9, color: tokens.colors.textSecondary }}>
              v{data.rings?.length} rings ·
              {data.quorum?.satisfied ? ' ✓ quorum' : ' ⚠ quorum pending'}
            </span>
          </>
        ) : error ? (
          <span style={{ fontSize: 9, color: tokens.colors.error }}>{error}</span>
        ) : (
          <span style={{ fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.5 }}>connecting…</span>
        )}
      </div>

      {/* Never Events */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.kernel}33`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.kernel, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          NEVER EVENTS (SACRED)
        </div>
        {(data?.never_events ?? []).map((ne: any) => (
          <div key={ne.id} style={{
            display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5,
            padding: '4px 8px', background: 'rgba(255,51,51,0.04)', borderRadius: 4,
          }}>
            <span style={{ color: tokens.colors.healthy, fontSize: 10 }}>✓</span>
            <span style={{ fontSize: 9, color: tokens.colors.textSecondary, minWidth: 24 }}>{ne.id}</span>
            <span style={{ fontSize: 9, color: tokens.colors.textPrimary, fontFamily: 'monospace', flex: 1 }}>{ne.name}</span>
            {ne.sacred && (
              <span style={{ fontSize: 7, color: tokens.colors.kernel, padding: '1px 4px',
                border: '1px solid rgba(255,51,51,0.3)', borderRadius: 2 }}>SACRED</span>
            )}
          </div>
        ))}
      </div>

      {/* Rings + YubiKey */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.adjudication}33`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.adjudication, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          RINGS + QUORUM
        </div>
        {(data?.rings ?? []).map((r: any) => (
          <div key={r.ring} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
            <span style={{ color: r.complete ? tokens.colors.healthy : tokens.colors.warning, fontSize: 10 }}>
              {r.complete ? '✅' : '⏳'}
            </span>
            <span style={{ fontSize: 9, color: tokens.colors.textSecondary }}>Ring {r.ring}: {r.name}</span>
            {!r.complete && r.blocked_by && (
              <span style={{ fontSize: 8, color: tokens.colors.warning, marginLeft: 'auto' }}>
                ← {r.blocked_by}
              </span>
            )}
          </div>
        ))}
        {data?.quorum && (
          <div style={{ marginTop: 10, padding: '8px', background: '#0A0E27', borderRadius: 5 }}>
            <div style={{ fontSize: 8, color: tokens.colors.textSecondary, lineHeight: 1.8 }}>
              <div>YubiKey: <span style={{ color: tokens.colors.textPrimary }}>{data.quorum.yubikey_serial}</span></div>
              <div>Model: <span style={{ color: tokens.colors.textPrimary }}>{data.quorum.model}</span></div>
              {data.quorum.slot_2_pending && (
                <div style={{ color: '#FFAA00' }}>slot_2 pending (~$55)</div>
              )}
              <div>Quorum: <span style={{ color: data.quorum.satisfied ? tokens.colors.healthy : tokens.colors.warning }}>
                {data.quorum.satisfied ? '✓ satisfied' : '⚠ not satisfied'}
              </span></div>
            </div>
          </div>
        )}
      </div>

      {/* Invariants */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.textSecondary, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          10 INVARIANTS
        </div>
        {data?.invariants && Object.entries(data.invariants).map(([k, v]) => (
          <div key={k} style={{ display: 'flex', gap: 6, marginBottom: 4, alignItems: 'flex-start' }}>
            <span style={{ fontSize: 8, color: tokens.colors.healthy, minWidth: 18 }}>✓</span>
            <span style={{ fontSize: 8, color: tokens.colors.violet, minWidth: 20 }}>{k}</span>
            <span style={{ fontSize: 8, color: tokens.colors.textSecondary }}>{v as string}</span>
          </div>
        ))}
      </div>

      {/* Threshold requests + policy sim */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.textSecondary, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          THRESHOLD REQUESTS
        </div>
        {data?.threshold_requests?.length ? (
          data.threshold_requests.map((tr: any, i: number) => (
            <div key={i} style={{
              padding: '6px 8px', background: 'rgba(255,170,0,0.08)',
              border: '1px solid rgba(255,170,0,0.25)', borderRadius: 4, marginBottom: 6,
            }}>
              <div style={{ fontSize: 9, color: '#FFAA00', fontWeight: 700 }}>{tr.label}</div>
              <div style={{ fontSize: 8, color: tokens.colors.textSecondary }}>
                {tr.op} · {tr.risk_tier} {tr.requires_yubikey ? '· 🔑 YubiKey' : ''}
              </div>
            </div>
          ))
        ) : (
          <div style={{ fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.5, marginBottom: 12 }}>
            No pending threshold requests
          </div>
        )}

        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 9, color: tokens.colors.textSecondary, marginBottom: 6 }}>POLICY SIMULATION</div>
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              value={simInput}
              onChange={e => setSimInput(e.target.value)}
              placeholder="describe action to simulate…"
              style={{
                flex: 1, background: 'rgba(255,255,255,0.04)',
                border: `1px solid ${tokens.colors.border}`, borderRadius: 4,
                color: tokens.colors.textPrimary, padding: '4px 8px',
                fontSize: 9, fontFamily: 'monospace', outline: 'none',
              }}
            />
            <button
              onClick={simulatePolicy}
              disabled={!simInput.trim() || simLoading}
              style={{
                padding: '4px 10px', background: 'rgba(255,51,51,0.12)',
                border: '1px solid rgba(255,51,51,0.25)', borderRadius: 4,
                color: tokens.colors.kernel, fontSize: 9, fontFamily: 'monospace',
                cursor: simInput.trim() && !simLoading ? 'pointer' : 'default',
              }}
            >
              {simLoading ? '…' : 'SIM'}
            </button>
          </div>
          {simResult && (
            <div style={{
              marginTop: 6, padding: '4px 8px', borderRadius: 4, fontSize: 8,
              background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)',
              color: tokens.colors.adjudication, fontFamily: 'monospace',
            }}>
              {JSON.stringify(simResult).slice(0, 200)}
            </div>
          )}
        </div>
      </div>

      {/* Doctrine */}
      {data?.doctrine && (
        <div style={{
          gridColumn: '1 / -1', padding: '8px 14px',
          background: '#0D1533', border: `1px solid ${tokens.colors.border}`,
          borderRadius: 8, fontSize: 10, color: tokens.colors.textSecondary, fontStyle: 'italic',
        }}>
          {data.doctrine}
        </div>
      )}
    </div>
  )
}

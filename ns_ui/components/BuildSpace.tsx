'use client'
import { useState, useEffect, useCallback } from 'react'
import { tokens } from '@/lib/design-tokens'
import { isStale } from '@/lib/viewmodels'

const NS_API  = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'
const NS_CORE = process.env.NEXT_PUBLIC_NS_URL     || 'http://localhost:9000'

type Stage = 'input' | 'structured_objects' | 'program_candidates' | 'execution_candidates' | 'handrail_dispatch' | 'receipts' | 'memory_writeback'

const STAGE_COLORS: Record<string, string> = {
  ready:  tokens.colors.healthy,
  active: tokens.colors.adjudication,
  gated:  tokens.colors.warning,
  done:   '#88CCFF',
}

export function BuildSpace() {
  const [meta, setMeta] = useState<any>(null)
  const [input, setInput] = useState('')
  const [stage, setStage] = useState<Stage | null>(null)
  const [structuredObj, setStructuredObj] = useState<any>(null)
  const [execResult, setExecResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)

  const loadMeta = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/build`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setMeta(await r.json())
      setFetchTs(new Date().toISOString())
    } catch {}
  }

  useEffect(() => { loadMeta(); const id = setInterval(loadMeta, 15000); return () => clearInterval(id) }, [])

  const runPipeline = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return
    setLoading(true)
    setError(null)
    setStage('structured_objects')
    setStructuredObj(null)
    setExecResult(null)

    try {
      // Step 1: HIC compile → structured intent
      setStage('structured_objects')
      const hicRes = await fetch(`${NS_CORE}/hic/compile`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const hicData = await hicRes.json()
      setStructuredObj(hicData)
      setStage('program_candidates')
      await new Promise(r => setTimeout(r, 300))

      // Step 2: Show execution candidates (CPS ops derived from HIC)
      setStage('execution_candidates')
      await new Promise(r => setTimeout(r, 300))

      // Step 3: Handrail boundary — ops requiring risk-gated dispatch
      setStage('handrail_dispatch')
      const opsToExec = (hicData.ops || []).filter((op: any) =>
        ['R0', 'R1'].includes(op.risk_tier || 'R0')
      )

      if (opsToExec.length > 0) {
        const hrRes = await fetch(`${NS_CORE}/ops/cps`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ops: opsToExec }),
        })
        setExecResult(await hrRes.json())
      } else {
        setExecResult({ ok: true, note: 'No R0/R1 ops ready for dispatch', ops: [] })
      }

      setStage('receipts')
      await new Promise(r => setTimeout(r, 200))
      setStage('memory_writeback')
      await loadMeta()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [input, loading])

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) runPipeline()
  }

  const stale = isStale(fetchTs ?? undefined, 30_000)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 12 }}>
      {/* Pipeline column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Notice */}
        <div style={{
          padding: '8px 14px', background: `${tokens.colors.buildSpace}11`,
          border: `1px solid ${tokens.colors.buildSpace}33`, borderRadius: 8,
          fontSize: 9, color: tokens.colors.buildSpace,
        }}>
          {meta?.notice || 'Build Space — proposals exist outside Canon until explicit promotion.'}
        </div>

        {/* Pipeline stages */}
        <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
          <div style={{ fontSize: 11, color: tokens.colors.buildSpace, fontWeight: 700, marginBottom: 10 }}>
            PIPELINE
          </div>
          <div style={{ display: 'flex', gap: 0, alignItems: 'center', overflowX: 'auto' }}>
            {(meta?.pipeline_stages ?? []).map((s: any, i: number, arr: any[]) => {
              const active = stage === s.stage
              const c = STAGE_COLORS[s.status] ?? tokens.colors.textSecondary
              return (
                <div key={s.stage} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                  <div style={{
                    padding: '6px 10px', borderRadius: 5,
                    background: active ? `${c}22` : 'transparent',
                    border: `1px solid ${active ? c : tokens.colors.border}`,
                    fontSize: 9, textAlign: 'center',
                  }}>
                    <div style={{ color: c, fontWeight: active ? 700 : 400 }}>{s.label}</div>
                    {s.status === 'gated' && <div style={{ fontSize: 7, color: tokens.colors.warning, marginTop: 2 }}>HANDRAIL</div>}
                  </div>
                  {i < arr.length - 1 && (
                    <span style={{ fontSize: 12, color: tokens.colors.border, margin: '0 4px' }}>→</span>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Input */}
        <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.buildSpace}44`, borderRadius: 8, padding: 14 }}>
          <div style={{ fontSize: 11, color: tokens.colors.buildSpace, fontWeight: 700, marginBottom: 8 }}>
            FOUNDER INPUT
          </div>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="Describe an intent, program, or action… (⌘↵ to run)"
            rows={4}
            style={{
              width: '100%', background: 'rgba(74,111,165,0.08)',
              border: `1px solid ${tokens.colors.buildSpace}44`, borderRadius: 6,
              color: tokens.colors.textPrimary, padding: '8px 10px',
              fontSize: 11, fontFamily: 'monospace', resize: 'vertical',
              outline: 'none', lineHeight: 1.5, boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center' }}>
            <button
              onClick={runPipeline}
              disabled={!input.trim() || loading}
              style={{
                padding: '6px 18px',
                background: input.trim() && !loading ? `${tokens.colors.buildSpace}` : 'rgba(74,111,165,0.2)',
                border: 'none', borderRadius: 5,
                color: '#fff', fontSize: 10, fontFamily: 'monospace',
                fontWeight: 700, cursor: input.trim() && !loading ? 'pointer' : 'default',
                transition: 'all 0.15s',
              }}
            >
              {loading ? 'RUNNING…' : 'RUN PIPELINE'}
            </button>
            {error && <span style={{ fontSize: 9, color: tokens.colors.error }}>{error}</span>}
            {stage && !loading && <span style={{ fontSize: 9, color: tokens.colors.healthy }}>✓ {stage}</span>}
          </div>
        </div>

        {/* Structured objects result */}
        {structuredObj && (
          <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.adjudication}33`, borderRadius: 8, padding: 14 }}>
            <div style={{ fontSize: 11, color: tokens.colors.adjudication, fontWeight: 700, marginBottom: 8 }}>
              STRUCTURED OBJECTS (HIC)
            </div>
            <pre style={{
              fontSize: 9, color: tokens.colors.textPrimary, fontFamily: 'monospace',
              overflow: 'auto', maxHeight: 200,
              background: '#080C1E', padding: 8, borderRadius: 4,
              border: `1px solid ${tokens.colors.border}`,
            }}>
              {JSON.stringify(structuredObj, null, 2)}
            </pre>
          </div>
        )}

        {/* Execution result */}
        {execResult && (
          <div style={{
            background: '#0D1533',
            border: `1px solid ${execResult.ok ? tokens.colors.healthy : tokens.colors.error}33`,
            borderRadius: 8, padding: 14,
          }}>
            <div style={{ fontSize: 11, color: execResult.ok ? tokens.colors.healthy : tokens.colors.error, fontWeight: 700, marginBottom: 8 }}>
              EXECUTION RESULT
            </div>
            <pre style={{
              fontSize: 9, color: tokens.colors.textPrimary, fontFamily: 'monospace',
              overflow: 'auto', maxHeight: 200,
              background: '#080C1E', padding: 8, borderRadius: 4,
              border: `1px solid ${tokens.colors.border}`,
            }}>
              {JSON.stringify(execResult, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Sidebar: canon gate + recent programs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
          <div style={{ fontSize: 11, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 10 }}>CANON GATE</div>
          {meta?.canon_gate && (
            <div style={{ fontSize: 9, lineHeight: 1.8, color: tokens.colors.textSecondary }}>
              <div>Score ≥ <span style={{ color: tokens.colors.textPrimary }}>{meta.canon_gate.score_threshold}</span></div>
              <div>Contradiction ≤ <span style={{ color: tokens.colors.textPrimary }}>{meta.canon_gate.contradiction_ceiling}</span></div>
              <div style={{ marginTop: 6, fontSize: 8, fontStyle: 'italic', color: tokens.colors.textSecondary, opacity: 0.7 }}>
                {meta.canon_gate.note}
              </div>
            </div>
          )}
        </div>

        {stale && (
          <div style={{ fontSize: 8, color: '#FFAA00', padding: '4px 8px', background: 'rgba(255,170,0,0.08)', borderRadius: 4 }}>
            ⚠ meta stale
          </div>
        )}

        <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
          <div style={{ fontSize: 11, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 8 }}>RECENT PROGRAMS</div>
          {meta?.recent_programs?.length ? (
            meta.recent_programs.map((r: any, i: number) => (
              <div key={i} style={{
                padding: '4px 0', borderBottom: `1px solid ${tokens.colors.border}`,
                fontSize: 9, color: tokens.colors.textPrimary,
              }}>{r.op || r.receipt_id?.slice(0, 20) || '—'}</div>
            ))
          ) : (
            <div style={{ fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.5 }}>No program receipts yet</div>
          )}
        </div>
      </div>
    </div>
  )
}

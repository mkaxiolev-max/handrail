/**
 * OmegaPanel — Bounded simulation engine. Advisory only. Never Canon.
 * Divergence · Confidence · Branches · Breach points · Compare to reality
 */
import React, { useState, useEffect, useCallback } from 'react'

const API = 'http://localhost:9000/api/v1/omega'

function ProvTag({ text = 'Simulation · Advisory Only' }) {
  return (
    <span className="font-mono text-xs px-2 py-0.5 rounded border border-yellow-700 bg-yellow-900/20 text-yellow-400"
          style={{ fontSize: '9px', letterSpacing: '0.06em' }}>
      {text}
    </span>
  )
}

function DivBar({ score }) {
  const pct = Math.min(100, Math.round((score || 0) * 100))
  const color = pct > 70 ? 'bg-red-500' : pct > 40 ? 'bg-yellow-500' : 'bg-emerald-500'
  const textColor = pct > 70 ? 'text-red-400' : pct > 40 ? 'text-yellow-400' : 'text-emerald-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-gray-700 rounded overflow-hidden">
        <div className={`h-full ${color} rounded`} style={{ width: `${pct}%`, transition: 'width 0.5s' }} />
      </div>
      <span className={`font-mono text-xs ${textColor} w-8 text-right`}>{pct}%</span>
    </div>
  )
}

function ConfBar({ label, value }) {
  const pct = Math.round((value || 0) * 100)
  return (
    <div className="flex items-center gap-2 mb-0.5">
      <span className="text-gray-500 font-mono w-28 shrink-0" style={{ fontSize: '9px' }}>
        {label.replace(/_/g, ' ')}
      </span>
      <div className="flex-1 h-0.5 bg-gray-700 rounded overflow-hidden">
        <div className="h-full bg-violet-600 rounded" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-violet-400 w-7 text-right" style={{ fontSize: '9px' }}>{pct}%</span>
    </div>
  )
}

function BranchRow({ branch, index }) {
  const [open, setOpen] = useState(false)
  const pct = Math.round((branch.likelihood || 0) * 100)
  const breachCount = (branch.breach_points || []).length
  return (
    <div
      className={`rounded border mb-1 cursor-pointer ${open ? 'border-violet-600/40 bg-violet-900/10' : 'border-gray-700 bg-gray-900/30'}`}
      onClick={() => setOpen(o => !o)}
    >
      <div className="flex items-center justify-between px-2 py-1.5">
        <span className="font-mono text-violet-300 text-xs">Branch {index + 1}</span>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-violet-400">{pct}% likely</span>
          {breachCount > 0 && (
            <span className="font-mono text-xs px-1 rounded border border-red-700/50 bg-red-900/20 text-red-400"
                  style={{ fontSize: '8px' }}>
              {breachCount}✗
            </span>
          )}
          <span className="text-gray-600 text-xs">{open ? '▲' : '▼'}</span>
        </div>
      </div>
      {open && (
        <div className="px-2 pb-2">
          {(branch.assumptions || []).map((a, i) => (
            <div key={i} className="font-mono text-gray-400 text-xs">→ {String(a)}</div>
          ))}
          {(branch.breach_points || []).map((bp, i) => (
            <div key={i} className="font-mono text-yellow-400 text-xs mt-0.5">
              ⚠ {typeof bp === 'object' ? (bp.description || JSON.stringify(bp)) : String(bp)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function OmegaPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [compareResult, setCompareResult] = useState(null)
  const [comparing, setComparing] = useState(false)
  const [domain, setDomain] = useState('operational')
  const [intent, setIntent] = useState('Evaluate current state and branch risks')
  const [horizon, setHorizon] = useState(5)
  const [branches, setBranches] = useState(3)

  const loadRuns = useCallback(async () => {
    try {
      const r = await fetch(`${API}/runs`)
      const d = await r.json()
      setRuns(Array.isArray(d) ? d : (d.runs || []))
    } catch {}
  }, [])

  useEffect(() => { loadRuns() }, [loadRuns])

  const simulate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    setCompareResult(null)
    try {
      const r = await fetch(`${API}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_type: domain,
          bounded_context: { description: intent },
          variables: {},
          constraints: { allow_execution: false, allow_promotion: false },
          observables: [],
          simulation_horizon: horizon,
          branch_count: branches,
          metadata: { actor: 'founder', source: 'violet_ui' },
        }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d?.detail?.reason || d?.detail || `HTTP ${r.status}`)
      setResult(d)
      setSelectedRun(d.run_id)
      loadRuns()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const compareToReality = async () => {
    if (!selectedRun) return
    setComparing(true)
    try {
      const r = await fetch(`${API}/runs/${selectedRun}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          observed_outcome: {
            status: 'founder_review',
            notes: `Manual compare at ${new Date().toISOString()}`,
            operator: 'founder',
          }
        }),
      })
      setCompareResult(await r.json())
    } catch (e) {
      setCompareResult({ error: e.message })
    } finally {
      setComparing(false)
    }
  }

  const conf = result?.confidence || {}
  const summary = result?.summary || {}

  return (
    <div className="h-full flex flex-col bg-gray-900 text-gray-100 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-700 bg-gray-800 shrink-0">
        <div>
          <div className="font-mono font-bold text-violet-300 text-sm tracking-wider">⍉ OMEGA</div>
          <div className="font-mono text-gray-500" style={{ fontSize: '9px', letterSpacing: '0.06em' }}>
            BOUNDED SIMULATION ENGINE
          </div>
        </div>
        <ProvTag />
      </div>

      {/* Input */}
      <div className="p-4 border-b border-gray-700 shrink-0">
        <div className="mb-3">
          <label className="block font-mono text-gray-500 mb-1" style={{ fontSize: '9px' }}>INTENT / CONTEXT</label>
          <textarea
            value={intent}
            onChange={e => setIntent(e.target.value)}
            rows={2}
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm font-mono text-gray-200 focus:outline-none focus:border-violet-500 resize-none"
          />
        </div>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block font-mono text-gray-500 mb-1" style={{ fontSize: '9px' }}>DOMAIN</label>
            <select
              value={domain}
              onChange={e => setDomain(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-violet-500"
            >
              {['operational','fundraising','commercial','governance','strategic','partnership','product'].map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block font-mono text-gray-500 mb-1" style={{ fontSize: '9px' }}>HORIZON</label>
            <input type="number" min="1" max="20" value={horizon}
              onChange={e => setHorizon(+e.target.value)}
              className="w-14 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs font-mono text-gray-200 text-center focus:outline-none focus:border-violet-500"
            />
          </div>
          <div>
            <label className="block font-mono text-gray-500 mb-1" style={{ fontSize: '9px' }}>BRANCHES</label>
            <input type="number" min="1" max="5" value={branches}
              onChange={e => setBranches(+e.target.value)}
              className="w-14 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs font-mono text-gray-200 text-center focus:outline-none focus:border-violet-500"
            />
          </div>
          <button
            onClick={simulate}
            disabled={loading}
            className="px-4 py-1.5 bg-violet-700 hover:bg-violet-600 disabled:opacity-40 rounded text-xs font-mono font-semibold text-white transition-colors"
          >
            {loading ? 'SIMULATING…' : 'RUN SIMULATION'}
          </button>
        </div>
        {error && (
          <div className="mt-2 px-3 py-2 bg-red-900/30 border border-red-700/50 rounded text-red-400 text-xs font-mono">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="flex-1 p-4 overflow-auto">
          {/* Policy strip */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ProvTag text={result.policy_state || 'advisory_only'} />
              {result.chain_verified && (
                <span className="font-mono text-emerald-400 border border-emerald-700/40 bg-emerald-900/20 px-2 py-0.5 rounded"
                      style={{ fontSize: '8px' }}>chain ✓</span>
              )}
            </div>
            <span className="font-mono text-gray-600" style={{ fontSize: '9px' }}>
              {result.receipt_hash?.slice(0, 14)}…
            </span>
          </div>

          {/* Divergence */}
          <div className="mb-4">
            <div className="font-mono text-gray-500 mb-1.5" style={{ fontSize: '9px', letterSpacing: '0.06em' }}>DIVERGENCE</div>
            <DivBar score={result.divergence_score} />
          </div>

          {/* Confidence */}
          {Object.keys(conf).some(k => typeof conf[k] === 'number') && (
            <div className="mb-4">
              <div className="font-mono text-gray-500 mb-1.5" style={{ fontSize: '9px', letterSpacing: '0.06em' }}>CONFIDENCE GEOMETRY</div>
              {Object.entries(conf).map(([k, v]) =>
                typeof v === 'number' ? <ConfBar key={k} label={k} value={v} /> : null
              )}
            </div>
          )}

          {/* Interventions */}
          {(summary.intervention_candidates || []).length > 0 && (
            <div className="mb-4">
              <div className="font-mono text-gray-500 mb-1.5" style={{ fontSize: '9px', letterSpacing: '0.06em' }}>INTERVENTIONS</div>
              {summary.intervention_candidates.map((ic, i) => (
                <div key={i} className="font-mono text-violet-300 text-xs px-2 py-1 bg-violet-900/10 border border-violet-700/20 rounded mb-1">
                  → {typeof ic === 'object' ? (ic.action || JSON.stringify(ic)) : String(ic)}
                </div>
              ))}
            </div>
          )}

          {/* Epistemic boundary */}
          {summary.epistemic_boundary && (
            <div className="mb-4 p-2 bg-yellow-900/10 border border-yellow-700/30 rounded">
              <div className="font-mono text-yellow-700 mb-1" style={{ fontSize: '8px', letterSpacing: '0.06em' }}>EPISTEMIC BOUNDARY</div>
              <div className="font-mono text-yellow-400 text-xs">{summary.epistemic_boundary}</div>
            </div>
          )}

          {/* Warnings */}
          {(result.warnings || []).map((w, i) => (
            <div key={i} className="mb-1 font-mono text-yellow-400 text-xs">⚠ {w}</div>
          ))}

          {/* Branches */}
          {(result.branches || []).length > 0 && (
            <div className="mb-4">
              <div className="font-mono text-gray-500 mb-2" style={{ fontSize: '9px', letterSpacing: '0.06em' }}>
                BRANCHES ({result.branches.length})
              </div>
              {result.branches.map((b, i) => <BranchRow key={b.branch_id || i} branch={b} index={i} />)}
            </div>
          )}

          {/* Compare to reality */}
          <div className="mb-4">
            <button
              onClick={compareToReality}
              disabled={comparing}
              className="px-3 py-1 bg-teal-900/30 hover:bg-teal-900/50 border border-teal-700/40 disabled:opacity-40 rounded text-xs font-mono font-semibold text-teal-400 transition-colors"
            >
              {comparing ? 'COMPARING…' : '⟳ COMPARE TO REALITY'}
            </button>
            {compareResult && !compareResult.error && (
              <div className="mt-2 p-2 bg-teal-900/10 border border-teal-700/30 rounded">
                <div className="flex justify-between mb-1">
                  <span className="font-mono text-gray-500" style={{ fontSize: '8px' }}>REALITY GAP</span>
                  <ProvTag text="provisional comparison" />
                </div>
                <div className="font-mono text-teal-400 text-xs">
                  Best match: Branch {(compareResult.best_match_branch_index ?? 0) + 1}
                  {' · '}{Math.round((compareResult.reality_gap || 0) * 100)}% gap
                </div>
              </div>
            )}
            {compareResult?.error && (
              <div className="mt-1 font-mono text-red-400 text-xs">{compareResult.error}</div>
            )}
          </div>
        </div>
      )}

      {/* Run history */}
      {runs.length > 0 && (
        <div className="border-t border-gray-700 p-3 shrink-0 max-h-28 overflow-auto">
          <div className="font-mono text-gray-600 mb-1.5" style={{ fontSize: '9px', letterSpacing: '0.06em' }}>
            RUN HISTORY
          </div>
          {runs.slice(0, 6).map(run => (
            <div
              key={run.run_id}
              onClick={() => setSelectedRun(run.run_id)}
              className={`flex justify-between items-center px-2 py-1 mb-0.5 rounded cursor-pointer text-xs font-mono ${
                selectedRun === run.run_id
                  ? 'bg-violet-800/40 border border-violet-600/40 text-violet-200'
                  : 'bg-gray-800/40 text-gray-400 hover:bg-gray-700/40'
              }`}
            >
              <span>{run.run_id?.slice(0, 18)}</span>
              <span className="text-gray-600">{run.domain_type} · {run.branch_count}B</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

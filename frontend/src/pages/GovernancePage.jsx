import React, { useEffect, useState } from 'react'
import axios from 'axios'

const NS_CORE = 'http://127.0.0.1:9000'

const GovernancePage = () => {
  const [govState, setGovState] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await axios.get(`${NS_CORE}/governance/state`)
        setGovState(res.data)
        setError(null)
      } catch (e) {
        setError(e.message)
      }
    }
    fetch_()
    const id = setInterval(fetch_, 10000)
    return () => clearInterval(id)
  }, [])

  const invariants = govState?.invariants ?? {}
  const gate = govState?.canon_gate ?? {}

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold font-mono">Governance</h1>
      {error && <div className="text-red-400 text-xs font-mono">{error}</div>}

      {govState && (
        <>
          <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
            <div className="text-xs text-gray-400 font-mono mb-3 uppercase tracking-wider">10 Invariants</div>
            <div className="space-y-1">
              {Object.entries(invariants).map(([k, v]) => (
                <div key={k} className="flex gap-3 text-xs font-mono">
                  <span className="text-green-400 w-4">✓</span>
                  <span className="text-violet-400 w-6">{k}</span>
                  <span className="text-gray-300">{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
            <div className="text-xs text-gray-400 font-mono mb-3 uppercase tracking-wider">Six-Fold Canon Gate</div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Score threshold</span>
                <span className="text-gray-300">{gate.score_threshold}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Contradiction ceiling</span>
                <span className="text-gray-300">{gate.contradiction_ceiling}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Reconstructability</span>
                <span className="text-gray-300">{gate.reconstructability_threshold}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Quorum required</span>
                <span className="text-gray-300">{govState.quorum_required}</span>
              </div>
            </div>
            <div className="mt-3 flex gap-2 flex-wrap">
              {(gate.conditions_six_fold ?? []).map(c => (
                <span key={c} className="text-xs font-mono bg-violet-900/30 border border-violet-500/30 rounded px-2 py-0.5 text-violet-300">
                  {c}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
            <div className="text-xs text-gray-400 font-mono mb-2 uppercase tracking-wider">Doctrine</div>
            <p className="text-xs text-gray-300 font-mono">{govState.doctrine}</p>
          </div>
        </>
      )}
      {!govState && !error && (
        <div className="text-xs text-gray-500 font-mono">Loading governance state…</div>
      )}
    </div>
  )
}

export default GovernancePage

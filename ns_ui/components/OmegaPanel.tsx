'use client'
import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { tokens } from '@/lib/design-tokens'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9000/api/v1'

export function OmegaPanel({
  omegaRuns,
  omegaLatest,
}: {
  omegaRuns?: any
  omegaLatest?: any
}) {
  const latestRun = useMemo(() => {
    if (omegaLatest?.run_id) return omegaLatest
    const runs = omegaRuns?.runs || []
    return runs[0] || null
  }, [omegaLatest, omegaRuns])

  const [compareInput, setCompareInput] = useState('{"observed_state":{"demand":10,"capacity":8,"burn":3}}')
  const [compareResult, setCompareResult] = useState<any>(null)
  const [compareError, setCompareError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const runId = latestRun?.run_id
  const summary = latestRun?.summary_payload || omegaLatest?.summary || {}
  const confidence = latestRun?.confidence || omegaLatest?.confidence || summary?.confidence_geometry || {}
  const branches = omegaLatest?.branches || []

  const runCompare = async () => {
    if (!runId) return
    try {
      setLoading(true)
      setCompareError(null)
      const parsed = JSON.parse(compareInput)
      const res = await fetch(`${NS_API}/api/v1/omega/runs/${runId}/compare`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(parsed),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'compare_failed')
      setCompareResult(data)
    } catch (err: any) {
      setCompareError(err?.message || 'compare_failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{display:'grid',gridTemplateColumns:'1.15fr 0.85fr',gap:12}}>
      <div style={{
        background:'linear-gradient(135deg, #101A3D 0%, #0A1020 100%)',
        border:`1px solid ${tokens.colors.buildSpace}`,
        borderRadius:12,
        padding:16,
      }}>
        <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:10}}>
          <span style={{color:tokens.colors.buildSpace,fontSize:12,fontWeight:'bold'}}>OMEGA SIMULATION</span>
          <span style={{
            border:`1px solid ${tokens.colors.warning}`,
            color:tokens.colors.warning,
            borderRadius:12,
            padding:'2px 8px',
            fontSize:9,
          }}>PROVISIONAL RESULT</span>
        </div>

        {!runId ? (
          <div style={{color:tokens.colors.textSecondary,fontSize:10,opacity:0.7}}>
            No Omega runs yet. Simulations will appear here once the service is exercised.
          </div>
        ) : (
          <>
            <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:8,marginBottom:12}}>
              <MetricCard label="Run ID" value={String(runId).slice(0, 18)} accent={tokens.colors.buildSpace} />
              <MetricCard label="Divergence" value={String(summary?.divergence_score ?? latestRun?.divergence_score ?? '—')} accent={tokens.colors.warning} />
              <MetricCard label="Confidence" value={String(confidence?.overall_confidence ?? '—')} accent={tokens.colors.adjudication} />
            </div>

            <div style={{background:'#0A0E27',borderRadius:10,padding:12,border:`1px solid ${tokens.colors.border}`,marginBottom:12}}>
              <div style={{fontSize:10,color:tokens.colors.textSecondary,marginBottom:6}}>Epistemic Boundary</div>
              <div style={{fontSize:11,color:tokens.colors.textPrimary,lineHeight:1.5}}>
                {summary?.epistemic_boundary || confidence?.epistemic_boundary || 'Simulation remains bounded and non-canonical.'}
              </div>
              <div style={{marginTop:8,fontSize:9,color:tokens.colors.alexandria}}>
                Receipt: {latestRun?.receipt_hash || omegaLatest?.receipt_hash || 'pending'}
              </div>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
              <PanelBlock title="Branch Spread">
                {Object.keys(summary?.branch_spread || {}).length === 0 ? (
                  <EmptyLine text="No branch spread available yet" />
                ) : Object.entries(summary.branch_spread).map(([key, value]) => (
                  <ValueRow key={key} label={key} value={String(value)} />
                ))}
              </PanelBlock>

              <PanelBlock title="Confidence Geometry">
                {[
                  ['observability', confidence?.observability],
                  ['branch_stability', confidence?.branch_stability],
                  ['divergence_pressure', confidence?.divergence_pressure],
                  ['model_fit', confidence?.model_fit],
                  ['constraint_satisfaction', confidence?.constraint_satisfaction],
                ].map(([label, value]) => (
                  <ValueRow key={String(label)} label={String(label)} value={value === undefined ? '—' : String(value)} />
                ))}
              </PanelBlock>

              <PanelBlock title="Breach Points">
                {(summary?.key_branch_points || []).length === 0 ? (
                  <EmptyLine text="No breach points flagged" />
                ) : (summary.key_branch_points || []).map((point: any, idx: number) => (
                  <div key={idx} style={{marginBottom:8,fontSize:10}}>
                    <div style={{color:tokens.colors.warning}}>{point.variable} @ step {point.step_index}</div>
                    <div style={{color:tokens.colors.textSecondary}}>{point.description}</div>
                  </div>
                ))}
              </PanelBlock>

              <PanelBlock title="Intervention Candidates">
                {(summary?.intervention_candidates || []).length === 0 ? (
                  <EmptyLine text="No interventions suggested" />
                ) : (summary.intervention_candidates || []).map((candidate: any, idx: number) => (
                  <div key={idx} style={{marginBottom:8,fontSize:10}}>
                    <div style={{color:tokens.colors.adjudication}}>{candidate.action}</div>
                    <div style={{color:tokens.colors.textSecondary}}>{candidate.expected_effect}</div>
                  </div>
                ))}
              </PanelBlock>
            </div>
          </>
        )}
      </div>

      <div style={{display:'flex',flexDirection:'column',gap:12}}>
        <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.border}`,borderRadius:12,padding:14}}>
          <div style={{color:tokens.colors.violet,fontSize:11,fontWeight:'bold',marginBottom:8}}>RUN HISTORY</div>
          {!(omegaRuns?.runs || []).length ? (
            <EmptyLine text="No runs loaded" />
          ) : (omegaRuns.runs || []).slice(0, 6).map((run: any) => (
            <div key={run.run_id} style={{
              padding:'8px 10px',
              borderRadius:8,
              background: run.run_id === runId ? `${tokens.colors.buildSpace}22` : '#0A0E27',
              border:`1px solid ${run.run_id === runId ? tokens.colors.buildSpace : tokens.colors.border}`,
              marginBottom:8,
            }}>
              <div style={{fontSize:10,color:tokens.colors.textPrimary}}>{run.domain_type || 'domain'} · {run.status}</div>
              <div style={{fontSize:9,color:tokens.colors.textSecondary}}>{String(run.run_id).slice(0, 20)}</div>
            </div>
          ))}
        </div>

        <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.warning}55`,borderRadius:12,padding:14}}>
          <div style={{color:tokens.colors.warning,fontSize:11,fontWeight:'bold',marginBottom:8}}>
            REPLAY VS REALITY
          </div>
          <textarea
            value={compareInput}
            onChange={(e) => setCompareInput(e.target.value)}
            style={{
              width:'100%',
              minHeight:110,
              background:'#0A0E27',
              color:tokens.colors.textPrimary,
              border:`1px solid ${tokens.colors.border}`,
              borderRadius:8,
              padding:10,
              fontSize:10,
              fontFamily:'monospace',
              marginBottom:10,
            }}
          />
          <button
            onClick={runCompare}
            disabled={!runId || loading}
            style={{
              width:'100%',
              background: loading ? '#334' : `${tokens.colors.warning}22`,
              color:tokens.colors.warning,
              border:`1px solid ${tokens.colors.warning}`,
              borderRadius:8,
              padding:'8px 10px',
              fontSize:10,
              cursor: !runId || loading ? 'default' : 'pointer',
            }}
          >
            {loading ? 'Comparing...' : 'Compare Against Stored Branches'}
          </button>
          {compareError && <div style={{marginTop:8,fontSize:9,color:tokens.colors.error}}>{compareError}</div>}
          {compareResult && (
            <div style={{marginTop:10,fontSize:10}}>
              <div style={{color:tokens.colors.textPrimary,marginBottom:4}}>
                Best match: {compareResult.best_match_branch}
              </div>
              <div style={{color:tokens.colors.textSecondary,marginBottom:4}}>
                Reality gap: {compareResult.reality_gap}
              </div>
              {(compareResult.warnings || []).map((warning: string, idx: number) => (
                <div key={idx} style={{color:tokens.colors.warning,marginBottom:4}}>{warning}</div>
              ))}
            </div>
          )}
        </div>

        <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.border}`,borderRadius:12,padding:14}}>
          <div style={{color:tokens.colors.handrail,fontSize:11,fontWeight:'bold',marginBottom:8}}>LATEST BRANCHES</div>
          {branches.length === 0 ? (
            <EmptyLine text="Branch detail will populate from the latest simulation envelope" />
          ) : branches.slice(0, 4).map((branch: any) => (
            <div key={branch.branch_id} style={{marginBottom:10,paddingBottom:10,borderBottom:`1px solid ${tokens.colors.border}`}}>
              <div style={{fontSize:10,color:tokens.colors.textPrimary}}>
                {branch.branch_id.slice(-8)} · likelihood {branch.likelihood}
              </div>
              <div style={{fontSize:9,color:tokens.colors.textSecondary}}>
                {(branch.assumptions || []).slice(0, 1).join(' ') || 'No assumptions captured'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MetricCard({label, value, accent}: {label: string, value: string, accent: string}) {
  return (
    <div style={{background:'#0A0E27',border:`1px solid ${accent}55`,borderRadius:10,padding:10}}>
      <div style={{fontSize:9,color:accent,marginBottom:4}}>{label}</div>
      <div style={{fontSize:12,color:tokens.colors.textPrimary,fontWeight:'bold'}}>{value}</div>
    </div>
  )
}

function PanelBlock({title, children}: {title: string, children: ReactNode}) {
  return (
    <div style={{background:'#0A0E27',border:`1px solid ${tokens.colors.border}`,borderRadius:10,padding:12}}>
      <div style={{fontSize:10,color:tokens.colors.textSecondary,marginBottom:8}}>{title}</div>
      {children}
    </div>
  )
}

function ValueRow({label, value}: {label: string, value: string}) {
  return (
    <div style={{display:'flex',justifyContent:'space-between',gap:10,fontSize:10,marginBottom:6}}>
      <span style={{color:tokens.colors.textSecondary}}>{label}</span>
      <span style={{color:tokens.colors.textPrimary}}>{value}</span>
    </div>
  )
}

function EmptyLine({text}: {text: string}) {
  return <div style={{fontSize:10,color:tokens.colors.textSecondary,opacity:0.7}}>{text}</div>
}

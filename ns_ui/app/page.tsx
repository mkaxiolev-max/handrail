import { VioletPanel } from "../../components/VioletPanel"
'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { VoiceOverlay } from '@/components/VoiceOverlay'
import { OrganismMap } from '@/components/OrganismMap'
import { EngineRoom } from '@/components/EngineRoom'
import { ProgramsRuntime } from '@/components/ProgramsRuntime'
import { GovernancePanel } from '@/components/GovernancePanel'
import { Timeline } from '@/components/Timeline'
import { OmegaPanel } from '@/components/OmegaPanel'
import { VioletLogo, AxiolevWordmark } from '@/components/VioletMark'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9000'

type Mode = 'organism'|'engine'|'runtime'|'memory'|'governance'|'omega'|'build'

const MODES: {id: Mode, label: string, color: string}[] = [
  {id:'organism', label:'Living Architecture', color: tokens.colors.violet},
  {id:'engine', label:'Engine Room', color: tokens.colors.handrail},
  {id:'runtime', label:'Programs Runtime', color: '#88FFAA'},
  {id:'memory', label:'Memory / Alexandria', color: tokens.colors.alexandria},
  {id:'governance', label:'Governance', color: tokens.colors.kernel},
  {id:'omega', label:'Omega Simulation', color: tokens.colors.buildSpace},
  {id:'build', label:'Build Space', color: tokens.colors.buildSpace},
]

export default function Home() {
  const [mode, setMode] = useState<Mode>('organism')
  const [systemState, setSystemState] = useState<any>(null)
  const [engineData, setEngineData] = useState<any>(null)
  const [programs, setPrograms] = useState<any[]>([])
  const [govState, setGovState] = useState<any>(null)
  const [timeline, setTimeline] = useState<any[]>([])
  const [selectedNode, setSelectedNode] = useState<string|null>(null)
  const [violetIdentity, setVioletIdentity] = useState<any>(null)
  const [omegaRuns, setOmegaRuns] = useState<any>(null)
  const [omegaLatest, setOmegaLatest] = useState<any>(null)

  const fetchAll = async () => {
    try {
      const [sys, eng, progs, gov, tl, vi, omegaRunsResp] = await Promise.allSettled([
        fetch(`${NS_API}/api/v1/system/state`).then(r=>r.json()),
        fetch(`${NS_API}/api/v1/engine/live`).then(r=>r.json()),
        fetch(`${NS_API}/api/v1/programs`).then(r=>r.json()),
        fetch(`${NS_API}/api/v1/governance/state`).then(r=>r.json()),
        fetch(`${NS_API}/api/v1/system/timeline`).then(r=>r.json()),
        fetch('http://localhost:9000/violet/identity').then(r=>r.json()),
        fetch(`${NS_API}/api/v1/omega/runs`).then(r=>r.json()),
      ])
      if (sys.status==='fulfilled') setSystemState(sys.value)
      if (eng.status==='fulfilled') setEngineData(eng.value)
      if (progs.status==='fulfilled') {
        const p = progs.value
        setPrograms(Array.isArray(p) ? p : (p?.programs || []))
      }
      if (gov.status==='fulfilled') setGovState(gov.value)
      if (tl.status==='fulfilled') setTimeline(Array.isArray(tl.value) ? tl.value : [])
      if (vi.status==='fulfilled') setVioletIdentity(vi.value)
      if (omegaRunsResp.status==='fulfilled') {
        setOmegaRuns(omegaRunsResp.value)
        const firstRun = omegaRunsResp.value?.runs?.[0]
        if (firstRun?.run_id) {
          try {
            const latest = await fetch(`${NS_API}/api/v1/omega/runs/${firstRun.run_id}`).then(r=>r.json())
            const branchData = await fetch(`${NS_API}/api/v1/omega/runs/${firstRun.run_id}/branches`).then(r=>r.json())
            setOmegaLatest({...latest, branches: branchData?.branches || []})
          } catch(e) {}
        } else {
          setOmegaLatest(null)
        }
      }
    } catch(e) {}
  }

  useEffect(() => { fetchAll(); const i = setInterval(fetchAll, 5000); return () => clearInterval(i) }, [])

  const currentMode = MODES.find(m => m.id === mode)!

  return (
    <div style={{minHeight:'100vh',background:tokens.colors.bg,display:'flex',flexDirection:'column'}}>
      <VoiceOverlay />

      {/* Top bar */}
      <div style={{background:'#080C1E',borderBottom:`1px solid ${tokens.colors.border}`,
        padding:'10px 20px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
        <div style={{display:'flex',alignItems:'center',gap:16}}>
          <VioletLogo size={28} />
          <AxiolevWordmark style={{fontSize:11}} />
          <span style={{color:tokens.colors.textSecondary,fontSize:11}}>NS∞ · Living Architecture</span>
          <span style={{color:tokens.colors.adjudication,fontSize:10}}>
            {systemState ? '● LIVE' : '○ CONNECTING'}
          </span>
        </div>
        {violetIdentity && (
          <div style={{fontSize:10,color:tokens.colors.textSecondary}}>
            <span style={{color:tokens.colors.violet}}>Violet</span>
            {' '}{violetIdentity.version} · {violetIdentity.shalom ? '✓ Shalom' : '⚠ Shalom'}
          </div>
        )}
      </div>

      <div style={{display:'flex',flex:1}}>
        {/* Left rail - mode navigation */}
        <div style={{width:180,background:'#080C1E',borderRight:`1px solid ${tokens.colors.border}`,
          padding:'16px 8px',display:'flex',flexDirection:'column',gap:4}}>
          {MODES.map(m => (
            <button key={m.id} onClick={() => setMode(m.id)} style={{
              background: mode===m.id ? `${m.color}22` : 'transparent',
              border: `1px solid ${mode===m.id ? m.color : 'transparent'}`,
              borderRadius:6, padding:'8px 12px', cursor:'pointer',
              color: mode===m.id ? m.color : tokens.colors.textSecondary,
              fontSize:11, textAlign:'left', transition:'all 0.2s'
            }}>{m.label}</button>
          ))}

          <div style={{marginTop:'auto',borderTop:`1px solid ${tokens.colors.border}`,paddingTop:12}}>
            <div style={{fontSize:9,color:tokens.colors.textSecondary,marginBottom:4}}>SERVICES</div>
            {[
              {label:'Handrail :8011', port:8011},
              {label:'NS :9000', port:9000},
              {label:'ns_api :9001', port:9001},
              {label:'Voice :9002', port:9002},
              {label:'Telephony :9003', port:9003},
              {label:'Conf :9004', port:9004},
            ].map(s => (
              <div key={s.port} style={{fontSize:9,color:tokens.colors.healthy,marginBottom:2}}>
                ● {s.label}
              </div>
            ))}
          </div>
        </div>

        {/* Center canvas */}
        <div style={{flex:1,padding:16,overflow:'auto'}}>
          <div style={{marginBottom:12,display:'flex',alignItems:'center',gap:8}}>
            <h2 style={{margin:0,fontSize:16,color:currentMode.color}}>{currentMode.label}</h2>
            <span style={{fontSize:10,color:tokens.colors.textSecondary}}>
              {mode==='organism' ? '— Autopoietic organism view' :
               mode==='engine' ? '— Cognition, adjudication, execution' :
               mode==='runtime' ? '— 10 constitutional programs' :
               mode==='memory' ? '— Alexandria ledger + receipts' :
               mode==='governance' ? '— Never-events, rings, quorum' :
               mode==='omega' ? '— Bounded, provisional branch simulation' :
               '— Design sandbox (outside canon)'}
            </span>
          </div>

          {mode==='organism' && <OrganismMap systemState={systemState} />}
          {mode==='engine' && <EngineRoom engineData={engineData} programs={programs} />}
          {mode==='runtime' && <ProgramsRuntime programs={programs} />}
          {mode==='memory' && (
            <div style={{background:'#0D1533',borderRadius:8,padding:16}}>
              <div style={{color:tokens.colors.alexandria,marginBottom:12,fontSize:12,fontWeight:'bold'}}>
                ALEXANDRIA — Memory Ledger
              </div>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:8}}>
                {[
                  {label:'Receipts', path:'/Volumes/NSExternal/receipts/', color:tokens.colors.handrail},
                  {label:'Atoms', path:'/Volumes/NSExternal/alexandria/atoms/', color:tokens.colors.adjudication},
                  {label:'Corpus', path:'/Volumes/NSExternal/alexandria/raw_ingest/', color:tokens.colors.violet},
                ].map(m => (
                  <div key={m.label} style={{background:'#0A0E27',borderRadius:6,padding:12,
                    border:`1px solid ${m.color}33`}}>
                    <div style={{color:m.color,fontSize:11,marginBottom:4}}>{m.label}</div>
                    <div style={{fontSize:9,color:tokens.colors.textSecondary}}>{m.path}</div>
                  </div>
                ))}
              </div>
              <div style={{marginTop:12}}>
                <div style={{color:tokens.colors.textSecondary,fontSize:10,marginBottom:8}}>Recent Timeline</div>
                <Timeline events={timeline} />
              </div>
            </div>
          )}
          {mode==='governance' && <GovernancePanel govState={govState} />}
          {mode==='omega' && <OmegaPanel omegaRuns={omegaRuns} omegaLatest={omegaLatest} />}
          {mode==='build' && (
            <div style={{background:'#0A1020',border:`2px dashed ${tokens.colors.buildSpace}`,
              borderRadius:12,padding:32,textAlign:'center',color:tokens.colors.buildSpace}}>
              <div style={{fontSize:24,marginBottom:8}}>⬡</div>
              <div style={{fontSize:14,fontWeight:'bold',marginBottom:8}}>BUILD SPACE</div>
              <div style={{fontSize:11,opacity:0.7,maxWidth:400,margin:'0 auto'}}>
                Design sandbox — outside the canonical boundary.<br/>
                Proposals, speculative builds, roadmaps, and unresolved questions live here.<br/>
                Nothing here mutates Canon without explicit promotion.
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div style={{width:260,background:'#080C1E',borderLeft:`1px solid ${tokens.colors.border}`,
          padding:16,overflow:'auto'}}>
          <div style={{fontSize:11,color:tokens.colors.textSecondary,marginBottom:12,fontWeight:'bold'}}>
            SYSTEM STATE
          </div>
          {systemState ? (
            <div style={{fontSize:10}}>
              <div style={{color:tokens.colors.adjudication,marginBottom:4}}>
                Phase: {systemState.metrics?.phase || 'idle'}
              </div>
              <div style={{color:tokens.colors.textSecondary}}>
                Integrity: {((systemState.metrics?.autopoietic_integrity||0)*100).toFixed(0)}%
              </div>
              <div style={{color:tokens.colors.textSecondary}}>
                Memory: {((systemState.metrics?.memory_usage||0)*100).toFixed(0)}%
              </div>
              <div style={{marginTop:8,color:tokens.colors.textSecondary}}>Services:</div>
              {systemState.nodes?.slice(0,6).map((n:any) => (
                <div key={n.id} style={{fontSize:9,color: n.health==='ok' ? tokens.colors.healthy : tokens.colors.warning}}>
                  {n.health==='ok'?'●':'○'} {n.label}
                </div>
              ))}
              {systemState.services?.slice(0,6).map((s:any) => (
                <div key={s.service} style={{fontSize:9,color: s.healthy ? tokens.colors.healthy : tokens.colors.warning}}>
                  {s.healthy?'●':'○'} {s.service}
                </div>
              ))}
            </div>
          ) : (
            <div style={{fontSize:10,color:tokens.colors.textSecondary,opacity:0.5}}>
              Connecting to NS API...
            </div>
          )}

          {violetIdentity && (
            <div style={{marginTop:16,padding:10,background:'#0D1533',borderRadius:8,
              border:`1px solid ${tokens.colors.violet}33`}}>
              <div style={{color:tokens.colors.violet,fontSize:10,fontWeight:'bold',marginBottom:6}}>VIOLET</div>
              <div style={{fontSize:9,color:tokens.colors.textSecondary,lineHeight:1.6}}>
                <div>{violetIdentity.axiom?.slice(0,80)}...</div>
                <div style={{marginTop:4,color:tokens.colors.adjudication}}>
                  {violetIdentity.shalom ? '✓ Shalom' : '⚠ Shalom'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom timeline */}
      <div style={{background:'#080C1E',borderTop:`1px solid ${tokens.colors.border}`,
        padding:'8px 16px'}}>
        <div style={{fontSize:9,color:tokens.colors.textSecondary,marginBottom:4}}>
          TIMELINE — Receipts / Commits / Executions
        </div>
        <Timeline events={timeline} />
      </div>
    </div>
  )
}

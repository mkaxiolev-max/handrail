"use client"
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { VoiceOverlay }      from '@/components/VoiceOverlay'
import { OrganismMap }       from '@/components/OrganismMap'
import { EngineRoom }        from '@/components/EngineRoom'
import { ProgramsRuntime }   from '@/components/ProgramsRuntime'
import { GovernanceSpace }   from '@/components/GovernanceSpace'
import { MemorySpace }       from '@/components/MemorySpace'
import { BuildSpace }        from '@/components/BuildSpace'
import { ExecutionSpace }    from '@/components/ExecutionSpace'
import { VoiceSpace }        from '@/components/VoiceSpace'
import { TimelineSpace }     from '@/components/TimelineSpace'
import { OmegaPanel }        from '@/components/OmegaPanel'
import { FounderHome }       from '@/components/FounderHome'
import { VioletLogo, AxiolevWordmark } from '@/components/VioletMark'
import { VioletPanel }       from '@/components/VioletPanel'

// NS_API defaults to ns_api :9001 (local) or env override in Docker/Tauri
const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

type Mode =
  | 'founder'
  | 'organism'
  | 'engine'
  | 'runtime'
  | 'memory'
  | 'governance'
  | 'build'
  | 'execution'
  | 'voice'
  | 'timeline'
  | 'omega'

interface ModeConfig { id: Mode; label: string; color: string; desc: string }

const MODES: ModeConfig[] = [
  { id: 'founder',    label: 'Founder Home',        color: tokens.colors.founder,    desc: 'Priorities, health, open loops' },
  { id: 'organism',   label: 'Living Architecture', color: tokens.colors.violet,     desc: 'Autopoietic organism view' },
  { id: 'engine',     label: 'Engine Room',         color: tokens.colors.handrail,   desc: 'Cognition, adjudication, execution' },
  { id: 'runtime',    label: 'Programs',            color: '#88FFAA',                desc: '10 constitutional programs' },
  { id: 'memory',     label: 'Memory',              color: tokens.colors.alexandria, desc: 'Alexandria ledger + receipts' },
  { id: 'governance', label: 'Governance',          color: tokens.colors.kernel,     desc: 'Never-events, rings, quorum' },
  { id: 'build',      label: 'Build Space',         color: tokens.colors.buildSpace, desc: 'Input → program → dispatch' },
  { id: 'execution',  label: 'Execution',           color: tokens.colors.adjudication, desc: 'Dispatch history, Handrail moat' },
  { id: 'voice',      label: 'Voice',               color: tokens.colors.voice,      desc: 'Sessions, telephony, receipts' },
  { id: 'timeline',   label: 'Timeline',            color: tokens.colors.textSecondary, desc: 'Reality feed, receipted deltas' },
  { id: 'omega',      label: 'Omega',               color: '#4A6FA5',                desc: 'Bounded branch simulation' },
]

export default function Home() {
  const [mode, setMode] = useState<Mode>('founder')
  const [systemState, setSystemState]     = useState<any>(null)
  const [engineData, setEngineData]       = useState<any>(null)
  const [programs, setPrograms]           = useState<any[]>([])
  const [govState, setGovState]           = useState<any>(null)
  const [timeline, setTimeline]           = useState<any[]>([])
  const [violetIdentity, setVioletIdentity] = useState<any>(null)
  const [omegaRuns, setOmegaRuns]         = useState<any>(null)
  const [omegaLatest, setOmegaLatest]     = useState<any>(null)

  const fetchShared = async () => {
    try {
      const [sys, eng, progs, gov, tl, vi, omR] = await Promise.allSettled([
        fetch(`${NS_API}/api/v1/system/state`).then(r => r.json()),
        fetch(`${NS_API}/api/v1/engine/live`).then(r => r.json()),
        fetch(`${NS_API}/api/v1/programs`).then(r => r.json()),
        fetch(`${NS_API}/api/v1/governance/state`).then(r => r.json()),
        fetch(`${NS_API}/api/v1/system/timeline`).then(r => r.json()),
        fetch(`${process.env.NEXT_PUBLIC_NS_URL || 'http://localhost:9000'}/violet/identity`).then(r => r.json()),
        fetch(`${NS_API}/api/v1/omega/runs`).then(r => r.json()),
      ])
      if (sys.status  === 'fulfilled') setSystemState(sys.value)
      if (eng.status  === 'fulfilled') setEngineData(eng.value)
      if (progs.status === 'fulfilled') {
        const p = progs.value
        setPrograms(Array.isArray(p) ? p : (p?.programs || []))
      }
      if (gov.status === 'fulfilled') setGovState(gov.value)
      if (tl.status  === 'fulfilled') setTimeline(Array.isArray(tl.value) ? tl.value : [])
      if (vi.status  === 'fulfilled') setVioletIdentity(vi.value)
      if (omR.status === 'fulfilled') {
        setOmegaRuns(omR.value)
        const first = omR.value?.runs?.[0]
        if (first?.run_id) {
          try {
            const [latest, branches] = await Promise.all([
              fetch(`${NS_API}/api/v1/omega/runs/${first.run_id}`).then(r => r.json()),
              fetch(`${NS_API}/api/v1/omega/runs/${first.run_id}/branches`).then(r => r.json()),
            ])
            setOmegaLatest({ ...latest, branches: branches?.branches || [] })
          } catch {}
        } else {
          setOmegaLatest(null)
        }
      }
    } catch {}
  }

  useEffect(() => {
    fetchShared()
    const id = setInterval(fetchShared, 6000)
    return () => clearInterval(id)
  }, [])

  const currentMode = MODES.find(m => m.id === mode)!
  const shalom = systemState?.services?.some((s: any) => s.service === 'ns' && s.healthy)

  return (
    <div style={{ minHeight: '100vh', background: tokens.colors.bg, display: 'flex', flexDirection: 'column' }}>
      <VoiceOverlay />

      {/* Top bar */}
      <div style={{
        background: '#080C1E', borderBottom: `1px solid ${tokens.colors.border}`,
        padding: '8px 20px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <VioletLogo size={26} />
          <AxiolevWordmark />
          <span style={{ color: tokens.colors.textSecondary, fontSize: 10 }}>NS∞ · Founder Habitat</span>
          <span style={{
            fontSize: 9, padding: '1px 7px',
            background: systemState ? 'rgba(0,255,136,0.08)' : 'rgba(255,255,255,0.04)',
            border: `1px solid ${systemState ? 'rgba(0,255,136,0.25)' : tokens.colors.border}`,
            borderRadius: 3,
            color: systemState ? tokens.colors.healthy : tokens.colors.textSecondary,
          }}>
            {systemState ? '● LIVE' : '○ CONNECTING'}
          </span>
        </div>
        {violetIdentity && (
          <div style={{ fontSize: 9, color: tokens.colors.textSecondary }}>
            <span style={{ color: tokens.colors.violet }}>Violet</span>
            {' '}{violetIdentity.version} · {violetIdentity.shalom ? '✓ Shalom' : '⚠ Shalom'}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left rail */}
        <div style={{
          width: 164, background: '#080C1E', borderRight: `1px solid ${tokens.colors.border}`,
          padding: '12px 6px', display: 'flex', flexDirection: 'column', gap: 2,
          flexShrink: 0, overflowY: 'auto',
        }}>
          {MODES.map(m => (
            <button key={m.id} onClick={() => setMode(m.id)} style={{
              background: mode === m.id ? `${m.color}18` : 'transparent',
              border: `1px solid ${mode === m.id ? m.color + '66' : 'transparent'}`,
              borderRadius: 5, padding: '7px 10px', cursor: 'pointer',
              color: mode === m.id ? m.color : tokens.colors.textSecondary,
              fontSize: 10, textAlign: 'left', transition: 'all 0.15s',
              lineHeight: 1.2,
            }}>{m.label}</button>
          ))}

          <div style={{ marginTop: 'auto', borderTop: `1px solid ${tokens.colors.border}`, paddingTop: 10 }}>
            <div style={{ fontSize: 8, color: tokens.colors.textSecondary, marginBottom: 4, paddingLeft: 4 }}>
              SERVICES
            </div>
            {systemState?.services?.slice(0, 5).map((s: any) => (
              <div key={s.service} style={{
                fontSize: 8, color: s.healthy ? tokens.colors.healthy : tokens.colors.warning,
                paddingLeft: 4, marginBottom: 2,
              }}>
                {s.healthy ? '●' : '○'} {s.service}
              </div>
            )) ?? (
              <div style={{ fontSize: 8, color: tokens.colors.textSecondary, paddingLeft: 4 }}>
                connecting…
              </div>
            )}
          </div>
        </div>

        {/* Center canvas */}
        <div style={{ flex: 1, padding: 16, overflow: 'auto' }}>
          <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ margin: 0, fontSize: 15, color: currentMode.color }}>{currentMode.label}</h2>
            <span style={{ fontSize: 10, color: tokens.colors.textSecondary }}>— {currentMode.desc}</span>
          </div>

          {mode === 'founder'    && <FounderHome />}
          {mode === 'organism'   && <OrganismMap systemState={systemState} />}
          {mode === 'engine'     && <EngineRoom engineData={engineData} programs={programs} />}
          {mode === 'runtime'    && <ProgramsRuntime programs={programs} />}
          {mode === 'memory'     && <MemorySpace />}
          {mode === 'governance' && <GovernanceSpace />}
          {mode === 'build'      && <BuildSpace />}
          {mode === 'execution'  && <ExecutionSpace />}
          {mode === 'voice'      && <VoiceSpace />}
          {mode === 'timeline'   && <TimelineSpace />}
          {mode === 'omega'      && <OmegaPanel omegaRuns={omegaRuns} omegaLatest={omegaLatest} />}
        </div>

        {/* Right panel — System State + Violet */}
        <div style={{
          width: 248, background: '#080C1E', borderLeft: `1px solid ${tokens.colors.border}`,
          padding: 12, overflow: 'auto', flexShrink: 0,
        }}>
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, marginBottom: 10, fontWeight: 700 }}>
            SYSTEM STATE
          </div>
          {systemState ? (
            <div style={{ fontSize: 9 }}>
              <div style={{ color: tokens.colors.adjudication, marginBottom: 3 }}>
                Phase: {systemState.metrics?.phase || 'active'}
              </div>
              {systemState.metrics?.autopoietic_integrity != null && (
                <div style={{ color: tokens.colors.textSecondary, marginBottom: 3 }}>
                  Integrity: {((systemState.metrics.autopoietic_integrity) * 100).toFixed(0)}%
                </div>
              )}
              <div style={{ marginTop: 6 }}>
                {systemState.services?.slice(0, 8).map((s: any) => (
                  <div key={s.service} style={{ color: s.healthy ? tokens.colors.healthy : tokens.colors.warning, marginBottom: 2 }}>
                    {s.healthy ? '●' : '○'} {s.service}
                    {s.latency_ms != null && (
                      <span style={{ color: tokens.colors.textSecondary, marginLeft: 4 }}>
                        {Math.round(s.latency_ms)}ms
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.5 }}>
              Connecting to NS API…
            </div>
          )}

          {violetIdentity && (
            <div style={{
              marginTop: 14, padding: 8, background: '#0D1533', borderRadius: 7,
              border: `1px solid ${tokens.colors.violet}33`,
            }}>
              <div style={{ color: tokens.colors.violet, fontSize: 9, fontWeight: 700, marginBottom: 4 }}>VIOLET</div>
              <div style={{ fontSize: 8, color: tokens.colors.textSecondary, lineHeight: 1.5 }}>
                {violetIdentity.axiom?.slice(0, 90)}…
              </div>
              <div style={{ marginTop: 4, fontSize: 8, color: violetIdentity.shalom ? tokens.colors.healthy : tokens.colors.warning }}>
                {violetIdentity.shalom ? '✓ Shalom' : '⚠ Shalom'}
              </div>
            </div>
          )}

          <div style={{ marginTop: 14, height: 380, overflow: 'hidden' }}>
            <VioletPanel compact={true} />
          </div>
        </div>
      </div>

      {/* Bottom timeline strip */}
      <div style={{
        background: '#080C1E', borderTop: `1px solid ${tokens.colors.border}`,
        padding: '6px 14px', flexShrink: 0,
      }}>
        <div style={{ fontSize: 8, color: tokens.colors.textSecondary, marginBottom: 3 }}>
          REALITY FEED
        </div>
        <div style={{ display: 'flex', gap: 8, overflowX: 'auto' }}>
          {timeline.slice(0, 12).map((e: any, i: number) => (
            <div key={i} style={{
              flexShrink: 0, fontSize: 8, fontFamily: 'monospace',
              color: tokens.colors.textSecondary,
              padding: '2px 8px', background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${tokens.colors.border}`, borderRadius: 3,
            }}>
              {e.event_type} {e.summary?.slice(0, 30)}
            </div>
          ))}
          {!timeline.length && (
            <span style={{ fontSize: 8, color: tokens.colors.textSecondary, opacity: 0.5 }}>
              No timeline events yet
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

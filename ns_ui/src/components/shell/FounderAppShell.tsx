'use client'
import { useState, useEffect, type ReactNode } from 'react'
import { tokens } from '@/lib/design-tokens'
import { VioletLogo, AxiolevWordmark } from '@/components/VioletMark'
import { VioletPanel } from '@/components/VioletPanel'
import { VoiceOverlay } from '@/components/VoiceOverlay'
import { FounderSidebar, type NavMode } from './FounderSidebar'
import { FounderStatusStrip } from './FounderStatusStrip'
import { api } from '@/src/lib/api/client'
import { EP } from '@/src/lib/api/endpoints'

interface SystemState {
  services?: Array<{ service: string; healthy: boolean; latency_ms?: number }>
  metrics?: { phase?: string; autopoietic_integrity?: number }
}

interface VioletIdentity {
  version?: string
  shalom?: boolean
  axiom?: string
}

interface Props {
  children: (mode: NavMode) => ReactNode
  defaultMode?: NavMode
}

export function FounderAppShell({ children, defaultMode = 'founder' }: Props) {
  const [mode, setMode]                   = useState<NavMode>(defaultMode)
  const [systemState, setSystemState]     = useState<SystemState | null>(null)
  const [violetIdentity, setVioletIdentity] = useState<VioletIdentity | null>(null)
  const [timeline, setTimeline]           = useState<unknown[]>([])

  const fetchShared = async () => {
    const [sys, vi, tl] = await Promise.allSettled([
      api.get<SystemState>(EP.system.state()),
      api.get<VioletIdentity>(EP.violet.identity()),
      api.get<unknown[]>(EP.system.timeline()),
    ])
    if (sys.status === 'fulfilled') setSystemState(sys.value)
    if (vi.status  === 'fulfilled') setVioletIdentity(vi.value)
    if (tl.status  === 'fulfilled') setTimeline(Array.isArray(tl.value) ? tl.value : [])
  }

  useEffect(() => {
    fetchShared()
    const id = setInterval(fetchShared, 6000)
    return () => clearInterval(id)
  }, [])

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
        <FounderSidebar
          active={mode}
          onSelect={setMode}
          services={systemState?.services}
        />

        {/* Center canvas */}
        <div style={{ flex: 1, padding: 16, overflow: 'auto' }}>
          {children(mode)}
        </div>

        {/* Right panel */}
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
                {systemState.services?.slice(0, 8).map(s => (
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

      <FounderStatusStrip events={timeline as Array<{ event_type?: string; summary?: string }>} />
    </div>
  )
}

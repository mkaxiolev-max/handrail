'use client'
import { useState, useEffect, useCallback } from 'react'
import { tokens } from '@/lib/design-tokens'
import { api } from '@/src/lib/api/client'
import { subscribeEngineLive, type EngineEvent } from '@/src/lib/sse/engineLive'
import { EP } from '@/src/lib/api/endpoints'

interface EngineSnapshot {
  layers?: Array<{ id: string; name: string; status: string; shalom?: boolean }>
  cognition?: { active_model?: string; decisions?: number }
  adjudication?: { queue_depth?: number; last_op?: string }
  ts?: string
  [key: string]: unknown
}

export function EngineRoomPage() {
  const [snapshot, setSnapshot] = useState<EngineSnapshot | null>(null)
  const [liveEvents, setLiveEvents] = useState<EngineEvent[]>([])
  const [sseConnected, setSseConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSnapshot = useCallback(async () => {
    try {
      const d = await api.get<EngineSnapshot>(EP.engine.live())
      setSnapshot(d)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'fetch error')
    }
  }, [])

  useEffect(() => {
    fetchSnapshot()
    const id = setInterval(fetchSnapshot, 8000)
    return () => clearInterval(id)
  }, [fetchSnapshot])

  useEffect(() => {
    let unsub: (() => void) | null = null
    try {
      unsub = subscribeEngineLive(ev => {
        setSseConnected(true)
        setLiveEvents(prev => [ev, ...prev].slice(0, 40))
      })
    } catch {
      // SSE not available — polling covers it
    }
    return () => unsub?.()
  }, [])

  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16,
        padding: '10px 16px', background: 'rgba(0,255,255,0.04)',
        border: `1px solid ${tokens.colors.handrail}33`, borderRadius: 8,
      }}>
        <span style={{ fontFamily: 'monospace', fontSize: 13, letterSpacing: '0.15em', color: tokens.colors.handrail }}>
          ENGINE ROOM
        </span>
        <span style={{
          fontSize: 9, padding: '2px 8px', borderRadius: 3,
          background: sseConnected ? 'rgba(0,255,136,0.08)' : 'rgba(255,255,255,0.04)',
          border: `1px solid ${sseConnected ? 'rgba(0,255,136,0.3)' : tokens.colors.border}`,
          color: sseConnected ? tokens.colors.healthy : tokens.colors.textSecondary,
        }}>
          {sseConnected ? '● SSE LIVE' : '○ POLLING'}
        </span>
        {error && <span style={{ fontSize: 10, color: tokens.colors.error, fontFamily: 'monospace' }}>{error}</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        {/* L10 Layers */}
        <div style={{ borderRadius: 8, border: `1px solid ${tokens.colors.border}`, background: 'rgba(255,255,255,0.02)', padding: 16 }}>
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 12, letterSpacing: '0.15em' }}>
            COGNITION LAYERS
          </div>
          {snapshot?.layers?.length ? (
            snapshot.layers.map(l => (
              <div key={l.id} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 10px', marginBottom: 4, borderRadius: 5,
                background: l.status === 'active' ? 'rgba(0,255,136,0.05)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${l.status === 'active' ? tokens.colors.healthy + '33' : tokens.colors.border}`,
              }}>
                <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textPrimary }}>{l.name}</span>
                <span style={{ fontSize: 9, color: l.status === 'active' ? tokens.colors.healthy : tokens.colors.warning }}>
                  {l.status}
                </span>
              </div>
            ))
          ) : (
            <pre style={{
              maxHeight: 320, overflow: 'auto', borderRadius: 6,
              border: `1px solid ${tokens.colors.border}`, background: 'rgba(0,0,0,0.3)',
              padding: 10, fontSize: 9, color: '#c0d0ff', fontFamily: 'monospace',
            }}>
              {JSON.stringify(snapshot ?? {}, null, 2)}
            </pre>
          )}
        </div>

        {/* Cognition + Adjudication */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ borderRadius: 8, border: `1px solid ${tokens.colors.border}`, background: 'rgba(255,255,255,0.02)', padding: 16, flex: 1 }}>
            <div style={{ fontSize: 10, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 10, letterSpacing: '0.15em' }}>
              COGNITION
            </div>
            {snapshot?.cognition ? (
              Object.entries(snapshot.cognition).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
                  <span>{k}</span>
                  <span style={{ color: tokens.colors.textPrimary }}>{String(v)}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: 9, color: tokens.colors.textSecondary }}>No cognition data</div>
            )}
          </div>

          <div style={{ borderRadius: 8, border: `1px solid ${tokens.colors.adjudication}33`, background: 'rgba(0,255,136,0.03)', padding: 16, flex: 1 }}>
            <div style={{ fontSize: 10, color: tokens.colors.adjudication, fontWeight: 700, marginBottom: 10, letterSpacing: '0.15em' }}>
              ADJUDICATION
            </div>
            {snapshot?.adjudication ? (
              Object.entries(snapshot.adjudication).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
                  <span>{k}</span>
                  <span style={{ color: tokens.colors.textPrimary }}>{String(v)}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: 9, color: tokens.colors.textSecondary }}>No adjudication data</div>
            )}
          </div>
        </div>
      </div>

      {/* Live event stream */}
      <div style={{ borderRadius: 8, border: `1px solid ${tokens.colors.border}`, background: 'rgba(255,255,255,0.02)', padding: 16 }}>
        <div style={{ fontSize: 10, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 10, letterSpacing: '0.15em' }}>
          LIVE STREAM ({liveEvents.length} events)
        </div>
        {liveEvents.length === 0 ? (
          <div style={{ fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.6, fontFamily: 'monospace' }}>
            Waiting for engine events…
          </div>
        ) : (
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {liveEvents.map((ev, i) => (
              <div key={i} style={{
                display: 'flex', gap: 10, padding: '4px 0',
                borderBottom: `1px solid ${tokens.colors.border}`,
              }}>
                <span style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.adjudication, flexShrink: 0 }}>
                  {ev.type}
                </span>
                <span style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary }}>
                  {ev.layer && `[${ev.layer}] `}{ev.summary ?? ''}
                </span>
                {ev.ts && (
                  <span style={{ fontFamily: 'monospace', fontSize: 8, color: tokens.colors.textSecondary, opacity: 0.5, marginLeft: 'auto', flexShrink: 0 }}>
                    {String(ev.ts).slice(11, 19)}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

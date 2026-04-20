'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { isStale } from '@/lib/viewmodels'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

function StaleBadge() {
  return (
    <span style={{
      fontSize: 8, padding: '1px 5px',
      background: 'rgba(255,170,0,0.15)', border: '1px solid rgba(255,170,0,0.4)',
      borderRadius: 3, color: '#FFAA00',
    }}>STALE</span>
  )
}

const MODE_COLORS: Record<string, string> = {
  ring5_pending: tokens.colors.warning,
  operational:   tokens.colors.healthy,
  building:      tokens.colors.violet,
  unknown:       tokens.colors.textSecondary,
}

function SessionCard({ s }: { s: any }) {
  const active = ['speaking', 'gathering', 'processing'].includes(s.status)
  return (
    <div style={{
      padding: '8px 12px', borderRadius: 6, marginBottom: 6,
      background: active ? 'rgba(0,204,255,0.08)' : 'rgba(255,255,255,0.03)',
      border: `1px solid ${active ? tokens.colors.voice + '44' : tokens.colors.border}`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 10, color: active ? tokens.colors.voice : tokens.colors.textSecondary, fontWeight: 700 }}>
          {active ? '📞 ACTIVE' : '○ IDLE'}
        </span>
        <span style={{ fontSize: 9, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>
          {s.channel || 'voice'}
        </span>
      </div>
      {s.last_input && (
        <div style={{ fontSize: 9, color: tokens.colors.textSecondary, fontStyle: 'italic' }}>
          "{s.last_input.slice(0, 80)}"
        </div>
      )}
      {s.duration_s != null && (
        <div style={{ fontSize: 8, color: tokens.colors.textSecondary, marginTop: 2 }}>
          {Math.floor(s.duration_s / 60)}m {s.duration_s % 60}s
        </div>
      )}
    </div>
  )
}

function ReceiptRow({ r }: { r: any }) {
  const ts = r.timestamp ? new Date(r.timestamp).toLocaleTimeString('en-US', { hour12: false }) : '—'
  return (
    <div style={{
      display: 'flex', gap: 8, padding: '4px 8px',
      borderBottom: `1px solid ${tokens.colors.border}`, alignItems: 'center',
    }}>
      <span style={{ fontSize: 8, color: tokens.colors.adjudication, minWidth: 30, fontFamily: 'monospace' }}>
        {r.receipt_type?.slice(0, 10) || 'RCPT'}
      </span>
      <span style={{ fontSize: 9, color: tokens.colors.textPrimary, flex: 1 }}>
        {r.op || r.receipt_id?.slice(0, 24) || '—'}
      </span>
      <span style={{ fontSize: 8, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>{ts}</span>
    </div>
  )
}

export function VoiceSpace() {
  const [data, setData] = useState<any>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/voice`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setData(d)
      setFetchTs(new Date().toISOString())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    }
  }

  useEffect(() => { load(); const id = setInterval(load, 6000); return () => clearInterval(id) }, [])

  const stale = isStale(fetchTs ?? undefined, 15_000)
  const modeColor = MODE_COLORS[data?.mode ?? 'unknown'] ?? tokens.colors.textSecondary

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>

      {/* Status header */}
      <div style={{
        gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 12,
        padding: '8px 14px', background: '#080C1E', borderRadius: 8,
        border: `1px solid ${tokens.colors.voice}33`,
      }}>
        <span style={{ fontSize: 11, color: tokens.colors.voice, fontWeight: 700 }}>VOICE</span>
        {stale && <StaleBadge />}
        {data ? (
          <>
            <span style={{
              fontSize: 9, padding: '2px 8px',
              background: `${modeColor}22`, border: `1px solid ${modeColor}44`,
              borderRadius: 3, color: modeColor, textTransform: 'uppercase',
            }}>{data.mode}</span>
            <span style={{ fontSize: 10, color: data.shalom ? tokens.colors.healthy : tokens.colors.error }}>
              {data.shalom ? '✓ Shalom' : '✗ Shalom'}
            </span>
            <span style={{ fontSize: 10, color: tokens.colors.textSecondary }}>
              {data.session_count} session{data.session_count !== 1 ? 's' : ''}
            </span>
            <span style={{ marginLeft: 'auto', fontSize: 9, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>
              {data.telephony_number}
            </span>
          </>
        ) : error ? (
          <span style={{ fontSize: 10, color: tokens.colors.error }}>{error}</span>
        ) : (
          <span style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>connecting…</span>
        )}
      </div>

      {/* Sessions */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.voice}33`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.voice, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          SESSIONS ({data?.session_count ?? 0})
        </div>
        {data?.sessions?.length ? (
          data.sessions.slice(0, 5).map((s: any, i: number) => <SessionCard key={i} s={s} />)
        ) : (
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>No active sessions</div>
        )}

        {data?.identity && (
          <div style={{
            marginTop: 12, padding: '8px 10px',
            background: 'rgba(0,212,255,0.06)', borderRadius: 6,
            border: `1px solid ${tokens.colors.violet}33`,
          }}>
            <div style={{ fontSize: 9, color: tokens.colors.violet, fontWeight: 700, marginBottom: 4 }}>VIOLET IDENTITY</div>
            <div style={{ fontSize: 9, color: tokens.colors.textSecondary, lineHeight: 1.5 }}>
              {data.identity.axiom?.slice(0, 100)}…
            </div>
          </div>
        )}
      </div>

      {/* Voice receipts */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.adjudication}33`, borderRadius: 8, padding: 14 }}>
        <div style={{ color: tokens.colors.adjudication, fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
          VOICE RECEIPTS
        </div>
        {data?.voice_receipts?.length ? (
          data.voice_receipts.map((r: any, i: number) => <ReceiptRow key={i} r={r} />)
        ) : (
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>No voice receipts yet</div>
        )}
      </div>

      {/* ISR + governance mode */}
      <div style={{ gridColumn: '1 / -1', background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 9, color: tokens.colors.textSecondary, marginBottom: 4 }}>ISR SUMMARY</div>
            <div style={{ fontSize: 10, color: tokens.colors.textPrimary, lineHeight: 1.5 }}>
              {data?.isr_summary || (error ? 'API unreachable' : 'Loading…')}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 9, color: tokens.colors.textSecondary, marginBottom: 4 }}>GOVERNANCE MODE</div>
            <div style={{ fontSize: 11, color: data?.governance_mode === 'founder' ? tokens.colors.healthy : tokens.colors.warning, fontWeight: 700 }}>
              {data?.governance_mode?.toUpperCase() ?? '—'}
            </div>
            <div style={{ fontSize: 9, color: tokens.colors.textSecondary, marginTop: 4 }}>
              Exec: {data?.execution_available ? '⚡ ready' : '⚠ unavail'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { isStale } from '@/lib/viewmodels'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

const TYPE_COLORS: Record<string, string> = {
  failure:      '#FF3333',
  VOICE:        '#00CCFF',
  CHAT_QUICK:   '#6B00FF',
  VIOLET_CHAT:  '#6B00FF',
  receipt:      '#00FF88',
  boot:         '#FF6B00',
  CANON:        '#FFFF00',
  OP_DISPATCH:  '#00FFFF',
}

function typeColor(t: string): string {
  return TYPE_COLORS[t] || tokens.colors.textSecondary
}

function EventRow({ e, selected, onClick }: { e: any; selected: boolean; onClick: () => void }) {
  const ts = e.ts ? new Date(e.ts).toLocaleTimeString('en-US', { hour12: false }) : '—'
  const c = typeColor(e.event_type)
  const isFailure = e.event_type === 'failure'

  return (
    <div onClick={onClick} style={{
      display: 'flex', gap: 8, padding: '6px 10px',
      borderBottom: `1px solid ${tokens.colors.border}`,
      background: selected ? `${c}11` : isFailure ? 'rgba(255,51,51,0.04)' : 'transparent',
      cursor: 'pointer', alignItems: 'center',
      borderLeft: selected ? `3px solid ${c}` : '3px solid transparent',
    }}>
      <span style={{ fontSize: 8, color: c, minWidth: 60, fontFamily: 'monospace', textTransform: 'uppercase' }}>
        {e.event_type?.slice(0, 12)}
      </span>
      <span style={{ fontSize: 10, color: isFailure ? '#FF8888' : tokens.colors.textPrimary, flex: 1, lineHeight: 1.3 }}>
        {e.summary}
      </span>
      <span style={{ fontSize: 8, color: tokens.colors.textSecondary, fontFamily: 'monospace', flexShrink: 0 }}>
        {ts}
      </span>
    </div>
  )
}

export function TimelineSpace() {
  const [data, setData] = useState<any>(null)
  const [selected, setSelected] = useState<any>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('')

  const load = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/timeline?limit=100`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setData(d)
      setFetchTs(new Date().toISOString())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    }
  }

  useEffect(() => { load(); const id = setInterval(load, 10000); return () => clearInterval(id) }, [])

  const stale = isStale(fetchTs ?? undefined, 25_000)
  const events: any[] = data?.events ?? []
  const filtered = filter
    ? events.filter(e =>
        e.summary?.toLowerCase().includes(filter.toLowerCase()) ||
        e.event_type?.toLowerCase().includes(filter.toLowerCase())
      )
    : events

  return (
    <div style={{ display: 'flex', gap: 12, height: '100%', minHeight: 500 }}>
      {/* Event list */}
      <div style={{
        flex: 1, background: '#0D1533',
        border: `1px solid ${tokens.colors.border}`, borderRadius: 8, overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Header */}
        <div style={{
          padding: '10px 14px', borderBottom: `1px solid ${tokens.colors.border}`,
          display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0,
        }}>
          <span style={{ fontSize: 11, color: '#88CCFF', fontWeight: 700 }}>REALITY FEED</span>
          {stale && <span style={{ fontSize: 8, color: '#FFAA00' }}>STALE</span>}
          {data?.has_failures && (
            <span style={{ fontSize: 8, color: '#FF3333', padding: '1px 5px', background: 'rgba(255,51,51,0.1)', borderRadius: 3 }}>
              ⚠ FAILURES
            </span>
          )}
          <span style={{ marginLeft: 'auto', fontSize: 9, color: tokens.colors.textSecondary }}>
            {filtered.length} events
          </span>
        </div>

        {/* Filter */}
        <div style={{ padding: '6px 10px', borderBottom: `1px solid ${tokens.colors.border}`, flexShrink: 0 }}>
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="filter events…"
            style={{
              width: '100%', background: 'rgba(255,255,255,0.04)',
              border: `1px solid ${tokens.colors.border}`, borderRadius: 4,
              padding: '4px 8px', color: tokens.colors.textPrimary,
              fontSize: 10, fontFamily: 'monospace', outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Events */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {error ? (
            <div style={{ padding: 14, fontSize: 10, color: tokens.colors.error }}>{error}</div>
          ) : filtered.length ? (
            filtered.map((e: any, i: number) => (
              <EventRow key={i} e={e} selected={selected?.id === e.id} onClick={() => setSelected(e)} />
            ))
          ) : (
            <div style={{ padding: 14, fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>
              {data ? 'No events match filter' : 'Loading timeline…'}
            </div>
          )}
        </div>
      </div>

      {/* Detail panel */}
      <div style={{
        width: 280, background: '#0D1533',
        border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14,
        flexShrink: 0,
      }}>
        <div style={{ fontSize: 11, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 12 }}>
          EVENT DETAIL
        </div>
        {selected ? (
          <div style={{ fontSize: 10, lineHeight: 1.6 }}>
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: typeColor(selected.event_type), fontWeight: 700 }}>
                {selected.event_type}
              </span>
            </div>
            <div style={{ color: tokens.colors.textPrimary, marginBottom: 8 }}>{selected.summary}</div>
            {selected.op && (
              <div style={{ marginBottom: 6 }}>
                <span style={{ color: tokens.colors.textSecondary }}>op: </span>
                <span style={{ color: tokens.colors.textPrimary, fontFamily: 'monospace', fontSize: 9 }}>{selected.op}</span>
              </div>
            )}
            {selected.receipt_id && (
              <div style={{ marginBottom: 6 }}>
                <span style={{ color: tokens.colors.textSecondary }}>receipt: </span>
                <span style={{ color: tokens.colors.adjudication, fontFamily: 'monospace', fontSize: 9 }}>
                  {selected.receipt_id.slice(0, 24)}…
                </span>
              </div>
            )}
            {selected.ts && (
              <div>
                <span style={{ color: tokens.colors.textSecondary }}>ts: </span>
                <span style={{ color: tokens.colors.textPrimary, fontFamily: 'monospace', fontSize: 9 }}>
                  {new Date(selected.ts).toISOString()}
                </span>
              </div>
            )}
            <div style={{ marginTop: 10 }}>
              <span style={{ fontSize: 8, padding: '2px 6px',
                background: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.2)',
                borderRadius: 3, color: tokens.colors.adjudication }}>
                {selected.source_class}
              </span>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: 10, color: tokens.colors.textSecondary, opacity: 0.5 }}>
            Click an event to inspect
          </div>
        )}
      </div>
    </div>
  )
}

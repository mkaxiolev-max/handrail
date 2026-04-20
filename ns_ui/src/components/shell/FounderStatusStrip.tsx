'use client'
import { tokens } from '@/lib/design-tokens'

interface TimelineEvent {
  event_type?: string
  summary?: string
  [key: string]: unknown
}

interface Props {
  events?: TimelineEvent[]
}

export function FounderStatusStrip({ events = [] }: Props) {
  return (
    <div style={{
      background: '#080C1E', borderTop: `1px solid ${tokens.colors.border}`,
      padding: '6px 14px', flexShrink: 0,
    }}>
      <div style={{ fontSize: 8, color: tokens.colors.textSecondary, marginBottom: 3 }}>
        REALITY FEED
      </div>
      <div style={{ display: 'flex', gap: 8, overflowX: 'auto' }}>
        {events.slice(0, 12).map((e, i) => (
          <div key={i} style={{
            flexShrink: 0, fontSize: 8, fontFamily: 'monospace',
            color: tokens.colors.textSecondary,
            padding: '2px 8px', background: 'rgba(255,255,255,0.03)',
            border: `1px solid ${tokens.colors.border}`, borderRadius: 3,
          }}>
            {e.event_type} {String(e.summary ?? '').slice(0, 30)}
          </div>
        ))}
        {!events.length && (
          <span style={{ fontSize: 8, color: tokens.colors.textSecondary, opacity: 0.5 }}>
            No timeline events yet
          </span>
        )}
      </div>
    </div>
  )
}

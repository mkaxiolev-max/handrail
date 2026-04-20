'use client'
import { tokens } from '@/lib/design-tokens'

export type NavMode =
  | 'founder' | 'organism' | 'engine' | 'runtime'
  | 'memory'  | 'governance' | 'build' | 'execution'
  | 'voice'   | 'timeline'  | 'omega'

interface NavItem { id: NavMode; label: string; color: string }

export const NAV_ITEMS: NavItem[] = [
  { id: 'founder',    label: 'Founder Home',        color: tokens.colors.founder },
  { id: 'organism',   label: 'Living Architecture', color: tokens.colors.violet },
  { id: 'engine',     label: 'Engine Room',         color: tokens.colors.handrail },
  { id: 'runtime',    label: 'Programs',            color: '#88FFAA' },
  { id: 'memory',     label: 'Memory',              color: tokens.colors.alexandria },
  { id: 'governance', label: 'Governance',          color: tokens.colors.kernel },
  { id: 'build',      label: 'Build Space',         color: tokens.colors.buildSpace },
  { id: 'execution',  label: 'Execution',           color: tokens.colors.adjudication },
  { id: 'voice',      label: 'Voice',               color: tokens.colors.voice },
  { id: 'timeline',   label: 'Timeline',            color: tokens.colors.textSecondary },
  { id: 'omega',      label: 'Omega',               color: '#4A6FA5' },
]

interface Props {
  active: NavMode
  onSelect: (m: NavMode) => void
  services?: Array<{ service: string; healthy: boolean }>
}

export function FounderSidebar({ active, onSelect, services }: Props) {
  return (
    <div style={{
      width: 164, background: '#080C1E', borderRight: `1px solid ${tokens.colors.border}`,
      padding: '12px 6px', display: 'flex', flexDirection: 'column', gap: 2,
      flexShrink: 0, overflowY: 'auto',
    }}>
      {NAV_ITEMS.map(item => (
        <button
          key={item.id}
          onClick={() => onSelect(item.id)}
          style={{
            background: active === item.id ? `${item.color}18` : 'transparent',
            border: `1px solid ${active === item.id ? item.color + '66' : 'transparent'}`,
            borderRadius: 5, padding: '7px 10px', cursor: 'pointer',
            color: active === item.id ? item.color : tokens.colors.textSecondary,
            fontSize: 10, textAlign: 'left', transition: 'all 0.15s', lineHeight: 1.2,
          }}
        >
          {item.label}
        </button>
      ))}

      <div style={{ marginTop: 'auto', borderTop: `1px solid ${tokens.colors.border}`, paddingTop: 10 }}>
        <div style={{ fontSize: 8, color: tokens.colors.textSecondary, marginBottom: 4, paddingLeft: 4 }}>
          SERVICES
        </div>
        {services?.slice(0, 5).map(s => (
          <div key={s.service} style={{
            fontSize: 8,
            color: s.healthy ? tokens.colors.healthy : tokens.colors.warning,
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
  )
}

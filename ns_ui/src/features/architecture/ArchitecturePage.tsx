'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { api } from '@/src/lib/api/client'
import { EP } from '@/src/lib/api/endpoints'

type ServiceStatus = 'live' | 'down' | 'unknown'

interface Service {
  id: string
  label: string
  status: ServiceStatus
  endpoint: string
  latency_ms?: number
  payload?: unknown
}

interface OverviewData {
  system_state?: {
    state?: string
    boot_mode?: string
    git_commit?: string
    degraded?: string[]
  }
  captured_at?: string
  services?: Service[]
  providers?: Array<{ id: string; status: string; model?: string; model_count?: number; endpoint?: string }>
  memory?: { atoms_total?: number; receipt_files?: number; alexandria_mounted?: boolean; latest_receipt?: string }
  execution?: { status?: string; payload?: unknown }
  governance?: { hic?: { status?: string }; pdp?: { status?: string } }
  voice?: { status?: string; sessions_count?: number; violet?: unknown }
  body?: { gateway?: { status?: string }; adapter?: { status?: string } }
  omega?: { status?: string; runs_count?: number; health?: unknown }
}

const TONE: Record<ServiceStatus | string, string> = {
  live:    '#00FF88',
  down:    '#FF3333',
  unknown: '#FFAA00',
}

function StatusPill({ value }: { value: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      borderRadius: 4, padding: '2px 8px', fontSize: 10,
      fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.05em',
      background: `${TONE[value] ?? TONE.unknown}18`,
      border: `1px solid ${TONE[value] ?? TONE.unknown}44`,
      color: TONE[value] ?? TONE.unknown,
    }}>
      {value}
    </span>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      borderRadius: 8, border: `1px solid ${tokens.colors.border}`,
      background: 'rgba(255,255,255,0.02)', padding: 16, marginBottom: 12,
    }}>
      <div style={{ fontSize: 10, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 10, letterSpacing: '0.15em' }}>
        {title.toUpperCase()}
      </div>
      {children}
    </div>
  )
}

export function ArchitecturePage() {
  const [data, setData] = useState<OverviewData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  const fetch_ = async () => {
    try {
      const d = await api.get<OverviewData>(EP.organism.overview())
      setData(d)
      setError(null)
      if (!selected && d.services?.length) setSelected(d.services[0].id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'fetch error')
    }
  }

  useEffect(() => {
    fetch_()
    const id = setInterval(fetch_, 10_000)
    return () => clearInterval(id)
  }, [])

  if (!data && !error) {
    return <div style={{ fontSize: 11, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>Loading organism telemetry…</div>
  }

  const selectedSvc = data?.services?.find(s => s.id === selected) ?? data?.services?.[0] ?? null

  return (
    <div>
      {/* Header */}
      <div style={{
        borderRadius: 10, border: `1px solid ${tokens.colors.violet}33`,
        background: 'linear-gradient(90deg, rgba(0,0,0,0) 0%, rgba(10,14,39,0.4) 100%)',
        padding: 20, marginBottom: 16,
        display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontFamily: 'monospace', fontSize: 14, letterSpacing: '0.2em', color: tokens.colors.violet }}>
          ORGANISM
        </span>
        <StatusPill value={(data?.system_state?.state || 'unknown').toLowerCase()} />
        <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
          boot: {data?.system_state?.boot_mode || 'unknown'}
        </span>
        <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
          commit: {data?.system_state?.git_commit?.slice(0, 8) || 'unknown'}
        </span>
        <span style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.6 }}>
          {data?.captured_at || ''}
        </span>
        {error && <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.error }}>{error}</span>}
        {(data?.system_state?.degraded?.length ?? 0) > 0 && (
          <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.warning }}>
            degraded: {data!.system_state!.degraded!.join(', ')}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 12, marginBottom: 12 }}>
        <Card title="Services">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
            {(data?.services || []).map(svc => (
              <button
                key={svc.id}
                onClick={() => setSelected(svc.id)}
                style={{
                  borderRadius: 6, padding: 12, textAlign: 'left', cursor: 'pointer',
                  background: selectedSvc?.id === svc.id ? `${tokens.colors.violet}10` : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${selectedSvc?.id === svc.id ? tokens.colors.violet + '44' : tokens.colors.border}`,
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, gap: 8 }}>
                  <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textPrimary, letterSpacing: '0.05em' }}>
                    {svc.label}
                  </span>
                  <StatusPill value={svc.status} />
                </div>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary }}>{svc.endpoint}</div>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary, marginTop: 6 }}>
                  latency: {svc.latency_ms ?? 'n/a'} ms
                </div>
              </button>
            ))}
          </div>
        </Card>

        <Card title="Drilldown">
          {selectedSvc ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10, gap: 8 }}>
                <div>
                  <div style={{ fontFamily: 'monospace', fontSize: 11, color: tokens.colors.textPrimary }}>{selectedSvc.label}</div>
                  <div style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary }}>{selectedSvc.endpoint}</div>
                </div>
                <StatusPill value={selectedSvc.status} />
              </div>
              <pre style={{
                maxHeight: 320, overflow: 'auto', borderRadius: 6,
                border: `1px solid ${tokens.colors.border}`, background: 'rgba(0,0,0,0.3)',
                padding: 12, fontSize: 10, color: '#c0d0ff', fontFamily: 'monospace',
              }}>
                {JSON.stringify(selectedSvc.payload ?? {}, null, 2)}
              </pre>
            </div>
          ) : (
            <div style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>No live service detail yet.</div>
          )}
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
        <Card title="Providers">
          {(data?.providers || []).map(p => (
            <div key={p.id} style={{
              borderRadius: 6, border: `1px solid ${tokens.colors.border}`,
              background: 'rgba(255,255,255,0.02)', padding: 12, marginBottom: 8,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textPrimary, letterSpacing: '0.05em' }}>
                  {p.id}
                </span>
                <StatusPill value={p.status} />
              </div>
              <div style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary }}>model: {p.model || 'unknown'}</div>
              <div style={{ fontFamily: 'monospace', fontSize: 9, color: tokens.colors.textSecondary }}>{p.endpoint}</div>
            </div>
          ))}
        </Card>

        <Card title="Memory">
          {[
            ['atoms', String(data?.memory?.atoms_total ?? 'unknown')],
            ['receipts', String(data?.memory?.receipt_files ?? 'unknown')],
            ['alexandria', data?.memory?.alexandria_mounted ? 'mounted' : 'missing'],
            ['latest receipt', data?.memory?.latest_receipt || 'none'],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
              <span>{k}</span><span style={{ color: tokens.colors.textPrimary }}>{v}</span>
            </div>
          ))}
        </Card>

        <Card title="Execution">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>handrail</span>
            <StatusPill value={data?.execution?.status || 'unknown'} />
          </div>
        </Card>

        <Card title="Governance">
          {[
            ['hic', data?.governance?.hic?.status || 'unknown'],
            ['pdp', data?.governance?.pdp?.status || 'unknown'],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
              <span>{k}</span><StatusPill value={v} />
            </div>
          ))}
        </Card>

        <Card title="Voice">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
            <span>violet</span><StatusPill value={data?.voice?.status || 'unknown'} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
            <span>sessions</span><span>{data?.voice?.sessions_count ?? 'unknown'}</span>
          </div>
        </Card>

        <Card title="Omega">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
            <span>omega</span><StatusPill value={data?.omega?.status || 'unknown'} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'monospace', fontSize: 10, color: tokens.colors.textSecondary }}>
            <span>runs</span><span>{data?.omega?.runs_count ?? 'unknown'}</span>
          </div>
        </Card>
      </div>
    </div>
  )
}

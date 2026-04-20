'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'
import { isStale } from '@/lib/viewmodels'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'

function ClassCard({ label, count, description, color }: { label: string; count: number; description: string; color: string }) {
  return (
    <div style={{
      padding: 12, background: `${color}08`,
      border: `1px solid ${color}33`, borderRadius: 7,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 10, color, fontWeight: 700, textTransform: 'uppercase' }}>{label}</span>
        <span style={{ fontSize: 13, color, fontWeight: 700 }}>{count}</span>
      </div>
      <div style={{ fontSize: 8, color: tokens.colors.textSecondary, lineHeight: 1.4 }}>{description}</div>
    </div>
  )
}

export function MemorySpace() {
  const [data, setData] = useState<any>(null)
  const [fetchTs, setFetchTs] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const r = await fetch(`${NS_API}/api/v1/ui/memory`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setData(await r.json())
      setFetchTs(new Date().toISOString())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    }
  }

  useEffect(() => { load(); const id = setInterval(load, 12000); return () => clearInterval(id) }, [])

  const stale = isStale(fetchTs ?? undefined, 30_000)
  const sub = data?.substrate

  const CLASS_COLORS: Record<string, string> = {
    receipt:   tokens.colors.adjudication,
    canonical: tokens.colors.alexandria,
    superseded:'#88CCFF',
    unresolved: tokens.colors.error,
  }

  const byType = data?.by_type ?? {}
  const topTypes = Object.entries(byType)
    .sort((a: any, b: any) => b[1] - a[1])
    .slice(0, 10)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      {/* Alexandria mount status */}
      <div style={{
        gridColumn: '1 / -1', padding: '8px 14px',
        background: data?.alexandria_mounted ? 'rgba(255,255,0,0.04)' : 'rgba(255,51,51,0.06)',
        border: `1px solid ${data?.alexandria_mounted ? tokens.colors.alexandria + '44' : tokens.colors.error + '44'}`,
        borderRadius: 8, display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 11, color: tokens.colors.alexandria, fontWeight: 700 }}>ALEXANDRIA</span>
        {stale && <span style={{ fontSize: 8, color: '#FFAA00' }}>STALE</span>}
        <span style={{
          fontSize: 9, padding: '1px 7px',
          background: data?.alexandria_mounted ? 'rgba(255,255,0,0.08)' : 'rgba(255,51,51,0.1)',
          border: `1px solid ${data?.alexandria_mounted ? 'rgba(255,255,0,0.3)' : 'rgba(255,51,51,0.3)'}`,
          borderRadius: 3, color: data?.alexandria_mounted ? tokens.colors.alexandria : tokens.colors.error,
        }}>{data?.alexandria_mounted ? '● MOUNTED' : '○ ABSENT'}</span>
        {sub && (
          <>
            <span style={{ fontSize: 9, color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>
              {data.alexandria_path}
            </span>
            <span style={{ fontSize: 9, color: tokens.colors.textSecondary }}>
              {sub.receipt_files} receipt files · {sub.ledger_files} ledger files
            </span>
          </>
        )}
        {error && <span style={{ fontSize: 9, color: tokens.colors.error }}>{error}</span>}
        {sub?.integrity_ok != null && (
          <span style={{
            marginLeft: 'auto', fontSize: 9, padding: '1px 6px',
            background: sub.integrity_ok ? 'rgba(0,255,136,0.08)' : 'rgba(255,51,51,0.08)',
            border: `1px solid ${sub.integrity_ok ? 'rgba(0,255,136,0.2)' : 'rgba(255,51,51,0.2)'}`,
            borderRadius: 3, color: sub.integrity_ok ? tokens.colors.healthy : tokens.colors.error,
          }}>integrity {sub.integrity_ok ? 'ok' : 'FAIL'}</span>
        )}
      </div>

      {/* Memory class cards */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
        <div style={{ fontSize: 11, color: tokens.colors.alexandria, fontWeight: 700, marginBottom: 12 }}>
          MEMORY CLASSES
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {(data?.memory_classes ?? []).map((mc: any) => (
            <ClassCard
              key={mc.class} label={mc.class} count={mc.count}
              description={mc.description} color={CLASS_COLORS[mc.class] ?? tokens.colors.textSecondary}
            />
          ))}
        </div>
      </div>

      {/* Receipt breakdown */}
      <div style={{ background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8, padding: 14 }}>
        <div style={{ fontSize: 11, color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: 10 }}>
          BY TYPE
        </div>
        {topTypes.length ? (
          <div>
            {topTypes.map(([type, count]) => (
              <div key={type} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '3px 0', borderBottom: `1px solid ${tokens.colors.border}`,
              }}>
                <span style={{ fontSize: 9, color: tokens.colors.textPrimary, fontFamily: 'monospace' }}>{type}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    height: 4, borderRadius: 2,
                    width: Math.max(4, Math.min(80, ((count as number) / Math.max(...Object.values(byType) as number[])) * 80)),
                    background: tokens.colors.adjudication + '88',
                  }} />
                  <span style={{ fontSize: 9, color: tokens.colors.adjudication, minWidth: 24, textAlign: 'right' }}>
                    {count as number}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: 9, color: tokens.colors.textSecondary, opacity: 0.5 }}>
            {error ? 'Cannot reach API' : 'No receipts yet'}
          </div>
        )}
      </div>

      {/* Latest receipt */}
      {sub?.latest_receipt_id && (
        <div style={{
          gridColumn: '1 / -1', padding: '8px 14px',
          background: '#0D1533', border: `1px solid ${tokens.colors.border}`, borderRadius: 8,
        }}>
          <span style={{ fontSize: 9, color: tokens.colors.textSecondary }}>Latest receipt: </span>
          <span style={{ fontSize: 9, color: tokens.colors.adjudication, fontFamily: 'monospace' }}>
            {sub.latest_receipt_id}
          </span>
          {sub.latest_ts && (
            <span style={{ fontSize: 9, color: tokens.colors.textSecondary, marginLeft: 12 }}>
              {new Date(sub.latest_ts).toLocaleString()}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

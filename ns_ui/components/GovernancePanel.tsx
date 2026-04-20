'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'

const NS_URL = process.env.NEXT_PUBLIC_NS_URL || 'http://localhost:9000'

const PRESSURE_COLORS: Record<string, string> = {
  ring5_pending: tokens.colors.warning,
  operational:   tokens.colors.healthy,
  building:      tokens.colors.violet,
}

function VioletStatusCard() {
  const [status, setStatus] = useState<any>(null)

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const r = await fetch(`${NS_URL}/violet/status`)
        setStatus(await r.json())
      } catch { /* silent */ }
    }
    fetch_()
    const id = setInterval(fetch_, 5000)
    return () => clearInterval(id)
  }, [])

  const mode     = status?.violet_mode ?? 'unknown'
  const modeColor = PRESSURE_COLORS[mode] ?? tokens.colors.textSecondary
  const thread   = (status?.active_thread ?? '—').slice(0, 60)
  const receipt  = (status?.last_receipt ?? '—').slice(0, 20)
  const shalom   = status?.shalom ?? false
  const execOk   = status?.execution_available ?? false
  const summary  = status?.isr_summary ?? 'Awaiting ISR...'

  return (
    <div style={{
      background: '#0A0E27',
      border: `1px solid ${modeColor}55`,
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ color: tokens.colors.violet, fontSize: 11, fontWeight: 'bold' }}>VIOLET STATUS</span>
        <span style={{
          background: modeColor + '33',
          color: modeColor,
          border: `1px solid ${modeColor}66`,
          borderRadius: 4,
          padding: '1px 7px',
          fontSize: 10,
          fontWeight: 'bold',
          textTransform: 'uppercase' as const,
        }}>{mode}</span>
        <span style={{ marginLeft: 'auto', fontSize: 10, color: shalom ? tokens.colors.healthy : tokens.colors.error }}>
          {shalom ? '✓ SHALOM' : '✗ SHALOM'}
        </span>
      </div>

      <div style={{ fontSize: 9, color: tokens.colors.textSecondary, marginBottom: 4 }}>
        <span style={{ color: tokens.colors.textPrimary }}>Thread: </span>{thread || '—'}
      </div>
      <div style={{ fontSize: 9, color: tokens.colors.textSecondary, marginBottom: 6 }}>
        <span style={{ color: tokens.colors.textPrimary }}>Receipt: </span>
        <span style={{ fontFamily: 'monospace', color: tokens.colors.alexandria }}>{receipt}</span>
      </div>

      <div style={{ fontSize: 9, color: tokens.colors.textSecondary, borderTop: `1px solid ${tokens.colors.border}`, paddingTop: 6 }}>
        {summary}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
        <span style={{
          fontSize: 9,
          color: execOk ? tokens.colors.healthy : tokens.colors.warning,
          border: `1px solid ${(execOk ? tokens.colors.healthy : tokens.colors.warning) + '44'}`,
          borderRadius: 3,
          padding: '1px 5px',
        }}>
          {execOk ? '⚡ exec ready' : '⚠ exec unavail'}
        </span>
      </div>
    </div>
  )
}

export function GovernancePanel({govState}: {govState?: any}) {
  const NEVER_EVENTS = ['NE1','NE2','NE3','NE4','NE5','NE6','NE7']
  const RINGS = ['Ring 1','Ring 2','Ring 3','Ring 4','Ring 5']
  const ringStatus = [true,true,true,true,false]

  return (
    <div>
      <VioletStatusCard />
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
        <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.kernel}33`,borderRadius:8,padding:12}}>
          <div style={{color:tokens.colors.kernel,fontSize:11,fontWeight:'bold',marginBottom:10}}>NEVER-EVENTS (NE1-NE7)</div>
          {NEVER_EVENTS.map(ne => (
            <div key={ne} style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
              <span style={{color:tokens.colors.healthy,fontSize:10}}>✓</span>
              <span style={{fontSize:10,color:tokens.colors.textSecondary}}>{ne}: Active</span>
            </div>
          ))}
        </div>
        <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.adjudication}33`,borderRadius:8,padding:12}}>
          <div style={{color:tokens.colors.adjudication,fontSize:11,fontWeight:'bold',marginBottom:10}}>RING STATUS</div>
          {RINGS.map((ring,i) => (
            <div key={ring} style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
              <span style={{color: ringStatus[i] ? tokens.colors.healthy : tokens.colors.warning}}>
                {ringStatus[i] ? '✅' : '⏳'}
              </span>
              <span style={{fontSize:10,color:tokens.colors.textSecondary}}>{ring}</span>
              {i===4 && <span style={{fontSize:9,color:tokens.colors.warning}}>← Revenue Gate</span>}
            </div>
          ))}
          <div style={{marginTop:10,padding:8,background:'#0A0E27',borderRadius:6}}>
            <div style={{fontSize:9,color:tokens.colors.textSecondary}}>YubiKey: 26116460</div>
            <div style={{fontSize:9,color: govState?.shalom ? tokens.colors.healthy : tokens.colors.error}}>
              Shalom: {govState?.shalom ? 'TRUE ✓' : 'FALSE'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

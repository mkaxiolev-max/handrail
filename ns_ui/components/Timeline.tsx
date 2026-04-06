'use client'
import { tokens } from '@/lib/design-tokens'

export function Timeline({events}: {events?: any[]}) {
  const data = events?.slice(0,20) || []
  return (
    <div style={{display:'flex',gap:8,overflowX:'auto',padding:'8px 0'}}>
      {data.length === 0 ? (
        <div style={{color:tokens.colors.textSecondary,fontSize:10,opacity:0.5}}>No timeline events yet</div>
      ) : data.map((ev: any, i: number) => (
        <div key={i} style={{
          background:'#0D1533',border:`1px solid ${tokens.colors.border}`,
          borderRadius:6,padding:'6px 10px',minWidth:140,flexShrink:0,fontSize:9
        }}>
          <div style={{color:tokens.colors.textSecondary,marginBottom:2}}>{ev.event_type}</div>
          <div style={{color:tokens.colors.textPrimary,wordBreak:'break-all'}}>{ev.receipt_id?.slice(0,20)}</div>
          {ev.op && <div style={{color:tokens.colors.violet,marginTop:2}}>{ev.op}</div>}
        </div>
      ))}
    </div>
  )
}

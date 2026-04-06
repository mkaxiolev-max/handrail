'use client'
import { tokens } from '@/lib/design-tokens'

export function EngineRoom({engineData, programs}: {engineData?: any, programs?: any[]}) {
  return (
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr',gap:8,height:400}}>
      {/* Intent */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.violet}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.violet,fontSize:11,fontWeight:'bold',marginBottom:8}}>INTENT</div>
        <div style={{color:tokens.colors.textSecondary,fontSize:10}}>
          {engineData?.current_intent ? (
            <div>
              <div style={{color:tokens.colors.textPrimary}}>{engineData.current_intent.last_intent || 'No active intent'}</div>
              <div style={{marginTop:4,opacity:0.7}}>{engineData.current_intent.last_run_id || ''}</div>
            </div>
          ) : <div style={{opacity:0.5}}>Awaiting intent...</div>}
        </div>
      </div>

      {/* Chambers */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.chambers}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.chambers,fontSize:11,fontWeight:'bold',marginBottom:8}}>CHAMBERS</div>
        {['NS Forge (Builder)','NS Institute (Architect)','NS Board (Guardian)'].map((c,i) => (
          <div key={i} style={{
            background:`${tokens.colors.chambers}11`,borderRadius:4,padding:'4px 8px',
            marginBottom:4,fontSize:9,color:tokens.colors.textSecondary,
            borderLeft:`2px solid ${tokens.colors.chambers}66`
          }}>{c}</div>
        ))}
        <div style={{marginTop:8,fontSize:9,color:tokens.colors.textSecondary,opacity:0.6}}>
          Model: claude-haiku-4-5
        </div>
      </div>

      {/* Adjudication */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.adjudication}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.adjudication,fontSize:11,fontWeight:'bold',marginBottom:8}}>ADJUDICATION</div>
        <div style={{fontSize:9}}>
          {engineData?.adjudication ? (
            <div>
              <div style={{color:tokens.colors.adjudication}}>Path: {engineData.adjudication.selected_path}</div>
              <div style={{color:tokens.colors.textSecondary,marginTop:4}}>Gate: {engineData.adjudication.canon_gate_result}</div>
              <div style={{color:tokens.colors.textSecondary}}>Conflicts: {engineData.adjudication.conflicts?.length || 0}</div>
            </div>
          ) : <div style={{opacity:0.5,color:tokens.colors.textSecondary}}>Idle</div>}
        </div>
      </div>

      {/* Execution + Receipt */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.handrail}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.handrail,fontSize:11,fontWeight:'bold',marginBottom:8}}>HANDRAIL + RECEIPT</div>
        <div style={{fontSize:9,color:tokens.colors.textSecondary}}>
          <div>Last receipt:</div>
          {engineData?.last_receipt ? (
            <div style={{marginTop:4}}>
              <div style={{color:tokens.colors.textPrimary,wordBreak:'break-all'}}>
                {engineData.last_receipt.receipt_id?.slice(0,24)}...
              </div>
              <div style={{color:tokens.colors.alexandria,marginTop:4}}>→ Alexandria</div>
            </div>
          ) : <div style={{opacity:0.5}}>No receipts yet</div>}
        </div>
      </div>
    </div>
  )
}

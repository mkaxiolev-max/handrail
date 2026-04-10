'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'

const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9011'

const CHAMBER_COLORS: Record<string, string> = {
  forge:     '#FF6B00',
  institute: '#6B00FF',
  board:     '#FF3333',
}

function chamberColor(role: string): string {
  const r = (role ?? '').toLowerCase()
  if (r.includes('forge') || r.includes('builder'))    return CHAMBER_COLORS.forge
  if (r.includes('institute') || r.includes('architect')) return CHAMBER_COLORS.institute
  if (r.includes('board') || r.includes('guardian'))   return CHAMBER_COLORS.board
  return tokens.colors.chambers
}

export function EngineRoom({
  engineData,
  programs,
  chamberOutputs: externalOutputs,
}: {
  engineData?: any
  programs?: any[]
  chamberOutputs?: any[]
}) {
  const [liveData, setLiveData]       = useState<any>(null)
  const [chamberOuts, setChamberOuts] = useState<any[]>(externalOutputs ?? [])

  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch(`${NS_API}/api/v1/engine/live`)
        const d = await r.json()
        setLiveData(d)
        const probe = d?.handrail_probe ?? {}
        const outputs = probe.chamber_outputs ?? probe.chambers ?? []
        if (outputs.length > 0) setChamberOuts(outputs)
      } catch { /* silent */ }
    }
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [])

  const intent = liveData?.current_intent ?? engineData?.current_intent
  const adj    = liveData?.adjudication   ?? engineData?.adjudication
  const rec    = liveData?.last_receipt   ?? engineData?.last_receipt
  const chambers = externalOutputs?.length ? externalOutputs : chamberOuts

  return (
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr',gap:8,height:400}}>

      {/* Intent */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.violet}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.violet,fontSize:11,fontWeight:'bold',marginBottom:8}}>INTENT</div>
        <div style={{color:tokens.colors.textSecondary,fontSize:10}}>
          {intent ? (
            <div>
              <div style={{color:tokens.colors.textPrimary}}>{intent.last_intent || 'No active intent'}</div>
              <div style={{marginTop:4,opacity:0.7}}>{intent.last_run_id || ''}</div>
            </div>
          ) : <div style={{opacity:0.5}}>Awaiting intent...</div>}
        </div>
      </div>

      {/* Chambers — live outputs when available */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.chambers}33`,borderRadius:8,padding:12,overflow:'hidden'}}>
        <div style={{color:tokens.colors.chambers,fontSize:11,fontWeight:'bold',marginBottom:8}}>CHAMBERS</div>
        {chambers.length > 0 ? (
          <div>
            {chambers.map((c: any, i: number) => {
              const role    = c.role ?? c.chamber ?? `Chamber ${i+1}`
              const score   = c.adjudication_score ?? c.score
              const preview = (c.response ?? c.output ?? '').slice(0, 100)
              const color   = chamberColor(role)
              return (
                <div key={i} style={{
                  background: color + '11',
                  borderLeft: `2px solid ${color}`,
                  borderRadius: 4,
                  padding: '4px 8px',
                  marginBottom: 5,
                }}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:2}}>
                    <span style={{fontSize:9,color,fontWeight:'bold'}}>{role.slice(0,18)}</span>
                    {score !== undefined && (
                      <span style={{fontSize:9,color:tokens.colors.adjudication,background:tokens.colors.adjudication+'22',borderRadius:3,padding:'0 4px'}}>
                        {typeof score==='number' ? score.toFixed(2) : score}
                      </span>
                    )}
                  </div>
                  {preview && <div style={{fontSize:8,color:tokens.colors.textSecondary,opacity:0.85,lineHeight:1.3}}>{preview}{preview.length>=100?'…':''}</div>}
                </div>
              )
            })}
          </div>
        ) : (
          <div>
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
        )}
      </div>

      {/* Adjudication */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.adjudication}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.adjudication,fontSize:11,fontWeight:'bold',marginBottom:8}}>ADJUDICATION</div>
        <div style={{fontSize:9}}>
          {adj ? (
            <div>
              <div style={{color:tokens.colors.adjudication}}>Path: {adj.selected_path}</div>
              <div style={{color:tokens.colors.textSecondary,marginTop:4}}>Gate: {adj.canon_gate_result}</div>
              <div style={{color:tokens.colors.textSecondary}}>Conflicts: {adj.conflicts?.length || 0}</div>
            </div>
          ) : <div style={{opacity:0.5,color:tokens.colors.textSecondary}}>Idle</div>}
        </div>
      </div>

      {/* Execution + Receipt */}
      <div style={{background:'#0D1533',border:`1px solid ${tokens.colors.handrail}33`,borderRadius:8,padding:12}}>
        <div style={{color:tokens.colors.handrail,fontSize:11,fontWeight:'bold',marginBottom:8}}>HANDRAIL + RECEIPT</div>
        <div style={{fontSize:9,color:tokens.colors.textSecondary}}>
          <div>Last receipt:</div>
          {rec ? (
            <div style={{marginTop:4}}>
              <div style={{color:tokens.colors.textPrimary,wordBreak:'break-all' as const}}>
                {rec.receipt_id?.slice(0,24)}...
              </div>
              <div style={{color:tokens.colors.alexandria,marginTop:4}}>→ Alexandria</div>
            </div>
          ) : <div style={{opacity:0.5}}>No receipts yet</div>}
        </div>
      </div>

    </div>
  )
}

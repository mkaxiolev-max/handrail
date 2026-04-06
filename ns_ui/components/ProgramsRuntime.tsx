'use client'
import { tokens } from '@/lib/design-tokens'

const STATE_COLORS: Record<string,string> = {
  init: tokens.colors.textSecondary,
  qualify: tokens.colors.warning,
  propose: tokens.colors.violet,
  decide: tokens.colors.adjudication,
  execute: tokens.colors.handrail,
  complete: tokens.colors.healthy,
  hold: tokens.colors.dispute,
  dispute: tokens.colors.error,
  draft: tokens.colors.textSecondary,
  active: tokens.colors.adjudication,
  archived: tokens.colors.buildSpace,
}

export function ProgramsRuntime({programs}: {programs?: any[]}) {
  const defaultPrograms = [
    'commercial','fundraising','hiring','partnership','ma',
    'advisor_san','customer_success','product_feedback','governance','knowledge_ingestion'
  ]
  const data = programs || defaultPrograms.map(id => ({id, namespace: id, state:'draft', description:''}))

  return (
    <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:8}}>
      {data.map((prog: any) => {
        const progId = prog.id || prog.program_id || prog.namespace || 'unknown'
        const progState = prog.state || prog.canonical_state || 'draft'
        return (
          <div key={progId} style={{
            background:'#0D1533',border:`1px solid ${tokens.colors.border}`,
            borderRadius:8,padding:10,cursor:'pointer',
            transition:'border-color 0.2s',
          }}
          onMouseEnter={e => (e.currentTarget.style.borderColor=tokens.colors.violet)}
          onMouseLeave={e => (e.currentTarget.style.borderColor=tokens.colors.border)}>
            <div style={{color:tokens.colors.textPrimary,fontSize:10,fontWeight:'bold',marginBottom:6,
              textTransform:'uppercase'}}>
              {progId.replace(/_/g,' ')}
            </div>
            <div style={{
              display:'inline-block',background:`${STATE_COLORS[progState]||tokens.colors.textSecondary}22`,
              border:`1px solid ${STATE_COLORS[progState]||tokens.colors.textSecondary}`,
              borderRadius:10,padding:'2px 8px',fontSize:9,
              color:STATE_COLORS[progState]||tokens.colors.textSecondary
            }}>{progState}</div>
            {prog.ops_count > 0 && (
              <div style={{fontSize:8,color:tokens.colors.textSecondary,marginTop:4}}>
                {prog.ops_count} ops
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

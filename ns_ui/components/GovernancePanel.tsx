'use client'
import { tokens } from '@/lib/design-tokens'

export function GovernancePanel({govState}: {govState?: any}) {
  const NEVER_EVENTS = ['NE1','NE2','NE3','NE4','NE5','NE6','NE7']
  const RINGS = ['Ring 1','Ring 2','Ring 3','Ring 4','Ring 5']
  const ringStatus = [true,true,true,true,false]

  return (
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
  )
}

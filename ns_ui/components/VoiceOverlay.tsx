'use client'
import { useState, useEffect } from 'react'
import { tokens } from '@/lib/design-tokens'

type VoiceState = 'dormant'|'ready'|'listening'|'processing'|'responding'|'muted'

const STATE_ICONS: Record<VoiceState,string> = {
  dormant:'◯', ready:'◉', listening:'◈', processing:'◆', responding:'◊', muted:'◌'
}
const STATE_LABELS: Record<VoiceState,string> = {
  dormant:'Violet is available', ready:'Say anything', listening:"I'm hearing you...",
  processing:'Thinking...', responding:"Here's what I found...", muted:'Voice is off'
}

export function VoiceOverlay() {
  const [state, setState] = useState<VoiceState>('ready')
  const [expanded, setExpanded] = useState(false)
  const [inputLevel, setInputLevel] = useState(0)
  const [listeningMode, setListeningMode] = useState('continuous')
  const [privacyMode, setPrivacyMode] = useState('local-first')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')

  const sendToViolet = async (text: string) => {
    if (!text.trim()) return
    setState('processing')
    setTranscript(text)
    try {
      const res = await fetch('http://localhost:9000/intent/execute', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})
      })
      const data = await res.json()
      setState('responding')
      setResponse(data.violet_response || JSON.stringify(data.results?.[0] || data))
      setTimeout(() => setState('ready'), 3000)
    } catch(e) {
      setState('ready')
    }
  }

  return (
    <div style={{position:'fixed',top:16,right:16,zIndex:1000}}>
      {/* Voice pill */}
      <div onClick={() => setExpanded(!expanded)} style={{
        background:'#0D1533', border:`1px solid ${tokens.colors.voice}`,
        borderRadius:24, padding:'8px 16px', cursor:'pointer',
        display:'flex', alignItems:'center', gap:8,
        boxShadow:`0 0 12px ${tokens.colors.voice}44`
      }}>
        <span style={{color:tokens.colors.voice, fontSize:18}}>{STATE_ICONS[state]}</span>
        <span style={{color:tokens.colors.textSecondary, fontSize:12}}>{STATE_LABELS[state]}</span>
        {state==='listening' && <span style={{color:tokens.colors.voice}}>{'▁▃▅'.slice(0,Math.floor(inputLevel*3)+1)}</span>}
      </div>

      {/* Expanded tray */}
      {expanded && (
        <div style={{
          marginTop:8, background:'#0D1533', border:`1px solid ${tokens.colors.border}`,
          borderRadius:12, padding:16, width:320,
          boxShadow:`0 8px 32px #00000088`
        }}>
          <div style={{display:'flex',justifyContent:'space-between',marginBottom:12}}>
            <span style={{color:tokens.colors.voice,fontWeight:'bold'}}>VOICE SETTINGS</span>
            <button onClick={()=>setExpanded(false)} style={{background:'none',border:'none',color:tokens.colors.textSecondary,cursor:'pointer'}}>✕</button>
          </div>

          <div style={{marginBottom:12}}>
            <div style={{color:tokens.colors.textSecondary,fontSize:11,marginBottom:6}}>Listening Mode</div>
            <div style={{display:'flex',gap:6}}>
              {['tap','hold','continuous','wake'].map(m => (
                <button key={m} onClick={()=>setListeningMode(m)} style={{
                  background: listeningMode===m ? tokens.colors.voice : 'transparent',
                  color: listeningMode===m ? '#000' : tokens.colors.textSecondary,
                  border:`1px solid ${tokens.colors.border}`,borderRadius:4,padding:'2px 8px',
                  fontSize:10,cursor:'pointer'
                }}>{m}</button>
              ))}
            </div>
          </div>

          <div style={{marginBottom:12}}>
            <div style={{color:tokens.colors.textSecondary,fontSize:11,marginBottom:6}}>Privacy Mode</div>
            <div style={{display:'flex',gap:6}}>
              {['local-first','normal','bounded-ext'].map(m => (
                <button key={m} onClick={()=>setPrivacyMode(m)} style={{
                  background: privacyMode===m ? tokens.colors.violet : 'transparent',
                  color: privacyMode===m ? '#000' : tokens.colors.textSecondary,
                  border:`1px solid ${tokens.colors.border}`,borderRadius:4,padding:'2px 8px',
                  fontSize:10,cursor:'pointer'
                }}>{m}</button>
              ))}
            </div>
          </div>

          <div style={{marginBottom:12}}>
            <input
              placeholder="Type intent for Violet..."
              onKeyDown={e => {if(e.key==='Enter') { sendToViolet((e.target as HTMLInputElement).value); (e.target as HTMLInputElement).value=''; }}}
              style={{width:'100%',background:'#0A0E27',border:`1px solid ${tokens.colors.border}`,
                color:tokens.colors.textPrimary,borderRadius:6,padding:'6px 10px',fontSize:12}}
            />
          </div>

          {response && (
            <div style={{background:'#0A1540',borderRadius:6,padding:10,fontSize:11,
              color:tokens.colors.textSecondary,borderLeft:`3px solid ${tokens.colors.violet}`}}>
              <div style={{color:tokens.colors.violet,marginBottom:4}}>Violet:</div>
              {response.slice(0,300)}{response.length>300?'...':''}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

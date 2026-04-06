'use client'
import { useEffect, useState } from 'react'
import { tokens } from '@/lib/design-tokens'

const NODES = [
  {id:'founder',label:'FOUNDER / MIKE',x:400,y:20,color:tokens.colors.founder,size:60},
  {id:'violet',label:'VIOLET',x:400,y:100,color:tokens.colors.violet,size:55},
  {id:'chambers',label:'CHAMBERS',x:200,y:200,color:tokens.colors.chambers,size:52},
  {id:'adjudication',label:'ADJUDICATION',x:400,y:200,color:tokens.colors.adjudication,size:50},
  {id:'ns_core',label:'NS CORE',x:600,y:200,color:tokens.colors.handrail,size:50},
  {id:'ether',label:'ETHER/HIC',x:650,y:300,color:'#FF88FF',size:45},
  {id:'handrail',label:'HANDRAIL',x:550,y:380,color:tokens.colors.handrail,size:52},
  {id:'alexandria',label:'ALEXANDRIA',x:400,y:450,color:tokens.colors.alexandria,size:55},
  {id:'programs',label:'PROGRAMS',x:220,y:380,color:'#88FFAA',size:48},
  {id:'lexicon',label:'LEXICON',x:120,y:300,color:'#FFCC44',size:42},
  {id:'kernel',label:'KERNEL',x:700,y:100,color:tokens.colors.kernel,size:45},
  {id:'voice',label:'VOICE/MAC',x:100,y:150,color:tokens.colors.voice,size:42},
]

const EDGES = [
  ['founder','violet'],['violet','chambers'],['violet','adjudication'],
  ['chambers','adjudication'],['adjudication','handrail'],['adjudication','ns_core'],
  ['ns_core','ether'],['handrail','alexandria'],['handrail','programs'],
  ['programs','alexandria'],['lexicon','violet'],['kernel','adjudication'],
  ['voice','violet'],['alexandria','violet'],
]

export function OrganismMap({systemState}: {systemState?: any}) {
  const [activeNode, setActiveNode] = useState<string|null>(null)
  const [phase, setPhase] = useState('idle')

  useEffect(() => {
    if (systemState?.metrics?.phase) setPhase(systemState.metrics.phase)
  }, [systemState])

  const getNodeHealth = (id: string) => {
    if (!systemState?.nodes) return 'ok'
    const n = systemState.nodes.find((n:any) => n.id === id)
    return n?.health || 'ok'
  }

  return (
    <div style={{position:'relative',width:'100%',height:520,background:'#080C1E',borderRadius:12,overflow:'hidden'}}>
      {/* Phase badge */}
      <div style={{position:'absolute',top:12,left:12,background:'#0D1533',
        border:`1px solid ${tokens.colors.adjudication}`,borderRadius:20,
        padding:'4px 12px',fontSize:11,color:tokens.colors.adjudication}}>
        PHASE: {phase.toUpperCase()}
      </div>

      {/* SVG flows */}
      <svg style={{position:'absolute',top:0,left:0,width:'100%',height:'100%'}} viewBox="0 0 800 520">
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill={tokens.colors.border}/>
          </marker>
        </defs>
        {EDGES.map(([from,to]) => {
          const fn = NODES.find(n=>n.id===from)!
          const tn = NODES.find(n=>n.id===to)!
          return (
            <line key={`${from}-${to}`}
              x1={fn.x} y1={fn.y} x2={tn.x} y2={tn.y}
              stroke={tokens.colors.border} strokeWidth={1.5}
              strokeDasharray="4 3" opacity={0.6}
              markerEnd="url(#arrow)"
            />
          )
        })}
      </svg>

      {/* Nodes */}
      {NODES.map(node => (
        <div key={node.id}
          onClick={() => setActiveNode(activeNode===node.id ? null : node.id)}
          className={getNodeHealth(node.id)==='ok' ? 'pulse' : ''}
          style={{
            position:'absolute',
            left: node.x - node.size/2,
            top: node.y - node.size/2,
            width: node.size,
            height: node.size,
            borderRadius:'50%',
            background: `${node.color}22`,
            border: `2px solid ${activeNode===node.id ? node.color : node.color+'88'}`,
            display:'flex',alignItems:'center',justifyContent:'center',
            cursor:'pointer',
            boxShadow: activeNode===node.id ? `0 0 20px ${node.color}88` : 'none',
            transition:'all 0.3s',
            zIndex: activeNode===node.id ? 10 : 1
          }}>
          <span style={{fontSize:8,color:node.color,textAlign:'center',lineHeight:1.2,padding:4}}>
            {node.label}
          </span>
        </div>
      ))}

      {/* Privacy membrane ring */}
      <svg style={{position:'absolute',top:0,left:0,width:'100%',height:'100%',pointerEvents:'none'}} viewBox="0 0 800 520">
        <ellipse cx="400" cy="260" rx="370" ry="245" fill="none"
          stroke={tokens.colors.kernel} strokeWidth={1} strokeDasharray="8 4" opacity={0.3}/>
        <text x="400" y="510" textAnchor="middle" fill={tokens.colors.kernel} fontSize={9} opacity={0.5}>
          PRIVACY MEMBRANE — CONSTITUTIONAL BOUNDARY
        </text>
      </svg>

      {/* Build space label */}
      <div style={{position:'absolute',bottom:8,right:12,fontSize:9,color:tokens.colors.buildSpace,opacity:0.7}}>
        BUILD SPACE →
      </div>
    </div>
  )
}

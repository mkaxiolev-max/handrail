import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { VioletLogo, AxiolevWordmark } from './brand/VioletMark'

const routes = [
  { path: '/violet', label: '⬡ Violet' },
  { path: '/briefing', label: 'Briefing' },
  { path: '/engine', label: 'Engine' },
  { path: '/runtime', label: 'Runtime' },
  { path: '/memory', label: 'Memory' },
  { path: '/governance', label: 'Governance' },
  { path: '/omega', label: '⍉ Omega' },
  { path: '/calls', label: 'Calls' },
  { path: '/build', label: 'Build' },
]

const LeftNav = () => {
  const loc = useLocation()
  return (
    <nav className="p-3">
      <div className="flex items-center gap-2 mb-5 pt-1">
        <VioletLogo size={32} />
        <div className="flex flex-col">
          <span className="font-mono font-bold text-xs text-violet-300 tracking-widest">AXIOLEV</span>
          <span className="font-mono text-xs text-violet-500" style={{ fontSize: '9px' }}>NS∞</span>
        </div>
      </div>
      {routes.map(r => (
        <Link key={r.path} to={r.path}
          className={`block py-1.5 px-2 rounded text-xs mb-0.5 font-mono ${
            loc.pathname === r.path
              ? 'bg-violet-800 text-violet-200'
              : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
          }`}>
          {r.label}
        </Link>
      ))}
    </nav>
  )
}

export default LeftNav

import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const routes = [
  { path: '/briefing', label: 'Briefing' },
  { path: '/engine', label: 'Engine' },
  { path: '/runtime', label: 'Runtime' },
  { path: '/memory', label: 'Memory' },
  { path: '/governance', label: 'Governance' },
  { path: '/calls', label: 'Calls' },
  { path: '/build', label: 'Build' }
]

const LeftNav = () => {
  const loc = useLocation()
  return (
    <nav className="p-4">
      <div className="font-bold text-lg mb-6 font-mono">NS∞</div>
      {routes.map(r => (
        <Link key={r.path} to={r.path}
          className={`block py-2 px-2 rounded text-sm mb-1 ${loc.pathname === r.path ? 'bg-violet-700' : 'hover:bg-gray-700'}`}>
          {r.label}
        </Link>
      ))}
    </nav>
  )
}

export default LeftNav

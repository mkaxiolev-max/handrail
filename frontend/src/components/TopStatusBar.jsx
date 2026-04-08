import React from 'react'
const TopStatusBar = ({ systemState }) => {
  if (!systemState) return null
  const s = systemState
  return (
    <div className="h-12 border-b border-gray-700 bg-gray-800 flex items-center px-4 text-sm gap-6 shrink-0">
      <span className={`font-mono ${s.system?.shalom ? 'text-green-400' : 'text-red-400'}`}>
        {s.system?.shalom ? 'shalom' : 'attention'}
      </span>
      <span className="font-mono text-gray-400">{s.system?.services_healthy}/{s.system?.services_expected} svc</span>
      <span className="font-mono text-violet-400">mode: {s.violet?.mode}</span>
      <span className="font-mono text-gray-300">role: {s.violet?.active_role}</span>
      <span className="font-mono text-gray-400">pressure: {s.violet?.current_pressure}</span>
      <span className="ml-auto font-mono text-xs text-gray-500">voice: {s.violet?.voice_state}</span>
    </div>
  )
}
export default TopStatusBar

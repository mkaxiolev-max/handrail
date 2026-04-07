import React, { useContext } from 'react'
import { SystemContext } from '../contexts/SystemContext'

const CallsPage = () => {
  const { systemState } = useContext(SystemContext)
  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Voice & Calls</h1>
      <div className="bg-gray-800 rounded p-4 border border-gray-700 space-y-3 text-sm">
        <div><span className="text-gray-500">Voice State: </span>
          <span className="font-mono text-violet-400">{systemState?.violet?.voice_state ?? 'idle'}</span></div>
        <div><span className="text-gray-500">Inbound: </span>
          <span className="font-mono">+1(307)202-4418</span></div>
        <div className="text-xs text-gray-400 pt-2">Call the system to start a voice session.</div>
      </div>
    </div>
  )
}

export default CallsPage

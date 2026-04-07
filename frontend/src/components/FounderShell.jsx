import React, { useContext } from 'react'
import { SystemContext } from '../contexts/SystemContext'
import LeftNav from './LeftNav'
import VioletRail from './VioletRail'
import TruthPanel from './TruthPanel'
import TimelineRail from './TimelineRail'

const FounderShell = ({ children }) => {
  const { systemState, loading } = useContext(SystemContext)

  if (loading) return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Loading NS∞...</div>

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <div className="w-48 border-r border-gray-700 overflow-y-auto">
        <LeftNav />
      </div>
      <div className="flex-1 flex flex-col">
        <div className="h-12 border-b border-gray-700 bg-gray-800 flex items-center px-4 text-sm font-mono">
          <span>NS∞ {systemState?.system?.services_healthy}/{systemState?.system?.services_expected} svc</span>
          <span className="ml-4">mode: {systemState?.violet?.mode ?? 'founder_ready'}</span>
          <span className="ml-auto">{systemState?.system?.shalom !== false ? 'shalom' : 'attention'}</span>
        </div>
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col overflow-hidden">
            <VioletRail />
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </div>
          <div className="w-72 border-l border-gray-700 overflow-y-auto">
            <TruthPanel systemState={systemState} />
          </div>
        </div>
        <div className="h-28 border-t border-gray-700 bg-gray-800 overflow-x-auto">
          <TimelineRail />
        </div>
      </div>
    </div>
  )
}

export default FounderShell

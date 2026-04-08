import React, { useContext } from 'react'
import { SystemContext } from '../contexts/SystemContext'
import LeftNav from './LeftNav'
import TopStatusBar from './TopStatusBar'
import VioletRail from './VioletRail'
import TruthPanel from './TruthPanel'
import TimelineRail from './TimelineRail'

const FounderShell = ({ children }) => {
  const { systemState, loading } = useContext(SystemContext)
  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-900 text-white font-mono">
      Loading NS∞...
    </div>
  )
  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      <div className="w-48 shrink-0 border-r border-gray-700 overflow-y-auto bg-gray-800">
        <LeftNav />
      </div>
      <div className="flex-1 flex flex-col min-w-0">
        <TopStatusBar systemState={systemState} />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0">
            <VioletRail systemState={systemState} />
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </div>
          <div className="w-72 shrink-0 border-l border-gray-700 overflow-y-auto bg-gray-800">
            <TruthPanel systemState={systemState} />
          </div>
        </div>
        <div className="h-20 shrink-0 border-t border-gray-700 bg-gray-800">
          <TimelineRail />
        </div>
      </div>
    </div>
  )
}
export default FounderShell

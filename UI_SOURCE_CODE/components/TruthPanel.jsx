import React from 'react'

const Row = ({ label, value, highlight }) => (
  <div className="mb-3">
    <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
    <div className={`font-mono text-sm mt-0.5 ${highlight ? 'text-violet-400' : 'text-white'}`}>{value ?? '—'}</div>
  </div>
)

const TruthPanel = ({ systemState }) => {
  if (!systemState) return <div className="p-4 text-sm text-gray-500">Connecting...</div>
  return (
    <div className="p-4 text-sm">
      <div className="text-xs font-bold text-gray-400 uppercase mb-4">Truth Panel</div>
      <Row label="Voice State" value={systemState.violet?.voice_state ?? 'idle'} highlight />
      <Row label="Mode" value={systemState.violet?.mode ?? 'founder_ready'} />
      <Row label="Active Program" value={systemState.violet?.active_program} />
      <Row label="Active Role" value={systemState.violet?.active_role} />
      <Row label="Pressure" value={systemState.violet?.current_pressure ?? 'low'} />
      <div className="border-t border-gray-700 pt-3 mt-3">
        <div className="text-xs font-bold text-gray-400 uppercase mb-2">Memory</div>
        <div className="font-mono text-xs space-y-1 text-gray-300">
          <div>atoms: {systemState.memory?.atoms ?? '—'}</div>
          <div>edges: {systemState.memory?.edges ?? '—'}</div>
          <div>feed: {systemState.memory?.feed_items ?? '—'}</div>
          <div>receipts: {systemState.memory?.receipts ?? '—'}</div>
        </div>
      </div>
      <div className="border-t border-gray-700 pt-3 mt-3">
        <div className="text-xs text-gray-500">Last Receipt</div>
        <div className="font-mono text-xs text-gray-400 mt-1 break-all">{systemState.recent?.last_receipt ?? '—'}</div>
      </div>
    </div>
  )
}

export default TruthPanel

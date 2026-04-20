import React, { useEffect, useState } from 'react'
import axios from 'axios'

const NS_CORE = 'http://127.0.0.1:9000'

const StatusDot = ({ status }) => (
  <span className={`inline-block w-2 h-2 rounded-full ${
    status === 'live' ? 'bg-green-400' : status === 'down' ? 'bg-red-400' : 'bg-yellow-400'
  }`} />
)

const RuntimePage = () => {
  const [overview, setOverview] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await axios.get(`${NS_CORE}/api/organism/overview`)
        setOverview(res.data)
        setError(null)
      } catch (e) {
        setError(e.message)
      }
    }
    fetch_()
    const id = setInterval(fetch_, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold font-mono">Runtime</h1>
      {error && <div className="text-red-400 text-xs font-mono">{error}</div>}

      {overview ? (
        <>
          <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
            <div className="text-xs text-gray-400 font-mono mb-3 uppercase tracking-wider">Services</div>
            <div className="space-y-2">
              {(overview.services || []).map(svc => (
                <div key={svc.id} className="flex items-center gap-3 text-xs font-mono">
                  <StatusDot status={svc.status} />
                  <span className="text-gray-200 w-24">{svc.label}</span>
                  <span className="text-gray-500">{svc.endpoint}</span>
                  {svc.latency_ms != null && (
                    <span className="ml-auto text-gray-400">{svc.latency_ms}ms</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
              <div className="text-xs text-gray-400 font-mono mb-2 uppercase tracking-wider">Memory</div>
              <div className="space-y-1 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-gray-400">Alexandria</span>
                  <span className={overview.memory?.alexandria_mounted ? 'text-green-400' : 'text-red-400'}>
                    {overview.memory?.alexandria_mounted ? 'mounted' : 'offline'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Receipt files</span>
                  <span className="text-gray-300">{overview.memory?.receipt_files ?? 'n/a'}</span>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
              <div className="text-xs text-gray-400 font-mono mb-2 uppercase tracking-wider">System</div>
              <div className="space-y-1 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-gray-400">State</span>
                  <span className="text-gray-300">{overview.system_state?.state ?? 'unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Commit</span>
                  <span className="text-gray-300">{overview.system_state?.git_commit ?? 'unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Shalom</span>
                  <span className={overview.system_state?.shalom ? 'text-green-400' : 'text-yellow-400'}>
                    {overview.system_state?.shalom ? '✓ true' : '✗ false'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        !error && <div className="text-xs text-gray-500 font-mono">Loading runtime telemetry…</div>
      )}
    </div>
  )
}

export default RuntimePage

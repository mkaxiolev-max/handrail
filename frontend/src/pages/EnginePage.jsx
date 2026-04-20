import React, { useEffect, useState } from 'react'
import axios from 'axios'

const NS_CORE = 'http://127.0.0.1:9000'

const EnginePage = () => {
  const [state, setState] = useState(null)
  const [events, setEvents] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await axios.get(`${NS_CORE}/ns/state`)
        setState(res.data)
        setError(null)
      } catch (e) {
        setError(e.message)
      }
    }
    fetchState()
    const id = setInterval(fetchState, 5000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const es = new EventSource(`${NS_CORE}/ns/engine/live`)
    es.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data)
        setEvents(prev => [ev, ...prev].slice(0, 20))
      } catch {}
    }
    return () => es.close()
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold font-mono">Engine — L10 Live Feed</h1>
      {error && <div className="text-red-400 text-xs font-mono">{error}</div>}

      {state && (
        <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
          <div className="text-xs text-gray-400 font-mono mb-3 uppercase tracking-wider">10-Layer Stack</div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(state.layers || {}).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-xs font-mono">
                <span className="text-violet-400">{k}</span>
                <span className="text-gray-300">{v.name}</span>
                <span className={`ml-auto ${v.status === 'active' || v.status === 'mounted' ? 'text-green-400' : 'text-yellow-400'}`}>
                  {v.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
        <div className="text-xs text-gray-400 font-mono mb-3 uppercase tracking-wider">Live Event Stream</div>
        {events.length === 0
          ? <div className="text-xs text-gray-500 font-mono">Connecting to engine stream…</div>
          : events.map((e, i) => (
            <div key={i} className="flex gap-3 text-xs font-mono border-b border-gray-800 py-1">
              <span className="text-gray-500">{e.ts?.slice(11, 19)}</span>
              <span className="text-violet-400">#{e.seq}</span>
              <span className="text-gray-300">{e.event}</span>
              <span className="text-gray-500 ml-auto">{e.layer}</span>
            </div>
          ))
        }
      </div>
    </div>
  )
}

export default EnginePage

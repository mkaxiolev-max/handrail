import React, { useEffect, useState } from 'react'
import axios from 'axios'

const NS_CORE = 'http://127.0.0.1:9000'

const BuildPage = () => {
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [ran, setRan] = useState(false)

  const buildFeed = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${NS_CORE}/feed/build`)
      setCards(res.data?.cards ?? [])
      setRan(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    buildFeed()
  }, [])

  const typeColors = {
    health: 'text-green-400',
    memory: 'text-blue-400',
    voice:  'text-violet-400',
    canon:  'text-yellow-400',
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold font-mono">Build Feed</h1>
        <button
          onClick={buildFeed}
          disabled={loading}
          className="text-xs font-mono px-3 py-1 rounded border border-violet-500/40 bg-violet-900/20 text-violet-300 hover:bg-violet-900/40 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Rebuilding…' : 'Rebuild'}
        </button>
      </div>

      {error && <div className="text-red-400 text-xs font-mono">{error}</div>}

      <div className="space-y-2">
        {cards.map((card, i) => (
          <div key={card.id ?? i} className="rounded-lg border border-gray-700 bg-gray-900/60 p-4 hover:border-violet-500/40 transition-colors">
            <div className={`text-xs font-mono uppercase tracking-wider mb-1 ${typeColors[card.type] ?? 'text-gray-400'}`}>
              {card.type}
            </div>
            <div className="text-sm text-gray-200 font-mono">{card.label}</div>
          </div>
        ))}
        {ran && cards.length === 0 && (
          <div className="text-xs text-gray-500 font-mono">No feed cards returned.</div>
        )}
      </div>
    </div>
  )
}

export default BuildPage

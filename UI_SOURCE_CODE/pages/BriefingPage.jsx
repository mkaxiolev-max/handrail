import React, { useContext, useEffect, useState } from 'react'
import { SystemContext } from '../contexts/SystemContext'
import axios from 'axios'

const BriefingPage = () => {
  const { systemState } = useContext(SystemContext)
  const [feed, setFeed] = useState([])

  useEffect(() => {
    axios.post('http://127.0.0.1:9000/feed/build')
      .then(res => setFeed(res.data?.cards ?? []))
      .catch(() => {})
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Founder Briefing</h1>
      <div className="grid gap-3">
        {feed.map((card, i) => (
          <div key={card.id ?? i} className="bg-gray-800 rounded p-4 border border-gray-700 hover:border-violet-500 transition-colors">
            <div className="text-xs text-gray-500 uppercase">{card.type}</div>
            <div className="font-medium mt-1">{card.label}</div>
          </div>
        ))}
        {feed.length === 0 && <div className="text-gray-500 text-sm">No feed items — run feed/build</div>}
      </div>
    </div>
  )
}

export default BriefingPage

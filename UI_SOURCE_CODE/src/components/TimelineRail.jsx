import React, { useEffect, useState } from 'react'
import axios from 'axios'

const TimelineRail = () => {
  const [events, setEvents] = useState([])

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:9000/feed')
        setEvents(res.data?.items ?? [])
      } catch {}
    }
    fetch()
    const id = setInterval(fetch, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex gap-2 p-3 overflow-x-auto h-full items-center">
      {events.length === 0 ? (
        <span className="text-xs text-gray-500">Timeline — no events yet</span>
      ) : events.slice(-12).map((e, i) => (
        <div key={i} className="flex-shrink-0 bg-gray-700 rounded px-3 py-1.5 text-xs whitespace-nowrap border border-gray-600">
          <span className="text-gray-400">{e.type}</span> {e.label}
        </div>
      ))}
    </div>
  )
}

export default TimelineRail

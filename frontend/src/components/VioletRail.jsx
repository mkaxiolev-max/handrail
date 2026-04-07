import React, { useContext, useState } from 'react'
import { SystemContext } from '../contexts/SystemContext'
import axios from 'axios'

const VioletRail = () => {
  const { systemState } = useContext(SystemContext)
  const [input, setInput] = useState('')
  const [transcript, setTranscript] = useState([])

  const handleExecute = async () => {
    if (!input.trim()) return
    const text = input
    setInput('')
    setTranscript(prev => [...prev, { role: 'founder', text, ts: new Date().toISOString() }])
    try {
      const res = await axios.post('http://127.0.0.1:9000/intent/execute', {
        intent: text, mode: systemState?.violet?.mode ?? 'founder_strategic'
      })
      setTranscript(prev => [...prev, { role: 'violet', text: res.data?.summary ?? JSON.stringify(res.data), ts: new Date().toISOString() }])
    } catch (err) {
      setTranscript(prev => [...prev, { role: 'error', text: err.message }])
    }
  }

  return (
    <div className="border-b border-gray-700 bg-gray-800 p-4">
      <div className="max-h-40 overflow-y-auto mb-3 space-y-1 text-sm">
        {transcript.map((msg, i) => (
          <div key={i} className={msg.role === 'violet' ? 'text-violet-400' : msg.role === 'error' ? 'text-red-400' : 'text-gray-300'}>
            <span className="font-mono text-xs text-gray-500">{msg.role}: </span>{msg.text}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input type="text" value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleExecute()}
          placeholder="Talk to Violet..."
          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500" />
        <button onClick={handleExecute}
          className="bg-violet-600 hover:bg-violet-700 px-4 py-2 rounded text-sm font-medium">Send</button>
      </div>
    </div>
  )
}

export default VioletRail

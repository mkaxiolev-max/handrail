import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const VioletRail = ({ systemState }) => {
  const [input, setInput] = useState('')
  const [transcript, setTranscript] = useState([])
  const [executing, setExecuting] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  const send = async () => {
    if (!input.trim() || executing) return
    const text = input.trim()
    setInput('')
    setExecuting(true)
    setTranscript(prev => [...prev, { role: 'founder', text, ts: new Date().toLocaleTimeString() }])
    try {
      const res = await axios.post('http://127.0.0.1:9000/intent/execute', {
        intent: text,
        mode: systemState?.violet?.mode || 'founder_strategic'
      })
      setTranscript(prev => [...prev, {
        role: 'violet',
        text: res.data?.response || res.data?.summary || 'Executed.',
        ts: new Date().toLocaleTimeString(),
        receipt: res.data?.receipt_hash
      }])
    } catch (err) {
      setTranscript(prev => [...prev, { role: 'error', text: err.message, ts: new Date().toLocaleTimeString() }])
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="border-b border-gray-700 bg-gray-800 p-3 shrink-0">
      <div className="h-36 overflow-y-auto mb-3 space-y-1.5 text-sm bg-gray-900 rounded p-3">
        {transcript.length === 0 && <div className="text-gray-500 italic text-xs">Talk to Violet...</div>}
        {transcript.map((msg, i) => (
          <div key={i} className={`flex gap-2 text-xs ${msg.role === 'violet' ? 'text-violet-300' : msg.role === 'error' ? 'text-red-400' : 'text-gray-300'}`}>
            <span className="text-gray-600 shrink-0 w-16">{msg.ts}</span>
            <span className="text-gray-500 shrink-0 w-12">{msg.role}:</span>
            <span className="break-words min-w-0">{msg.text}</span>
            {msg.receipt && <span className="text-gray-600 shrink-0">[{msg.receipt.slice(0,8)}]</span>}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input type="text" value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="What do you need?"
          disabled={executing}
          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-white text-sm focus:outline-none focus:border-violet-500 disabled:opacity-50"
        />
        <button onClick={send} disabled={executing}
          className="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 px-4 py-1.5 rounded text-sm font-medium">
          {executing ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
export default VioletRail

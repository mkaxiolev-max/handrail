import React, { useState, useRef, useEffect } from 'react'

const NS_CORE = 'http://127.0.0.1:9000'

const SUGGESTIONS = [
  'What is your current state?',
  'Summarize the system health.',
  'What programs are running?',
  'Give me a briefing.',
]

const Bubble = ({ msg }) => {
  const isUser = msg.role === 'user'
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 10,
    }}>
      {!isUser && (
        <div style={{
          width: 26, height: 26, borderRadius: '50%',
          background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, color: '#fff', fontWeight: 'bold',
          flexShrink: 0, marginRight: 8, marginTop: 2,
        }}>V</div>
      )}
      <div style={{
        maxWidth: '72%',
        background: isUser ? '#312e81' : '#1e1b4b',
        border: `1px solid ${isUser ? '#4f46e5' : '#2d2a6e'}`,
        borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
        padding: '8px 12px',
        fontSize: 12,
        color: isUser ? '#c7d2fe' : '#e0e7ff',
        lineHeight: 1.55,
        wordBreak: 'break-word',
      }}>
        {msg.text}
        <div style={{ fontSize: 9, color: '#6366f1', marginTop: 4, opacity: 0.7 }}>
          {msg.ts}
        </div>
      </div>
    </div>
  )
}

const VioletChat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'violet',
      text: 'Shalom. I am Violet — the intelligence layer of NS∞. How can I serve you?',
      ts: new Date().toLocaleTimeString(),
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [provider, setProvider] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const prompt = (text || input).trim()
    if (!prompt || loading) return
    setInput('')
    const ts = new Date().toLocaleTimeString()
    setMessages(prev => [...prev, { role: 'user', text: prompt, ts }])
    setLoading(true)

    try {
      const res = await fetch(`${NS_CORE}/violet/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: prompt }),
      })
      const data = await res.json()
      if (data.ok) {
        setProvider(data.provider || null)
        setMessages(prev => [...prev, {
          role: 'violet',
          text: data.text,
          ts: new Date().toLocaleTimeString(),
        }])
      } else {
        setMessages(prev => [...prev, {
          role: 'violet',
          text: `[Error] ${data.error || 'Unknown error'}`,
          ts: new Date().toLocaleTimeString(),
        }])
      }
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'violet',
        text: '[Network error] Cannot reach NS Core at :9000.',
        ts: new Date().toLocaleTimeString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#0d0d1f', borderRadius: 10,
      border: '1px solid #2d2a6e', overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 16px',
        background: '#12103a',
        borderBottom: '1px solid #2d2a6e',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, color: '#fff', fontWeight: 'bold',
        }}>V</div>
        <div>
          <div style={{ fontSize: 12, color: '#a5b4fc', fontWeight: 'bold', fontFamily: 'monospace' }}>
            VIOLET · NS∞ Intelligence
          </div>
          <div style={{ fontSize: 9, color: '#6366f1', fontFamily: 'monospace' }}>
            {provider ? `via ${provider}` : 'multi-provider fallback chain'}
          </div>
        </div>
        <div style={{ marginLeft: 'auto', fontSize: 9, color: '#22c55e' }}>● LIVE</div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: 'auto', padding: '14px 12px',
        display: 'flex', flexDirection: 'column',
      }}>
        {messages.map((m, i) => <Bubble key={i} msg={m} />)}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
            <div style={{
              width: 26, height: 26, borderRadius: '50%',
              background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, color: '#fff', fontWeight: 'bold', flexShrink: 0,
            }}>V</div>
            <div style={{
              background: '#1e1b4b', border: '1px solid #2d2a6e',
              borderRadius: '12px 12px 12px 2px', padding: '8px 14px',
              fontSize: 12, color: '#6366f1',
            }}>
              <span className="animate-pulse">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && !loading && (
        <div style={{ padding: '0 12px 8px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => send(s)} style={{
              fontSize: 10, padding: '4px 10px',
              background: '#1e1b4b', border: '1px solid #4f46e5',
              borderRadius: 20, color: '#a5b4fc', cursor: 'pointer',
              fontFamily: 'monospace',
            }}>{s}</button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: '10px 12px',
        borderTop: '1px solid #2d2a6e',
        background: '#12103a',
        display: 'flex', gap: 8, alignItems: 'flex-end',
      }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Message Violet… (Enter to send)"
          rows={1}
          style={{
            flex: 1, background: '#0d0d1f', border: '1px solid #4f46e5',
            borderRadius: 8, padding: '8px 10px', color: '#e0e7ff',
            fontSize: 12, fontFamily: 'monospace', resize: 'none',
            outline: 'none', lineHeight: 1.5,
          }}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          style={{
            background: input.trim() && !loading ? '#4f46e5' : '#1e1b4b',
            border: 'none', borderRadius: 8, padding: '8px 14px',
            color: input.trim() && !loading ? '#fff' : '#4f46e5',
            cursor: input.trim() && !loading ? 'pointer' : 'default',
            fontSize: 12, fontFamily: 'monospace', fontWeight: 'bold',
            transition: 'all 0.15s',
          }}
        >↑</button>
      </div>
    </div>
  )
}

export default VioletChat

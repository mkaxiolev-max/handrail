import React from 'react'
import VioletChat from '../components/VioletChat'

const VioletPage = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: 12 }}>
        <h1 style={{ fontSize: 18, fontWeight: 'bold', margin: 0, color: '#a5b4fc', fontFamily: 'monospace' }}>
          Violet
        </h1>
        <div style={{ fontSize: 10, color: '#6366f1', fontFamily: 'monospace', marginTop: 2 }}>
          NS∞ Intelligence · Multi-provider LLM · Groq → Grok → Ollama → Anthropic → OpenAI → canned
        </div>
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <VioletChat />
      </div>
    </div>
  )
}

export default VioletPage

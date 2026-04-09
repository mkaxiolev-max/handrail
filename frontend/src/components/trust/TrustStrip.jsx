/**
 * TrustStrip — first-class system truth on every response card.
 * If these values are absent, the system is not proving its work.
 */
import React from 'react'

const Pill = ({ label, value, ok }) => {
  const bg = ok === true ? '#1a7a4a' : ok === false ? '#7a1a1a' : '#1a3a5a'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '4px',
      background: bg, borderRadius: '4px', padding: '2px 7px',
      fontSize: '10px', fontFamily: 'monospace', color: '#e8e8e8',
      margin: '2px', letterSpacing: '0.3px',
    }}>
      <span style={{ opacity: 0.6 }}>{label}</span>
      <span style={{ fontWeight: 700 }}>{String(value)}</span>
    </span>
  )
}

export function TrustStrip({
  receiptHash, chainVerified, mode,
  pressure, canonVersion, canonHash,
  memoryAtomsWritten = 0, memoryAtomsQueried = 0,
  feedItemsAdded = 0, responseShape, voiceSessionId,
}) {
  return (
    <div style={{
      borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: '8px',
      paddingTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '2px',
    }}>
      <Pill label="receipt" value={receiptHash ? receiptHash.slice(0, 12) + '…' : '—'} />
      <Pill label="chain" value={chainVerified ? '✓' : 'BROKEN'} ok={chainVerified} />
      <Pill label="mode" value={mode} />
      {pressure && <Pill label="pressure" value={pressure} />}
      {responseShape && <Pill label="kind" value={responseShape} />}
      {canonVersion != null && <Pill label="canon" value={`v${canonVersion}`} />}
      {canonHash && <Pill label="canon_hash" value={canonHash.slice(0, 8) + '…'} />}
      {memoryAtomsWritten > 0 && <Pill label="atoms_written" value={memoryAtomsWritten} />}
      {memoryAtomsQueried > 0 && <Pill label="atoms_queried" value={memoryAtomsQueried} />}
      {feedItemsAdded > 0 && <Pill label="feed+" value={feedItemsAdded} />}
      {voiceSessionId && <Pill label="voice" value={voiceSessionId.slice(0, 8) + '…'} />}
    </div>
  )
}

export default TrustStrip

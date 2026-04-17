import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function PastTimeline() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.alexandriaEvents).then(setData); }, []);
  if (!data) return <div className="pane loading">Past loading…</div>;
  if (isError(data)) return <div className="pane error">PAST ERROR: {errorMessage(data)}</div>;
  const events = data.artifacts || data.events || [];
  return (
    <div className="pane">
      <h3>PAST — Alexandria Events</h3>
      {events.length === 0 && <p>No events yet</p>}
      {events.slice(0, 20).map((e, i) => (
        <div key={i} className="event">
          <span className="ts">{(e.timestamp || e.ts || '').slice(0, 19)}</span>
          <span className="op">{e.operation || e.op || e.type || '?'}</span>
          <span className={e.ok === false ? 'fail' : 'pass'}>{e.ok === false ? '✗' : '✓'}</span>
        </div>
      ))}
    </div>
  );
}

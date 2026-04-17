import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function CanonPendingTile() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.canonPending).then(setData); }, []);
  if (!data) return <div className="tile loading">Canon Pending loading…</div>;
  if (isError(data)) return <div className="tile error">Canon Pending ERROR: {errorMessage(data)}</div>;
  const items = data.artifacts || [];
  return (
    <div className="tile ok">
      <h4>Canon Pending ({items.length})</h4>
      {items.length === 0 && <p className="small">No pending promotions</p>}
      {items.slice(0, 3).map((p, i) => (
        <p key={i} className="small">{p.candidate_id}: {p.queued_at?.slice(0, 10)}</p>
      ))}
    </div>
  );
}

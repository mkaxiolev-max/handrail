import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function ClearingTile() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.clearingAbstentions).then(setData); }, []);
  if (!data) return <div className="tile loading">Clearing loading…</div>;
  if (isError(data)) return <div className="tile error">Clearing ERROR: {errorMessage(data)}</div>;
  const items = data.artifacts || [];
  return (
    <div className="tile ok">
      <h4>Clearing Abstentions ({items.length})</h4>
      {items.slice(0, 3).map((a, i) => (
        <p key={i} className="small">{a.op || '?'}: {a.reason}</p>
      ))}
    </div>
  );
}

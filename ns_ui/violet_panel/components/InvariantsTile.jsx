import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function InvariantsTile() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.canonInvariants).then(setData); }, []);
  if (!data) return <div className="tile loading">Invariants loading…</div>;
  if (isError(data)) return <div className="tile error">Invariants ERROR: {errorMessage(data)}</div>;
  const items = data.artifacts || [];
  return (
    <div className="tile ok">
      <h4>Constitutional Invariants ({items.length})</h4>
      <ul>
        {items.map(inv => <li key={inv.id} className="small">{inv.id}: {inv.name}</li>)}
      </ul>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function ReceiptChainTile() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.alexandriaReceipts).then(setData); }, []);
  if (!data) return <div className="tile loading">Receipt Chain loading…</div>;
  if (isError(data)) return <div className="tile error">Receipts ERROR: {errorMessage(data)}</div>;
  const items = data.artifacts || [];
  return (
    <div className="tile ok">
      <h4>Receipt Chain ({items.length})</h4>
      {items.slice(0, 5).map((r, i) => (
        <p key={i} className="mono small">{(r.receipt_id || r.id || '?').slice(0, 12)}…</p>
      ))}
    </div>
  );
}

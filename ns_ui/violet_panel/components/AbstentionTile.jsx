import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function AbstentionTile() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.clearingAbstentions).then(setData); }, []);
  if (!data) return <div className="tile loading">Abstentions loading…</div>;
  if (isError(data)) return <div className="tile error">Abstentions ERROR: {errorMessage(data)}</div>;
  const items = (data.artifacts || []).filter(a => a.reason);
  return (
    <div className="tile ok">
      <h4>Abstentions (CI-5)</h4>
      {items.length === 0 && <p className="small">No abstentions recorded</p>}
      {items.slice(0, 3).map((a, i) => (
        <p key={i} className="small">{a.reason}</p>
      ))}
    </div>
  );
}

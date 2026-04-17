import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

const RING5_GATES = [
  { id: 'G1', name: 'Stripe LLC', description: 'Live Stripe secret key' },
  { id: 'G2', name: 'Price IDs', description: 'Live Stripe price IDs' },
  { id: 'G3', name: 'DNS CNAME', description: 'Production domain CNAME' },
  { id: 'G4', name: 'YK slot_2', description: 'YubiKey slot_2 ~$55' },
  { id: 'G5', name: 'Founder sig', description: 'Founder signature for G5' },
];

export default function CathedralPane() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.ring5Gates).then(setData); }, []);

  const gatesFromEndpoint = (!data || isError(data))
    ? RING5_GATES.map(g => ({ ...g, status: 'unknown' }))
    : (data.artifacts || []);

  return (
    <div className="pane">
      <h3>FUTURE — Cathedrals (Ring 5 Gates)</h3>
      {(!data || isError(data)) && (
        <div className="error-light">Gates endpoint unavailable — showing known gates</div>
      )}
      {gatesFromEndpoint.map((g, i) => (
        <div key={g.id || i} className={`gate ${g.status === 'complete' ? 'done' : 'pending'}`}>
          <span className="gate-id">{g.id}</span>
          <span className="gate-name">{g.name}</span>
          <span className="gate-status">{g.status || 'pending'}</span>
        </div>
      ))}
    </div>
  );
}
